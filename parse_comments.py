import logging
import os
from pprint import pprint
import sys
import time
import comment_def
import traceback

__author__ = 'Alexey'

class CallBackException(Exception):
    pass

class ParseComments():
    ignore_dirs = ['.git', '.idea']
    ignore_types = ['png', 'gif', 'wav', 'jpg']
    collect_statistic = False # Set True for collect statistic for file types and parse time

    files_limit = 0
    return_comments_callback = None

    def __init__(self):
        self.comments_parser = comment_def.CommentDictionary(collect_statistics=self.collect_statistic)
        self.comments_store = dict()
        self.comments_store_size = 0
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

    def get_comments_size(self, comments):
        comments_size = 0
        for c in comments['comments']:
            comments_size += len(c)
        return comments_size

    def add_comments(self, comments):
        self.comments_store.append(comments)
        self.comments_store_size += self.get_comments_size(comments)
        res = True
        if (self.files_limit and len(self.comments_store) >= self.files_limit) or (self.size_limit and self.comments_store_size > self.size_limit):
            if self.return_comments_callback:
                try:
                    res = self.return_comments_callback(self.comments_store, self.comments_store_size)
                except:
                    raise CallBackException()
            self.comments_store = []
            self.comments_store_size = 0
        return res

    def add_file(self, file_path, ext):
        comments = self.comments_parser.parseAllComments(file_path, ext)
        if len(comments) != 0:
            file_path = os.path.normcase(file_path)
            res = file_path.split(os.path.sep)
            file_name = os.path.sep.join(res[self.root_len:])
            result = dict(file_name=file_name, file_type=ext, comments=comments)
            return self.add_comments(result)
        return True

    def getFiles(self, dir_path):
        '''Takes the dictionary of filepaths and tags and returns a list of
        all files in the associated directories'''
        self.files_count = 0
        for (current, dirs, files) in os.walk(str(dir_path)):
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
                    if not self.add_file(os.path.join(current, file_path), ext):
                        return
                except (KeyboardInterrupt, CallBackException):
                    raise
                except:
                    traceback.print_exc()
                    logging.error(traceback.format_exc())
                    print 'Fail %s' % file_path
                if self.files_count % 100 == 0:
                    print '.',
        logging.info('Files count %d', self.files_count)

    def parse_dir(self, directory):
        self.files_limit = 0
        self.size_limit = 0
        self.return_comments_callback = None
        print '\tparsing',
        if os.path.exists(directory):
            self.root_len = len(os.path.normcase(directory).split(os.path.sep))
            self.comments_store = [] #clear store
            self.comments_store_size = 0
            self.getFiles(directory)
            return self.comments_store
        else:
            print 'Repo not found'
        return []

    def parse_dir_partly(self, directory, callback, files_limit = 0, size_limit = 0):
        self.files_limit = files_limit
        self.size_limit = size_limit
        self.return_comments_callback = callback
        print '\tparsing',
        if os.path.exists(directory):
            self.root_len = len(os.path.normcase(directory).split(os.path.sep))
            self.comments_store = [] #clear store
            self.comments_store_size = 0
            self.getFiles(directory)
            self.return_comments_callback(self.comments_store, self.comments_store_size)
            return True
        else:
            print 'Repo not found'
        return False


    def print_statistics(self):
        pprint(self.comments_parser.pattern_stat)
        ext_list = []
        for (ext, ecount) in self.ext_stat.items():
            ext_list.append((ext, ecount))
        pprint(sorted(ext_list, key=lambda x: x[1], reverse=True))

if __name__ == "__main__":
    parser = ParseComments()
    # logging.basicConfig(filename=os.path.join('/repo/logs', '%s.%d.log' % ('ParseComments', int(time.time()))), filemode='w', level=logging.INFO)
    dirs = ['/repo/github/diaspora/diaspora', '/repo/github/django/django']
    for d in dirs:
        comments = parser.parse_dir(d)
        pprint(comments)

    print 'Statictics\n'
    parser.print_statistics()
