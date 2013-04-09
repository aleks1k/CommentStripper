from pprint import pprint
import sys
import os
import itertools
import pymongo
import comment_def
import config
from elastic_search import ESIndex

class cli():
    def __init__(self):
        self.c = comment_def.CommentDictionary()
        self.files_filter = []
        for exp in self.c.reference.keys():
            self.files_filter.append(exp)

        print self.files_filter

        self.ignore_dirs = ['.git', '.idea']

        self.ext_stat = dict()

    def parseCommandLineArguments(self, tagDictionary={"-r": "recursive"}, allArguments=sys.argv):
        '''For now just allow the recursive tag, and assume every passed
        directory should have the tag. Recursive should be -r.
        Tags should be passed in the form of a dictionary mapping tag
        with meaning. Output of this method should be a dictionary mapping all
        filepaths to the results from the tagDictionary. All tags should start
        with a '-' character, and nothing else should'''
        directoryDictionary = {}
        for i in range(1, len(allArguments)):
            if allArguments[i][0] != '-':
                mapping = ""
                for key in tagDictionary:
                    try:
                        if allArguments[i + 1] == key:
                            mapping = tagDictionary[key]
                    except IndexError:
                        #Should only get an index error while checking the
                        #last element of the provided arguments
                        print "Near The End"
                        continue
                directoryDictionary[allArguments[i]] = mapping
        return directoryDictionary



    def add_ext(self, ext):
        if ext in self.ext_stat.keys():
            self.ext_stat[ext] += 1
        else:
            self.ext_stat[ext] = 1

    def filter_dir(self, dir):
        dirname = os.path.split(dir)[-1]
        return dirname not in self.ignore_dirs

    def getFiles(self, directoryDictionary):
        '''Takes the dictionary of filepaths and tags and returns a list of
        all files in the associated directories'''
        # path = os.path.abspath(__file__).rstrip('cli.py')
        allFiles = dict()

        for exp in self.files_filter:
            allFiles[exp] = []

        for path in directoryDictionary:
            # localPath = path + key
            if directoryDictionary[path] == 'recursive':
                for (current, dirs, files) in os.walk(path):
                    dirs[:] = filter(self.filter_dir, dirs)
                    if files != []:
                        for file in files:
                            ext = os.path.splitext(file)[1][1:].lower()
                            self.add_ext(ext)
                            # if ext in files_filter:
                            if ext not in allFiles:
                                allFiles[ext] = []
                            allFiles[ext].append(os.path.join(current, file))
            # else:
            #     for (current, dirs, files) in os.walk(path):
            #         if files != []:
            #             allFiles.extend(files)
            #         break

        return allFiles

    def mapFilesToTypes(self, allFiles):
        filesToTypes = {}
        for path in allFiles:
            filesToTypes[path] = self.getFileEnding(path).strip().lower()
        return filesToTypes


    def getFileEnding(self, fileName, delimiter="."):
        return fileName.rpartition(delimiter)

    def parse_repo(self, path, callback = None):
        os.chdir(path)
        allFiles = self.getFiles(self.parseCommandLineArguments(allArguments=["cli.py", '.', "-r"]))
        results = []
        i = 0
        for file_type in allFiles:
            for file_name in allFiles[file_type]:
                comments = self.c.parseAllComments(file_name, file_type)
                if len(comments) != 0:
                    results.append(dict(file_name=file_name, file_type=file_type, comments=comments))
                    i += 1
                    if callback and i % 20 == 0:
                        callback(results)
                        print '.',
                        results = []
        if callback:
            callback(results)
            return i
        else:
            return results

def main():
    mongoConn = pymongo.MongoClient(config.DB_HOST, 27017)
    db = mongoConn[config.DB_NAME]
    modules_collection = db['modules']
    modules = modules_collection.find()

    es = ESIndex()

    cl = cli()

    count = modules.count()
    i = 0
    for module in modules:
        id = dict(user=module['owner'], repo=module['module_name'])
        i += 1
        repo_name = '%(user)s/%(repo)s' % id
        print '(%d/%d)' % (i, count), repo_name
        path = os.path.join(config.GITHUB_REPOS_CLONE_PATH, repo_name)
        if os.path.exists(path):
            add_callback = lambda files: es.add_to_index(files, module, bulk=True)
            results = cl.parse_repo(path, add_callback)
            print '\n', results
            # es.add_to_index(results, module)
            sys.stdout.write("Done!\n")
            sys.stdout.flush()
        else:
            print 'Repo not found'

    ext_list = []
    for (ext, count) in cl.ext_stat.items():
        ext_list.append((ext, count))

    pprint(sorted(ext_list, key=lambda x: x[1], reverse=True))

    # pprint(ext_stat)

    # es.print_all()

if __name__ == "__main__":
    main()
