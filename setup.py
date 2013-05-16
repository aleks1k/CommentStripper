__author__ = 'Alexey'
# setup py
from distutils.core import setup

setup(name = 'CommentStripper',
      version = '1.0',
      py_modules = ['parse_comments', 'comment_def', 'nanorc'],
      scripts = ['nanorc parser.py'],
      author = 'Alexey Knyazev',
      author_email = 'aleks.kn@gmail.com',
      url = 'https://github.com/aleks1k/CommentStripper',
      description = 'A python library for the automated scraping code comments across many languages within a file directory'
      )