import logging
import multiprocessing
from multiprocessing import Queue
from Queue import Empty as QueueEmptyException
import os
from bson import ObjectId
import pymongo
import time
import comment_def
import config
from elastic_search import ESIndex

__author__ = 'Alexey'

class Parser():
    def __init__(self, process_id):
        self.process_id = process_id
        logging.disable(logging.CRITICAL)
        self.logger = logging.getLogger('parser.%d' % process_id)
        mongoConn = pymongo.MongoClient(config.DB_HOST, 27017)
        self.logger.info('Connect to mongo db: %s', config.DB_HOST)
        db = mongoConn[config.DB_NAME]
        self.modules = db[config.DB_MODULES_COLLECTION]
        self.comments = db[config.DB_COMMENTS_COLLECTION]
        self.es = ESIndex()
        self.c = comment_def.CommentDictionary()
        self.root_len = len(os.path.normcase(config.GITHUB_REPOS_CLONE_PATH[0]).split(os.path.sep)) #FIXME repo root dirs may have different len

    curr_owner = ''
    curr_repo = ''

    mid = ''

    def get_module_by_id(self, mid):
        if mid == self.mid:
            return self.curr_module_
        module = self.modules.find_one(ObjectId(mid))
        if module:
            self.mid = mid
            self.curr_module_ = module
            return module

    def main(self, files_query, last_time):
        # last_time_f = float(last_time.value)
        self.logger.info('Parser started')
        # time_interval_indexing = 0
        # results = []
        # last_comment_count = 0
        while True:
            curr_time = time.time()
            # time_interval = (curr_time - last_time_f)
            last_time_f = curr_time
            with last_time.get_lock():
                last_time.value = int(last_time_f)
            try:
                f, mid = files_query.get(True, 10)

                file_path = os.path.normcase(f)
                # self.logger.info('Get file: last time: %f, %d, %f, %s, ', time_interval, last_comment_count, time_interval_indexing, file_path )
                ext = os.path.splitext(file_path)[1][1:].lower()
                # results = []
                comments = self.c.parseAllComments(file_path, ext)
                # time.sleep(5)
                last_comment_count = len(comments)
                if last_comment_count != 0:
                    module = self.get_module_by_id(mid)
                    if module:
                        res = file_path.split(os.path.sep)
                        file_name = os.path.sep.join(res[self.root_len + 2:])
                        # file_name = self.file_name
                        result = dict(file_name=file_name, file_type=ext, comments=comments)
                        # last_time_indexing = time.time()
                        # if len(results) > 10:
                        #     self.es.add_to_index(results, module, bulk=True)
                        #     results = []
                        # with es_lock:
                        self.es.add_comments_form_file_to_mongo(self.comments, mid, result)
                        # time_interval_indexing = (time.time() - last_time_indexing)
                    else:
                        self.logger.error('Module not found, id: %s', mid)
            except QueueEmptyException:
                pass

def proc_main(q, v=multiprocessing.Value('i', int(time.time())), process_id=0):
    # logging.basicConfig(filename=os.path.join(config.LOG_PATH, 'parser.%d.%d.log' % (id, v.value)), level=logging.INFO)
    p = Parser(process_id)
    p.main(q, v)

if __name__ == "__main__":
    q = multiprocessing.Queue()
    bigcss = 'D:\\repo\\github\\adobe\\brackets\\test\\spec\\ExtensionUtils-test-files\\sub dir\\second.css'
    smallcss = 'D:\\repo\\github\\adobe\\brackets\\test\\spec\\ExtensionUtils-test-files\\sub dir\\fourth.css'
    # q.put(bigcss)
    # q.put(smallcss)
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    q.put((r'\repo\github\blueimp\jquery-file-upload\contributing.md', '5133bbdf290a9d6c0d000011'))
    proc_main(q)
