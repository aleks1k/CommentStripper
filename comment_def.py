#this is my initial idea for how to specify the comment syntax for each language
#this will allow us to look up in the dictionary by file extension
#feedback is welcome
import StringIO
import codecs
import logging
import os
import re
import time
from nanorc import nanorc


class CommentDef:
    def __init__(self, blockRegex, lineRegex, blockContinuation=""):
        self.blockRegexStr = blockRegex
        self.lineRegexStr = lineRegex
        self.blockRegex = re.compile(self.blockRegexStr, re.DOTALL)
        self.lineRegex = re.compile(self.lineRegexStr)
        self.blockContinuation = blockContinuation


class CommentDictionary:
    curr_regexp = None
    pattern_stat = dict()

    def start_re_search(self, pattern, path):
        self.curr_regexp = pattern
        logging.info('start search block pattern %s in file %s', self.curr_regexp, path)
        self.start_time = time.time()

    def end_re_search(self, comments_count):
        t = time.time() - self.start_time
        # logging.info('end search %f', t)
        st = self.pattern_stat.get(self.curr_regexp)
        if st:
            self.pattern_stat[self.curr_regexp] = (st[0] + t, st[1] + 1, st[2] + comments_count)
        else:
            self.pattern_stat[self.curr_regexp] = (t, 1, comments_count)

    def __init__(self, collect_statistics=False):
        self.collect_statistics = collect_statistics
        cstyle = CommentDef(r'/\*(.*?)\*/', r'//(.*)', "*")
        python = CommentDef(r'[\']{3}(.*?)[\']{3}', r'#+(.*)')
        perl = CommentDef(r'=begin(.*?)=cut', r'#+(.*)')
        ruby = CommentDef(r'=begin(.*?)=end', r'#+(.*)')
        lisp = CommentDef(r'#\|(.*?)\|#', r';+(.*)')
        powershell = CommentDef(r'<#(.*?)>#', r'#+(.*)')
        # text = CommentDef(r'', r'')
        #All block comment should be indicated such that the closing
        #element of the comment is in a lookahead assertion to allow
        #for nested comments

        style_ext = [
            (['c', 'js', 'json', 'h', 'cc', 'cpp', 'hpp', 'cs', 'java', 'as', 'd', 'go', 'scala',
              'php', 'phtml', 'php4', 'php3', 'php5', 'phps', 'css', 'scss', 'sass', 'less'], cstyle),
            (['md', 'txt'], None) # text
        ]

        self.reference = {
            'py': python,
            'pl': perl,
            'rb': ruby,
            'lisp': lisp,
            'scm': lisp,
            'ps1': powershell,
            }

        for s in style_ext:
            for ext in s[0]:
                self.reference[ext] = s[1]

        # Compile nanorc regexp
        self.nanorc = []
        for drc in nanorc:
            rc = dict(filename_regex=[],line_regex=[],block_regex=[],type=drc['type'])
            self.nanorc.append(rc)
            for file_pattern in drc['filename_patterns']:
                rc['filename_regex'].append(re.compile(r'.*'+file_pattern))
                for l in drc['line_pattern']:
                    rc['line_regex'].append(re.compile(l))
                for b in drc['block_pattern']:
                    rc['block_regex'].append(re.compile(b, re.DOTALL))

    # @staticmethod
    def parseFile(self, path, lineRegex=None, blockRegex = None):
        buff_limit = 512 * 1024
        allComments = []
        lineRegex_comments_count = 0
        # if os.path.getsize(path) > self.buff_limit:
        #     return []
        with codecs.open(path, 'r', 'utf-8', errors='ignore') as corpus:
            if blockRegex:
                file_buff = StringIO.StringIO()
                buff_size = 0
            if lineRegex:
                # parse Inline Comments
                if self.collect_statistics: self.start_re_search(lineRegex.pattern, path)
                for line in corpus:
                    line_size = len(line)
                    if line_size > 2:
                        if blockRegex and buff_size < buff_limit:
                            file_buff.write(line)
                            buff_size += line_size
                        result = lineRegex.search(line)
                        if result:
                            if result.lastindex >= 1:
                                gr = result.group(1)
                                if gr:
                                    c = gr.strip()
                                    if len(c) != 0:
                                        allComments.append(c)
                if self.collect_statistics:
                    lineRegex_comments_count = len(allComments)
                    self.end_re_search(len(allComments))

            if blockRegex:
                # Second time read file from buffer
                if buff_size < buff_limit and lineRegex:
                    file_buff.seek(0)
                    buff = file_buff
                else:
                    corpus.seek(0)
                    buff = corpus
                    # parse Block Comments
                if self.collect_statistics: self.start_re_search(blockRegex.pattern, path)
                results = blockRegex.finditer(buff.read())
                for result in results:
                    if result.lastindex >= 1:
                        res = result.group(1)
                        if len(res) != 0:
                            allComments.append(res)
                if self.collect_statistics: self.end_re_search(len(allComments) - lineRegex_comments_count)
        return allComments

    def parseAllComments(self, path, file_type=None):
        allComments = []
        if not file_type:
            file_type = os.path.splitext(path)[1][1:].lower()
        if file_type in self.reference:
            comdef = self.reference[file_type]
            if comdef == None:
                with codecs.open(path, 'r', 'utf-8', errors='ignore') as corpus:
                    text_str = corpus.read()#.replace('\n', ' ')
                    allComments.append(text_str)
            else:
                allComments = self.parseFile(path, comdef.lineRegex, comdef.blockRegex)
        else: # use nanorc rules
            parsed = False
            for drc in self.nanorc:
                for file_pattern in drc['filename_regex']:
                    if file_pattern.match(path):
                        i = 0
                        while True:
                            if len(drc['line_regex']) > i:
                                lineRegex = drc['line_regex'][i]
                            else:
                                lineRegex = None
                            if len(drc['block_regex']) > i:
                                blockRegex = drc['block_regex'][i]
                            else:
                                blockRegex = None
                            if lineRegex or blockRegex:
                                allComments.extend(self.parseFile(path, lineRegex, blockRegex))
                            else:
                                break
                            i += 1
                        # if len(allComments):
                        #     print type
                        parsed = True
                        break
                if parsed:
                    break
        return allComments

def test_big_file():
    from pprint import pprint
    files = [
        r'\repo\github\joyent\node\deps\npm\lib\outdated.js',
        'D:\\repo\\github\\adobe\\brackets\\test\\spec\\ExtensionUtils-test-files\\sub dir\\second.css',
        'D:\\repo\\github\\adobe\\brackets\\test\\spec\\ExtensionUtils-test-files\\sub dir\\fourth.css',
    ]
    c = CommentDictionary()
    for f in files:
        # c.parseFile(f, re.compile(r'([/]{2})(.*)'), re.compile(r'(/\*)(.*?)\*/', re.DOTALL))
        pprint(c.parseAllComments(f))

def main():
    test_big_file()

if __name__ == "__main__":
    main()


