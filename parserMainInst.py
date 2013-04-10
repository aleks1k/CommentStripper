import logging
import multiprocessing
from pprint import pprint
import sys
import os
import itertools
from paramiko.logging22 import logger
import pymongo
import time
import comment_def
import config
from elastic_search import ESIndex
from parserInst import proc_main

logger = logging.getLogger('main')

class CommentsMain():
    def __init__(self):
        self.ignore_dirs = ['.git', '.idea']
        self.ext_stat = dict()
        self.procs = []
        self.files_query = multiprocessing.Queue()
        for i in range(0, 10):
            self.start_process(i)

    def add_ext(self, ext):
        if ext in self.ext_stat.keys():
            self.ext_stat[ext] += 1
        else:
            self.ext_stat[ext] = 1

    def filter_dir(self, dir):
        dirname = os.path.split(dir)[-1]
        return dirname not in self.ignore_dirs

    def getFiles(self, dir_path, func):
        '''Takes the dictionary of filepaths and tags and returns a list of
        all files in the associated directories'''
        for (current, dirs, files) in os.walk(dir_path):
            dirs[:] = filter(self.filter_dir, dirs)
            if files != []:
                for file in files:
                    ext = os.path.splitext(file)[1][1:].lower()
                    self.add_ext(ext)
                    func(os.path.join(current, file))

    def start_process(self, id):
        start_time = multiprocessing.Value('i', int(time.time()))

        proc = multiprocessing.Process(target=proc_main, args=(self.files_query, start_time, id))
        proc.start_time = start_time
        proc.id = id
        self.procs.append(proc)
        proc.start()


    def check_procs(self):
        for p in self.procs:
            curr_time = int(time.time())
            # with p.start_time.get_lock():
            spend_time = curr_time - p.start_time.value
            if spend_time > 30:
                logger.warn('Kill parser process %d by timeout %d', p.id, spend_time)
                p.terminate()
                p.join()
                self.procs.remove(p)
                self.start_process(p.id)
                break
                # p.close()

    def kill_procs(self):
        for p in self.procs:
            p.terminate()
            p.join()

def main():
    logging.basicConfig(filename='main.log', filemode='w', level=logging.INFO)
    mongoConn = pymongo.MongoClient(config.DB_HOST, 27017)
    db = mongoConn[config.DB_NAME]
    modules_collection = db['modules']
    modules = modules_collection.find()

    p = CommentsMain()
    es = ESIndex()
    es.create_index()

    mcount = modules.count()
    i = 0
    for module in modules:
        id = dict(user=module['owner'], repo=module['module_name'])
        i += 1
        repo_name = '%(user)s/%(repo)s' % id
        logger.info('Module %s', repo_name)
        print '(%d/%d)' % (i, mcount), repo_name
        path = os.path.join(config.GITHUB_REPOS_CLONE_PATH, repo_name)
        p.files_count = 0
        if os.path.exists(path):
            module_id = str(module['_id'])
            def add_file(f):
                p.check_procs()
                while p.files_query.qsize() > 100:
                    time.sleep(1)
                    p.check_procs()
                p.files_query.put((f, module_id))
                p.files_count += 1
                if p.files_count % 100 == 0:
                    print '.',
            p.getFiles(path, add_file)
            sys.stdout.write("Done!\n")
            sys.stdout.flush()

            if i % 2 == 0:
                with open('ext_stat.log', 'w') as stat_log:
                    ext_list = []
                    for (ext, ecount) in p.ext_stat.items():
                        ext_list.append((ext, ecount))

                    pprint(sorted(ext_list, key=lambda x: x[1], reverse=True), stat_log)
        else:
            print 'Repo not found'
    while not p.files_query.empty():
        p.check_procs()
        time.sleep(1)
    p.kill_procs()
    print 'END!!!'

if __name__ == "__main__":
    main()
