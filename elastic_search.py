__author__ = 'Alexey'

from pyes import *
# only in beta
# from pyes.queryset import generate_model

class ESIndex():
    indexname = 'comments-index'
    doc_type = 'module'
    def __init__(self):
        # self.conn = ES('127.0.0.1:9200') # Use HTTP
        self.conn = ES() # Defaults to connecting to the server at '127.0.0.1:9500'

    def create_index(self):
        self.conn.indices.delete_index_if_exists(self.indexname)
        self.conn.indices.create_index(self.indexname)

        #module_name=repo_name, file_name=file, type=type, commets=comments
        mapping = {
            'module_id': {
                'type': 'string',
                'index': 'not_analyzed',
            },
            'owner': {
                'type': 'string',
                },
            'module_name': {
                'type': 'string',
                },
            'description': {
                'type': 'string',
                },
            'file_name': {
                'type': 'string',
            },
            'file_type': {
                # 'index': 'not_analyzed',
                'type': 'string',
            },
            'comments': {
                'type': 'string',
                "index_name": "comment"
            },
        }
        self.conn.indices.put_mapping(self.doc_type, {'properties':mapping}, [self.indexname])

    def add_to_index(self, docs, module_info, bulk=False):
        for d in docs:
            for field in ['module_id', 'owner', 'module_name', 'description']:
                if field == 'module_id':
                    d[field] = str(module_info['_id'])
                else:
                    d[field] = module_info[field]
            self.conn.index(d, self.indexname, self.doc_type, bulk=bulk)
        if bulk:
            self.conn.indices.refresh(self.indexname)

    # only in beta
    # def print_all(self):
    #     model = generate_model(self.indexname, self.doc_type)
    #     results = model.objects.all()
    #     for r in results:
    #         print r
