import logging
import os
from pprint import pprint
import sys
import time
import comment_def
import config
import traceback
from updater_base import ModulesUpdaterBase
from elastic_search import ESIndex

__author__ = 'Alexey'

class ParseComments(ModulesUpdaterBase):
    name = 'ParseComments'

    ignore_dirs = ['.git', '.idea']
    ignore_types = ['png', 'gif', 'wav', 'jpg']

    def init(self, new_ind):
        self.ext_stat = dict()
        self.files_count = 0
        self.comments_store = dict()
        self.comments_parser = comment_def.CommentDictionary(collect_statistics=False)
        self.root_len = len(os.path.normcase(config.GITHUB_REPOS_CLONE_PATH[0]).split(os.path.sep)) #FIXME repo root dirs may have different len

        self.es = ESIndex()
        if new_ind: self.clear_index()

    def add_ext(self, ext):
        return
        if ext in self.ext_stat.keys():
            self.ext_stat[ext] += 1
        else:
            self.ext_stat[ext] = 1

    def filter_dir(self, d):
        dirname = os.path.split(d)[-1]
        return dirname not in self.ignore_dirs

    def add_comments(self, mid, comments):
        self.comments_store.append(comments)
        # if mid in self.comments_store:
        #     self.comments_store[mid].append(comments)
        # else:
        #     self.comments_store[mid] = [comments]

    def add_file(self, f, ext):
        file_path = os.path.normcase(f)
        comments = self.comments_parser.parseAllComments(file_path, ext)
        last_comment_count = len(comments)
        if last_comment_count != 0:
            assert(self.curr_module)
            mid = self.curr_module['_id']
            res = file_path.split(os.path.sep)
            file_name = os.path.sep.join(res[self.root_len + 2:])
            # file_name = self.file_name
            result = dict(file_name=file_name, file_type=ext, comments=comments)
            # last_time_indexing = time.time()
            # if len(results) > 10:
            #     self.es.add_to_index(results, module, bulk=True)
            #     results = []
            # with es_lock:
            self.add_comments(mid, result)
            # time_interval_indexing = (time.time() - last_time_indexing)

    def check_files_limit(self):
        return False
        # stats = self.db.command('collStats', config.DB_COMMENTS_COLLECTION)
        # files_with_comments_count = stats['size']
        # if files_with_comments_count > config.COMMENTS_PARSE_MAXCOMMENTS_SIZE:
        #     self.logger.warn('Comments Size Limit, %d bytes', files_with_comments_count)
        #     print 'Size Limit!'
        #     return True
        # else:
        #     return False

    def getFiles(self, dir_path):
        '''Takes the dictionary of filepaths and tags and returns a list of
        all files in the associated directories'''
        self.files_count = 0
        stop_walk = False
        for (current, dirs, files) in os.walk(dir_path):
            dirs[:] = filter(self.filter_dir, dirs)
            if files != []:
                for file_path in files:
                    ext = os.path.splitext(file_path)[1][1:].lower()
                    self.add_ext(ext)
                    if ext in self.ignore_types:
                        continue
                    self.files_count += 1
                    if not stop_walk:
                        try:
                            self.add_file(os.path.join(current, file_path), ext)
                        except:
                            traceback.print_exc()
                            self.logger.error(traceback.format_exc())
                            print 'Fail %s' % file_path
                        if self.files_count % 100 == 0:
                            print '.',
                            #if self.check_files_limit():
                            #    stop_walk = True
        self.logger.info('Files count %d', self.files_count)

    def clear_index(self):
        print 'Create Index'
        # self.es.create_index()

    def update_module(self, num, module_info):
        print '\tparsing',
        repo_dir_exist, path = self.check_repo_dir_exist(module_info)
        if repo_dir_exist:
            mid = str(module_info['_id'])
            self.curr_module = module_info
            # doc = self.es.is_module_in_index(module_id)
            diff_res = None
            # if doc:
            #     diff_res = self.update(module_id, path)
            #     if diff_res:
            #         for files in diff_res['A'], diff_res['M']:
            #             for filename in files:
            #                 if self.p:
            #                     self.p.add_file(os.path.join(path, filename))
            # else:
            self.comments_store = [] #clear store
            self.getFiles(path)

            res = self.es.add_module_from_dict(module_info, self.comments_store, diff_res)
            # if res:
            #     if diff_res:
            #         updates = self.db['module_updates']
            #         updates.remove(ObjectId(module_id))
            print '\n\tDone!'
            # if num % 100 == 0:
            #     with open(os.path.join(config.LOG_PATH, 'ext_stat.%d.log' % self.start_time), 'w') as stat_log:
            #         ext_list = []
            #         for (ext, ecount) in self.p.ext_stat.items():
            #             ext_list.append((ext, ecount))
            #
            #         pprint(sorted(ext_list, key=lambda x: x[1], reverse=True), stat_log)
        else:
            print 'Repo not found'

    # def update(self, module_id, repo_path):
    #     updates = self.db['module_updates']
    #     up_info = updates.find_one(ObjectId(module_id))
    #     if up_info:
    #         if git_tools.check_git_repo_exist(repo_path):
    #             res = git_tools.git_diff(repo_path, up_info['old_commit'], up_info['new_commit'])
    #             print 'A: %d, M: %d, D: %d' % (len(res['A']),len(res['M']),len(res['D']))
    #             return res
    #     return None

    def final(self):
        pprint(self.comments_parser.pattern_stat)
        pass
        # self.err_modules.close()
        # if self.p:
        #     self.p.kill_procs()

if __name__ == "__main__":
    new_ind = 'new' in sys.argv
    # new_ind = True
    LIMIT = None
    u = ParseComments()
    logging.basicConfig(filename=os.path.join(config.LOG_PATH, '%s.%d.log' % (u.name, int(time.time()))), filemode='w', level=logging.INFO)
    u.main(new_ind, LIMIT)
    u.final()
