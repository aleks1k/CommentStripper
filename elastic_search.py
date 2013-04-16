__author__ = 'Alexey'

from pyes import *
# only in beta
# from pyes.queryset import generate_model

class ESIndex():
    import es_mapping
    index_name = es_mapping.index_name
    doc_type = es_mapping.doc_type
    mapping = es_mapping.mapping

    def __init__(self):
        # self.conn = ES('127.0.0.1:9200') # Use HTTP
        self.conn = ES() # Defaults to connecting to the server at '127.0.0.1:9500'

    def create_index(self):
        self.conn.indices.delete_index_if_exists(self.index_name)
        self.conn.indices.create_index(self.index_name)
        self.conn.indices.put_mapping(self.doc_type, self.mapping, [self.index_name])

    def add_module(self, module_info):
        _id = str(module_info['_id'])
        doc = dict(source_files=[])
        # doc = dict(source_files=[dict(file_name='a',file_type='b',comments=['a', 'b'])])
        for field in ['owner', 'module_name', 'description', 'language', 'watchers']:
            if 'watchers' == field:
                doc['stars'] = module_info[field]
            else:
                doc[field] = module_info[field]

        self.conn.index(doc, self.index_name, self.doc_type, _id)

    def add_comments_form_file(self, module_id, doc):
        script = 'ctx._source.source_files += source_file'
        params = dict(source_file=doc)
        self.conn.partial_update(self.index_name, self.doc_type, module_id, script, params)

    # only in beta
    # def print_all(self):
    #     model = generate_model(self.indexname, self.doc_type)
    #     results = model.objects.all()
    #     for r in results:
    #         print r

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