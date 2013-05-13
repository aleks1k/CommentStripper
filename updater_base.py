import logging
import os
import pickle
from random import Random
import traceback
import time
import pymongo
import sys
import config

__author__ = 'Alexey'

rand = Random()

class ModulesUpdaterBase():
    name = 'base'
    logger = logging.getLogger(name)

    def init(self, new_ind):
        pass

    def update_module(self, num, module_info):
        print 'start',
        if 1 == rand.randint(1, 10):
            raise Exception()
        print 'end'

    def get_repo_path(self, module_info):
        path = os.path.join(os.path.join(config.GITHUB_REPOS_CLONE_PATH, module_info['owner']), module_info['module_name'])
        return path

    def check_repo_dir_exist(self, module_info):
        for base_dir in config.GITHUB_REPOS_CLONE_PATH:
            path = os.path.join(os.path.join(base_dir, module_info['owner']), module_info['module_name'])
            if os.path.exists(path):
                return True, path
        return False, path # return path in last dir from config

    def run(self, new_ind, limit=None):
        self.start_time = int(time.time())
        logging.basicConfig(filename=os.path.join(config.LOG_PATH, '%s.%d.log' % (self.name, self.start_time)), filemode='w', level=logging.INFO)
        mongoConn = pymongo.MongoClient(config.DB_HOST, 27017)
        self.db = mongoConn[config.DB_NAME]
        self.modules_collection = self.db[config.DB_MODULES_COLLECTION]
        startModuleIndex = 0
        pcl_file_name = 'last_success_%s.pcl' % self.name
        if not new_ind and os.path.exists(pcl_file_name):
            with open(pcl_file_name, 'rb') as pcl_file:
                startModuleIndex = pickle.load(pcl_file)
        modules = self.modules_collection.find(timeout=False).sort('_id').skip(startModuleIndex)
        if limit:
            l = limit - startModuleIndex
            if l <= 0:
                print 'Completed'
                return
            modules = modules.limit(l)
            mcount = limit
        else:
            mcount = modules.count()

        self.init(new_ind)

        module_num = startModuleIndex
        for module in modules:
            mid = dict(user=module['owner'], repo=module['module_name'])
            module_num += 1
            repo_name = '%(user)s/%(repo)s' % mid
            self.logger.info('Module %s', repo_name)
            print '(%d/%d)' % (module_num, mcount), repo_name
            self.update_module(module_num, module)
            with open(pcl_file_name, 'wb') as pcl_file:
                pickle.dump(module_num, pcl_file)
        # self.final()
        print 'END, Time: %d!!!' % (int(time.time()) - self.start_time)

    def main(self, new_ind=True, limit=None):
        while True:
            try:
                self.run(new_ind, limit)
                break
            except:
                traceback.print_exc()
                self.logger.error(traceback.format_exc())
                time.sleep(1)
                new_ind = False

if __name__ == "__main__":
    new_ind = 'new' in sys.argv
    new_ind = True
    LIMIT = 100
    u = ModulesUpdaterBase()
    u.main(new_ind, LIMIT)
