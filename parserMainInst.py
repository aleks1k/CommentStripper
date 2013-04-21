import logging
import multiprocessing
import pickle
from pprint import pprint
import sys
import os
import traceback
import pymongo
import time
import config
from elastic_search import ESIndex
from parserInst import proc_main

logger = logging.getLogger('main')

class CommentsMain():
    queue_limit = 100
    proc_timeout = 120
    ignore_dirs = ['.git', '.idea']
    processes_count = 5

    def __init__(self):
        self.ext_stat = dict()
        self.procs = []
        self.files_count = 0
        self.files_query = multiprocessing.Queue()
        self.es_lock = None#multiprocessing.Lock()
        for i in range(0, self.processes_count):
            self.start_process(i)

    def add_ext(self, ext):
        if ext in self.ext_stat.keys():
            self.ext_stat[ext] += 1
        else:
            self.ext_stat[ext] = 1

    def filter_dir(self, dir):
        dirname = os.path.split(dir)[-1]
        return dirname not in self.ignore_dirs

    def add_file(self, f):
        self.check_procs()
        while self.files_query.qsize() > self.queue_limit:
            time.sleep(1)
            self.check_procs()
        self.files_query.put((f, self.curr_module_id))

    def check_files_limit(self):
        stats = self.db.command('collStats', config.DB_COMMENTS_COLLECTION)
        files_with_comments_count = stats['size']
        return files_with_comments_count > config.COMMENTS_PARSE_MAXCOMMENTS_SIZE

    def getFiles(self, dir_path):
        '''Takes the dictionary of filepaths and tags and returns a list of
        all files in the associated directories'''
        self.files_count = 0
        stop_walk = False
        for (current, dirs, files) in os.walk(dir_path):
            dirs[:] = filter(self.filter_dir, dirs)
            if files != []:
                for file in files:
                    ext = os.path.splitext(file)[1][1:].lower()
                    self.add_ext(ext)
                    self.add_file(os.path.join(current, file))
                    self.files_count += 1
                    if self.files_count % 100 == 0:
                        print '.',
                        if self.check_files_limit():
                            stop_walk = True
                            break
            if stop_walk:
                break

    def start_process(self, id):
        start_time = multiprocessing.Value('i', int(time.time()))
        proc = multiprocessing.Process(target=proc_main, args=(self.files_query, start_time, id, self.es_lock))
        proc.start_time = start_time
        proc.id = id
        self.procs.append(proc)
        proc.start()


    def check_procs(self):
        for p in self.procs:
            curr_time = int(time.time())
            # with p.start_time.get_lock():
            spend_time = curr_time - p.start_time.value
            if spend_time > self.proc_timeout:
                logger.warn('Kill parser process %d by timeout %d', p.id, spend_time)
                p.terminate()
                p.join()
                self.procs.remove(p)
                self.start_process(p.id)
                break

    def kill_procs(self):
        for p in self.procs:
            p.terminate()
            p.join()

def main(new_ind=True):
    start_time = int(time.time())
    logging.basicConfig(filename=os.path.join(config.LOG_PATH, 'main.%d.log' % start_time), filemode='w', level=logging.INFO)
    mongoConn = pymongo.MongoClient(config.DB_HOST, 27017)
    db = mongoConn[config.DB_NAME]
    modules_collection = db['modules']
    startModuleIndex = 0
    pcl_file_name = 'last_success.pcl'
    if not new_ind and os.path.exists(pcl_file_name):
        with open(pcl_file_name, 'rb') as pcl_file:
            startModuleIndex = pickle.load(pcl_file)
    modules = modules_collection.find(timeout=False).sort('_id').skip(startModuleIndex)

    p = CommentsMain()
    p.db = db
    es = ESIndex()
    if not new_ind:
        es.create_index()
    mcount = modules.count()
    module_num = startModuleIndex
    for module in modules:
        mid = dict(user=module['owner'], repo=module['module_name'])
        module_num += 1
        repo_name = '%(user)s/%(repo)s' % mid
        logger.info('Module %s', repo_name)
        print '(%d/%d)' % (module_num, mcount), repo_name
        print '\tparsing',
        path = os.path.join(config.GITHUB_REPOS_CLONE_PATH, repo_name)
        if os.path.exists(path):
            module_id = str(module['_id'])
            p.curr_module_id = module_id
            db.drop_collection(config.DB_COMMENTS_COLLECTION)
            db.create_collection(config.DB_COMMENTS_COLLECTION)

            p.getFiles(path)
            while p.files_query.qsize() > 0:
                time.sleep(3)
                p.check_procs()
            es.add_module_from_mongo(module, db[config.DB_COMMENTS_COLLECTION])
            print '\n\tDone!'
            if module_num % 100 == 0:
                with open(os.path.join(config.LOG_PATH, 'ext_stat.%d.log' % start_time), 'w') as stat_log:
                    ext_list = []
                    for (ext, ecount) in p.ext_stat.items():
                        ext_list.append((ext, ecount))

                    pprint(sorted(ext_list, key=lambda x: x[1], reverse=True), stat_log)
        else:
            print 'Repo not found'
        with open(pcl_file_name, 'wb') as pcl_file:
            pickle.dump(module_num, pcl_file)
    while not p.files_query.empty():
        p.check_procs()
        time.sleep(1)
    p.kill_procs()
    print 'END!!!'

if __name__ == "__main__":
    new_ind = 'new' in sys.argv
    while True:
        try:
            main(new_ind)
        except:
            traceback.print_exc()
            logger.error(traceback.format_exc())
            new_ind = False
