import os
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

def parse_rc(path):
    with open(path, 'r') as rcfile:
        for line in rcfile:
            for pattern in patterns:
                result = pattern.match(line)
                if result:
                    if pattern == syntax_patern:
                        ss = [eval(s) for s in result.group(1).split(' ')]
                        print ss[0], ss[1:]
                    elif pattern == line_comment_patern:
                        ss = result.group(1)
                        print '\tcomment\t', ss
                    elif pattern == block_comment_patern:
                        start = result.group(1)
                        stop = result.group(2)
                        print '\tblock_comment\t', start, '===', stop
                    elif pattern == template_comment_patern:
                        style = result.group(1)
                        print '\tcomment style\t', style

def main():
    for file in os.listdir(NANORC_PATH):
        if file.endswith(".nanorc"):
            # print file
            parse_rc(os.path.join(NANORC_PATH, file))

if __name__ == "__main__":
    main()
