import sys
from elastic_search import ESIndex
from updater_base import ModulesUpdaterBase

__author__ = 'Alexey'

class ModulesIndexer(ModulesUpdaterBase):
    name = 'ModulesIndexer'

    def init(self, new_ind):
        self.es = ESIndex()
        self.clear_index()

    def clear_index(self):
        print 'Create Index'
        self.es.create_index()

    def update_module(self, num, module_info):
        module_id = str(module_info['_id'])
        doc = self.es.is_module_in_index(module_id)
        if not doc:
            res = self.es.add_module(module_info)
            if not res:
                print 'Error!'

if __name__ == "__main__":
    new_ind = 'new' in sys.argv
    new_ind = True
    LIMIT = None
    u = ModulesIndexer()
    u.main(new_ind, LIMIT)
