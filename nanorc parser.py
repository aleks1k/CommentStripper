import os
from pprint import pprint
import re

__author__ = 'Alexey'

# Parser for nanorc files with syntax highlighting
# Getting comments and file's name regexp
# See git://github.com/craigbarnes/nanorc.git

NANORC_PATH='D:\\Projects\\_Clones\\nanorc'

syntax_patern = re.compile(r'(?:^syntax\s)("(.)+["\s])+')
line_comment_patern = re.compile(r'(?:^COMMENT\:\s+)("(.*?)")+$')
block_comment_patern = re.compile(r'(?:^COMMENT\:\s+)(?:start="(.+?)")\s(?:end="(.+?)")$')
template_comment_patern = re.compile(r'(?:^\+)([\w]+)(?:COMMENT)')

patterns = [syntax_patern, line_comment_patern, block_comment_patern, template_comment_patern]

comment_styles = {
    'C':
        {
            'block_pattern': r'/\*(.*?)\*/',
            'line_pattern': r'//(.*)'
        },
    'HASH':
        {
            'line_pattern': r'#+(.*)'
        },
}

def parse_rc(path):
    res_list = []
    with open(path, 'r') as rcfile:
        for line in rcfile:
            for pattern in patterns:
                result = pattern.match(line)
                if result:
                    if pattern == syntax_patern:
                        ss = [eval(s) for s in result.group(1).split(' ')]
                        res = dict()
                        res_list.append(res)
                        res['type'] = ss[0]
                        res['filename_patterns'] = ss[1:]
                        res['line_pattern'] = []
                        res['block_pattern'] = []
                        print ss[0], ss[1:]
                    elif pattern == line_comment_patern:
                        ss = eval(result.group(1))
                        res['line_pattern'].append(ss)
                        print '\tcomment\t', ss
                    elif pattern == block_comment_patern:
                        start = result.group(1)
                        stop = result.group(2)
                        block_regexp = r'%s(.*?)%s' % (start, stop)
                        res['block_pattern'].append(block_regexp)
                        print '\tblock_comment\t', start, '===', stop, '-------', block_regexp
                    elif pattern == template_comment_patern:
                        style = result.group(1)
                        for i in comment_styles[style]:
                            res[i].append(comment_styles[style][i])
                        print '\tcomment style\t', style
    return res_list

def parse_all():
    results = []
    for file in os.listdir(NANORC_PATH):
        if file.endswith(".nanorc"):
            # print file
            for res in parse_rc(os.path.join(NANORC_PATH, file)):
                if len(res['line_pattern']) or len(res['block_pattern']):
                    results.append(res)
    return results

def main():
    with open('nanorc.py', 'w') as result:
        result.write('nanorc = ')
        pprint(parse_all(), result)

if __name__ == "__main__":
    main()
