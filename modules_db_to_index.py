import sys
import config
from elastic_search import ESIndex
from updater_base import ModulesUpdaterBase

__author__ = 'Alexey'

class ModulesIndexer(ModulesUpdaterBase):
    name = 'ModulesIndexer'

    def init(self, new_ind):
        self.es = ESIndex()
        self.clear_index()
        self.mod_set = set()

    def clear_index(self):
        print 'Create Index'
        self.es.create_index()

    def update_module(self, num, module_info):
        repo_name = '%(user)s/%(repo)s' % dict(user=module_info['owner'], repo=module_info['module_name'])
        if repo_name not in self.mod_set:
            self.mod_set.add(repo_name)
            doc = self.es.is_module_in_index(str(module_info['_id']))
            if not doc:
                res = self.es.add_module(module_info)
                if not res:
                    print 'Error!'
        else:
            print 'Dublicate'
            self.modules_collection.remove(module_info['_id'])

if __name__ == "__main__":
    new_ind = 'new' in sys.argv
    #new_ind = True
    LIMIT = None
    u = ModulesIndexer()
    u.main(new_ind, LIMIT)
