import multiprocessing
import os
import time
import config
from parserInst import proc_main

class WorkProcess(multiprocessing.Process):
    def __init__(self, process_id, files_query):
        self.start_time = multiprocessing.Value('i', int(time.time()))
        self.process_id = process_id
        super(WorkProcess, self).__init__(target=proc_main, args=(files_query, self.start_time, self.process_id))

    def get_time(self):
        return self.start_time.value

    def kill(self):
        self.terminate()
        self.join()

class CommentsMain():
    queue_limit = 100
    proc_timeout = 30
    ignore_dirs = ['.git', '.idea']
    ignore_types = ['png', 'gif', 'wav', 'jpg']
    processes_count = 10

    def __init__(self):
        self.ext_stat = None#dict()
        self.procs = []
        self.files_count = 0
        self.files_query = multiprocessing.Queue()
        for i in range(0, self.processes_count):
            self.start_process(i)

    def add_ext(self, ext):
        pass
        # if ext in self.ext_stat.keys():
        #     self.ext_stat[ext] += 1
        # else:
        #     self.ext_stat[ext] = 1

    def filter_dir(self, dir):
        dirname = os.path.split(dir)[-1]
        return dirname not in self.ignore_dirs

    def add_file(self, f):
        self.check_process_timeout()
        while self.files_query.qsize() > self.queue_limit:
            time.sleep(1)
            self.check_process_timeout()
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

    def start_process(self, process_id):
        p = WorkProcess(process_id, self.files_query)
        self.procs.append(p)
        p.start()

    def check_process_timeout(self):
        curr_time = int(time.time())
        for p in self.procs:
            spend_time = curr_time - p.get_time()
            if spend_time > self.proc_timeout:
                self.logger.warn('Kill parser process %d by timeout %d', p.process_id, spend_time)
                p.kill()
                self.procs.remove(p)
                self.start_process(p.process_id)
                break

    def kill_procs(self):
        for p in self.procs:
            p.kill()
