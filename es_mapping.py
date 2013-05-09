__author__ = 'Alexey'

index_name = 'modules-v4'
doc_type = 'module_v2'

mapping = {
    '_all':
        {
            'enabled': False
        },
    'properties':
        {
            'owner': {
                'type': 'string',
                'analyzer': 'suggest_analyzer',
                },
            'module_name': {
                'type': 'string',
                'analyzer': 'suggest_analyzer',
                },
            'description': {
                'type': 'string',
                'analyzer': 'snowball',
                },
            'language': {
                'type': 'string',
                },
            'stars': {
                'type': 'string',
                },
            'source_files': {
                "type": "object",
                "properties": {
                    'file_name': {
                        'type': 'string',
                        },
                    'file_type': {
                        'type': 'string',
                        },
                    'comments': {
                        'type': 'string',
                        'analyzer': 'snowball',
                        },
                    },
                },
            }
}
