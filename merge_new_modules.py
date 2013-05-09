import sys
import config

__author__ = 'Alexey'
from updater_base import ModulesUpdaterBase

class ModulesNewMerge(ModulesUpdaterBase):
    name = 'ModulesNewMerge'

    def init(self, new_ind):
        self.new_modules = self.db['modules2']
        self.output_col = self.db['modules3']
        pass

    def update_module(self, num, module_info):
        print '\tmerge module'
        newMod_info = self.new_modules.find_one({'owner': module_info['owner'], 'module_name': module_info['module_name']})
        if newMod_info:
            for field in ['watchers', 'pushed_at', 'description', 'forks', 'language']:
                module_info[field] = newMod_info[field]
            for field in ['followers', 'pushed', 'created']:
                if field in module_info:
                    module_info.pop(field)
            self.output_col.save(module_info)
            self.new_modules.remove(newMod_info)
            #delete module from new_modules collection
        else:
            pass #delete this module

    def final(self):
        modules = self.db[config.DB_MODULES_COLLECTION]
        for mod in self.new_modules:
            mod.pop('_id')
            self.output_col.insert(mod)
        self.err_modules.close()

if __name__ == "__main__":
    new_ind = 'new' in sys.argv
    new_ind = True
    LIMIT = None
    u = ModulesNewMerge()
    u.main(new_ind, LIMIT)
    u.final()
