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

class ParseComments():
    ignore_dirs = ['.git', '.idea']
    ignore_types = ['png', 'gif', 'wav', 'jpg']
    collect_statistic = True

    def __init__(self):
        self.comments_parser = comment_def.CommentDictionary(collect_statistics=self.collect_statistic)
        self.comments_store = dict()
        self.files_count = 0
        self.ext_stat = dict()

    if collect_statistic:
        def add_ext(self, ext):
            if ext in self.ext_stat.keys():
                self.ext_stat[ext] += 1
            else:
                self.ext_stat[ext] = 1

    def filter_dir(self, d):
        dirname = os.path.split(d)[-1]
        return dirname not in self.ignore_dirs

    def add_comments(self, comments):
        self.comments_store.append(comments)

    def add_file(self, file_path, ext):
        comments = self.comments_parser.parseAllComments(file_path, ext)
        if len(comments) != 0:
            file_path = os.path.normcase(file_path)
            res = file_path.split(os.path.sep)
            file_name = os.path.sep.join(res[self.root_len:])
            result = dict(file_name=file_name, file_type=ext, comments=comments)
            self.add_comments(result)

    def getFiles(self, dir_path):
        '''Takes the dictionary of filepaths and tags and returns a list of
        all files in the associated directories'''
        self.files_count = 0
        for (current, dirs, files) in os.walk(dir_path):
            dirs[:] = filter(self.filter_dir, dirs)
            if not len(files):
                continue
            for file_path in files:
                ext = os.path.splitext(file_path)[1][1:].lower()
                if self.collect_statistic: self.add_ext(ext)
                if ext in self.ignore_types:
                    continue
                self.files_count += 1
                try:
                    self.add_file(os.path.join(current, file_path), ext)
                except:
                    traceback.print_exc()
                    logging.error(traceback.format_exc())
                    print 'Fail %s' % file_path
                if self.files_count % 100 == 0:
                    print '.',
        logging.info('Files count %d', self.files_count)

    def parse_dir(self, directory):
        print '\tparsing',
        if os.path.exists(directory):
            self.root_len = len(os.path.normcase(directory).split(os.path.sep))
            self.comments_store = [] #clear store
            self.getFiles(directory)
            return self.comments_store
        else:
            print 'Repo not found'
        return []

    def print_statistics(self):
        pprint(self.comments_parser.pattern_stat)
        ext_list = []
        for (ext, ecount) in self.ext_stat.items():
            ext_list.append((ext, ecount))
        pprint(sorted(ext_list, key=lambda x: x[1], reverse=True))

class ParseModuleComments(ModulesUpdaterBase):
    name = 'ParseComments'

    def init(self, new_ind):
        # self.root_len = len(os.path.normcase(config.GITHUB_REPOS_CLONE_PATH[0]).split(os.path.sep)) #FIXME repo root dirs may have different len
        self.parser = ParseComments()
        self.es = ESIndex()
        if new_ind: self.clear_index()

    def clear_index(self):
        print 'Create Index'
        # self.es.create_index()

    def update_module(self, num, module_info):
        # print '\tparsing',
        repo_dir_exist, path = self.check_repo_dir_exist(module_info)
        if repo_dir_exist:
            comments = self.parser.parse_dir(path)
            res = self.es.add_module_from_dict(module_info, comments)
            print '\n\tDone!'
        else:
            print 'Repo not found'

    def final(self):
        self.parser.print_statistics()

if __name__ == "__main__":
    new_ind = 'new' in sys.argv
    new_ind = True
    LIMIT = 5
    u = ParseModuleComments()
    logging.basicConfig(filename=os.path.join(config.LOG_PATH, '%s.%d.log' % (u.name, int(time.time()))), filemode='w', level=logging.INFO)
    u.main(new_ind, LIMIT)
    u.final()
