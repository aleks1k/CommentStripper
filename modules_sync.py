import os
from pprint import pprint
import sys
import time
import traceback
from bson import ObjectId
import git
import config

__author__ = 'Alexey'
from updater_base import ModulesUpdaterBase
from parserMainInst import CommentsMain
from elastic_search import ESIndex

import git_tools

class ModulesGitUpdater(ModulesUpdaterBase):
    name = 'ModulesGitUpdater'

    def init(self, new_ind):
        if new_ind:
            pass
            # self.db.drop_collection('module_updates')
        self.err_modules = open(os.path.join(config.LOG_PATH, 'not_cloned_modules.%d.txt' % self.start_time), 'w')

    def update_from_git(self, module_info):
        path = self.get_repo_path(module_info)
        mod_path_id = dict(user=module_info['owner'], repo=module_info['module_name'])
        try:
            if git_tools.check_git_repo_exist(path):
                def save_update_to_db(old_commit, new_commit):
                    module_id = module_info['_id']
                    updates = self.db['module_updates']
                    item = updates.find_one(module_id) # id update item equal module id
                    if not item:
                        item = dict(_id=module_id, old_commit=old_commit, new_commit=new_commit)
                    else:
                        item['new_commit'] = new_commit

                    updates.save(item)

                git_tools.git_pull(path, save_update_to_db)
            else:
                git_tools.git_clone(mod_path_id)
            sys.stdout.write("Done!\n")
            sys.stdout.flush()
        except git.exc.GitCommandError as ex:
            if ex.status == 128:
                sys.stdout.write("Repository not found.\n")
                sys.stdout.flush()
                git_tools.drop_dir(path)
            self.err_modules.write('%(user)s/%(repo)s\n' % mod_path_id)
            self.err_modules.write(traceback.format_exc())
            self.err_modules.flush()
        except Exception as ex:
            try:
                print 'try make clone repo again...\n'
                git_tools.drop_dir(path)
                git_tools.git_clone(mod_path_id)
                sys.stdout.write("Done!\n")
                sys.stdout.flush()
            except Exception as ex:
                self.err_modules.write('%(user)s/%(repo)s\n' % mod_path_id)
                self.err_modules.write(traceback.format_exc())
                self.err_modules.flush()


    def update_module(self, num, module_info):
        print '\tupdate from git'
        self.update_from_git(module_info)

    def final(self):
        self.err_modules.close()

class ModulesSync(ModulesUpdaterBase):
    name = 'ModulesSync'

    def init(self, new_ind):
        self.p = CommentsMain()
        if self.p:
            self.p.db = self.db
            self.p.logger = self.logger
        self.es = ESIndex()
        self.err_modules = open(os.path.join(config.LOG_PATH, 'not_cloned_modules.%d.txt' % self.start_time), 'w')

        if new_ind: self.clear_index()

    def clear_index(self):
        print 'Create Index'
        # self.es.create_index()
        self.db.drop_collection('module_updates')

    def update_module(self, num, module_info):
        # print '\tupdate from git',
        # self.update_from_git(module_info)

        print '\tparsing',
        repo_dir_exist, path = self.check_repo_dir_exist(module_info)
        if repo_dir_exist:
            module_id = str(module_info['_id'])
            if self.p:
                self.p.curr_module_id = module_id
            self.db.drop_collection(config.DB_COMMENTS_COLLECTION)
            self.db.create_collection(config.DB_COMMENTS_COLLECTION)

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
            if self.p:
                self.p.getFiles(path)

            if self.p:
                while self.p.files_query.qsize() > 0:
                    time.sleep(3)
                    self.p.check_process_timeout()
            res = self.es.add_module_from_mongo(module_info, self.db[config.DB_COMMENTS_COLLECTION], diff_res)
            if res:
                if diff_res:
                    updates = self.db['module_updates']
                    updates.remove(ObjectId(module_id))
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

    def update(self, module_id, repo_path):
        updates = self.db['module_updates']
        up_info = updates.find_one(ObjectId(module_id))
        if up_info:
            if git_tools.check_git_repo_exist(repo_path):
                res = git_tools.git_diff(repo_path, up_info['old_commit'], up_info['new_commit'])
                print 'A: %d, M: %d, D: %d' % (len(res['A']),len(res['M']),len(res['D']))
                return res
        return None

    def final(self):
        self.err_modules.close()
        if self.p:
            self.p.kill_procs()

if __name__ == "__main__":
    new_ind = 'new' in sys.argv
    # new_ind = True
    LIMIT = None
    if 'git' in sys.argv:
        u = ModulesGitUpdater()
    else:
        u = ModulesSync()
    u.main(new_ind, LIMIT)
    u.final()
