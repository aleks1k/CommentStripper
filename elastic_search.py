__author__ = 'Alexey'

from pyes import *
from pyes.queryset import generate_model

# import config
#
# conn = ES(config.DB_HOST + ':9200')
#
# q = TermQuery("name", "joe")
# results = conn.search(query = q)
#
# for r in results:
#     print r
# indexname = 'mongomodules'
class ESIndex():
    indexname = 'comments-index'
    doc_type = 'module'
    def __init__(self):
        self.conn = ES('127.0.0.1:9200') # Use HTTP

        self.conn.indices.delete_index(self.indexname)
        self.conn.indices.create_index(self.indexname)

        #module_name=repo_name, file_name=file, type=type, commets=comments
        mapping = {
        'module_name': {
            'type': 'string',
            },
        'file_name': {
            'type': 'string',
            },
        'type': {
            'index': 'not_analyzed',
            'type': 'string',
            },
        'commets': {
            'type': 'string',
            "index_name" : "comment"
        },
        }
        self.conn.indices.put_mapping(self.doc_type, {'properties':mapping}, [self.indexname])

    def add_to_index(self, docs):
        for d in docs:
            self.conn.index(d, self.indexname, self.doc_type)
        self.conn.indices.refresh(self.indexname)

    def print_all(self):
        model = generate_model(self.indexname, self.doc_type)
        results = model.objects.all()
        for r in results:
            print r
    # results = model.objects.filter(name="joe")
    # for r in results:
    #     print r
