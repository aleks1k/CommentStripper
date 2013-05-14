import os
from pyes.exceptions import NoServerAvailable, ElasticSearchException
import pymongo
from retry import retry_on_exceptions
import config
import time
from pyes import *
# only in beta
# from pyes.queryset import generate_model
__author__ = 'Alexey'

class ESIndex():
    import es_mapping
    index_name = es_mapping.index_name
    doc_type = es_mapping.doc_type
    mapping = es_mapping.mapping

    def connect(self):
        self.conn = ES(config.ES_HOST, timeout=180.0) # Use HTTP
        # self.conn = ES('127.0.0.1:9500') # Use thrift

    def __init__(self, index_name=None):
        if index_name:
            self.index_name = index_name
        self.connect()

    def create_index(self):
        self.conn.indices.delete_index_if_exists(self.index_name)
        self.conn.indices.create_index(self.index_name)
        self.conn.indices.put_mapping(self.doc_type, self.mapping, [self.index_name])

    @retry_on_exceptions(types=[Exception], tries=3, delay=5)
    def add_module(self, module_info, source_files=[]):
        mid = str(module_info['_id'])
        doc = dict(source_files=source_files)
        # for field in ['owner', 'module_name', 'description', 'language', 'watchers']:
        #     if 'watchers' == field:
        #         doc['stars'] = module_info[field]
        #     else:
        #         doc[field] = module_info[field]

        res = self.conn.update(doc, self.index_name, self.doc_type, mid)
        return res and 'ok' in res and res['ok']

    @retry_on_exceptions(types=[Exception], tries=3, delay=5)
    def update_part(self, module_info, source_files):
        script = 'ctx._source.source_files += source_file'
        params = dict(source_file=source_files)
        res = self.conn.partial_update(self.index_name, self.doc_type, module_info['_id'], script, params)
        return res and 'ok' in res and res['ok']

    def add_comments_form_file(self, module_id, doc):
        script = 'ctx._source.source_files += source_file'
        params = dict(source_file=doc)
        self.conn.partial_update(self.index_name, self.doc_type, module_id, script, params)

    def add_comments_form_file_to_mongo(self, collect, module_id, doc):
        # doc['module_id'] = module_id
        collect.insert(doc)

    def is_module_in_index(self, module_id):
        return self.conn.exists(self.index_name, self.doc_type, module_id)

    def get_module(self, module_id):
        return self.conn.get(self.index_name, self.doc_type, module_id)

    @retry_on_exceptions(types=[Exception], tries=5, delay=5)
    def update_module(self, module_info, collect, diff_res):
        doc = self.get_module(module_info['_id'])
        print len(doc['source_files']),
        # Deleted files
        deleted = []
        for files in diff_res['M'], diff_res['D']:
            for filename in files:
                deleted.append(os.path.normpath(filename).lower())

        def source_files_filter(f):
            return os.path.normpath(f['file_name']).lower() not in deleted

        new_source_files = filter(source_files_filter, doc['source_files'])
        new_source_files.extend(list(collect.find({}, {'_id': 0})))
        doc['source_files'] = new_source_files
        print len(doc['source_files'])

        res = self.conn.update(doc, self.index_name, self.doc_type, module_info['_id'])
        return res and 'ok' in res and res['ok']


    def add_module_from_mongo(self, module_info, collect, diff_res=None):
        files_count = collect.count()
        print '\n\tindexing %d files' % files_count,
        logger.info('start indexing %d files' % files_count)
        if files_count == 0:
            return True
        if diff_res:
            print 'update'
            return self.update_module(module_info, collect, diff_res)
        limit = 1000
        for i in range(0, files_count, limit):
            source_files = list(collect.find({}, {'_id': 0}).skip(i).limit(limit))
            print '-',
            while True:
                try:
                    if i == 0:
                       self.add_module(module_info, source_files)
                    else:
                        self.update_part(module_info, source_files)
                    break
                except KeyboardInterrupt:
                    raise
                except (NoServerAvailable, ElasticSearchException):
                    print 'Elastic Search Server Not Available'
                    logger.error('Elastic Search Server Not Available')
                    time.sleep(5)
                    self.connect()
                # except Exception:
                #     print 'Elastic Search Server Not Available'
                #     time.sleep(1)
                #     self.connect()

import unittest
from bson import ObjectId
from pprint import pprint

class IndexTest(unittest.TestCase):
    def setUp(self):
        self.es = ESIndex()
        self.es.index_name += '_test'

    def test_createIndex(self):
        self.es.create_index()
        stat = self.es.conn.index_stats(self.es.index_name)
        # pprint(stat)
        self.assertIsNotNone(stat)

    def test_addModule(self):
        self.test_createIndex()
        m = {
            "_id" : ObjectId("512f19df76000d216b818e84"),
            "created" : "2008-12-05T21:46:18Z",
            "description" : "Port of the Lua programming language for ActionScript using Alchemy",
            "followers" : 122,
            "is_a_fork" : False,
            "language" : "C",
            "module_name" : "lua-alchemy",
            "owner" : "lua-alchemy",
            "pushed" : "2012-03-23T07:42:10Z",
            "pushed_at" : "2012-03-23T07:42:10Z",
            "so_questions_answered" : 0,
            "so_questions_asked" : 0,
            "username" : "lua-alchemy",
            "watchers" : 121
        }
        self.es.add_module(m)

        res = self.es.conn.get(self.es.index_name, self.es.doc_type, m['_id'])

        for f in ['username','so_questions_answered','so_questions_asked','pushed','is_a_fork','watchers','created','pushed_at','followers','_id']:
            del m[f]

        self.assertDictContainsSubset(m, res)

    def test_addComments(self):
        self.test_addModule()
        mid = "512f19df76000d216b818e84"
        result = dict(file_name='src/testfile.txt', file_type='txt', comments=['bla', 'blabla', 'sadferwe'])

        self.es.add_comments_form_file(mid, result)

    def test_addCommentsMongo(self):
        # self.test_addModule()
        mongoConn = pymongo.MongoClient(config.DB_HOST, 27017)
        db = mongoConn[config.DB_NAME]
        db.drop_collection('module_comments_tmp')
        comments_collection = db['module_comments_tmp']

        mid = "512f19df76000d216b818e84"
        for i in range(0, 10):
            result = dict(file_name=('src/testfile_%d.txt' % i), file_type='txt', comments=['bla', 'blabla', 'sadferwe', str(i)])
            self.es.add_comments_form_file_to_mongo(comments_collection, mid, result)

        self.test_createIndex()
        m = {
            "_id" : ObjectId("512f19df76000d216b818e84"),
            "created" : "2008-12-05T21:46:18Z",
            "description" : "Port of the Lua programming language for ActionScript using Alchemy",
            "followers" : 122,
            "is_a_fork" : False,
            "language" : "C",
            "module_name" : "lua-alchemy",
            "owner" : "lua-alchemy",
            "pushed" : "2012-03-23T07:42:10Z",
            "pushed_at" : "2012-03-23T07:42:10Z",
            "so_questions_answered" : 0,
            "so_questions_asked" : 0,
            "username" : "lua-alchemy",
            "watchers" : 121
        }
        self.es.add_module_from_mongo(m, comments_collection)

        res = self.es.conn.get(self.es.index_name, self.es.doc_type, m['_id'])

        for f in ['username','so_questions_answered','so_questions_asked','pushed','is_a_fork','watchers','created','pushed_at','followers','_id']:
            del m[f]

        self.assertDictContainsSubset(m, res)

