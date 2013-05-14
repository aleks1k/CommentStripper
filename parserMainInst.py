import multiprocessing
import os
import time
import config
from parserInst import proc_main

class CommentsMain():
    queue_limit = 100
    proc_timeout = 30
    ignore_dirs = ['.git', '.idea']
    ignore_types = ['png', 'gif', 'wav', 'jpg']
    processes_count = 10

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
        if files_with_comments_count > config.COMMENTS_PARSE_MAXCOMMENTS_SIZE:
            self.logger.warn('Comments Size Limit, %d bytes', files_with_comments_count)
            print 'Size Limit!'
            return True
        else:
            return False

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
                    if ext in self.ignore_types:
                        continue
                    self.files_count += 1
                    if not stop_walk:
                        self.add_file(os.path.join(current, file))
                        if self.files_count % 100 == 0:
                            print '.',
                            if self.check_files_limit():
                                stop_walk = True
                                # break
            # if stop_walk:
            #     break
        self.logger.info('Files count %d', self.files_count)

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
                self.logger.warn('Kill parser process %d by timeout %d', p.id, spend_time)
                p.terminate()
                p.join()
                self.procs.remove(p)
                self.start_process(p.id)
                break

    def kill_procs(self):
        for p in self.procs:
            p.terminate()
            p.join()
