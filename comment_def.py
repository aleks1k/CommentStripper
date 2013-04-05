#this is my initial idea for how to specify the comment syntax for each language
#this will allow us to look up in the dictionary by file extension
#feedback is welcome
import StringIO
import codecs
import re


class CommentDef:
    def __init__(self, blockRegex, lineRegex, blockContinuation=""):
        self.blockRegexStr = blockRegex
        self.lineRegexStr = lineRegex
        self.blockRegex = re.compile(self.blockRegexStr)
        self.lineRegex = re.compile(self.lineRegexStr)
        self.blockContinuation = blockContinuation


class CommentDictionary:
    def __init__(self):
        cstyle = CommentDef(r'(/\*)((.|[\r\n])*?)(?=\*/)', r'([/]{2})(.*)', "*")
        python = CommentDef(r'([\']{3})([.|\r|\n]*?)(?=([\']{3}))', r'(#)+(.*)')
        perl = CommentDef(r'(=begin)([.|\r|\n]*?)(?=(=cut))', r'(#)+(.*)')
        ruby = CommentDef(r'(=begin)([.|\r|\n]*?)(?=(=end))', r'(#)+(.*)')
        lisp = CommentDef(r'(#|)([.|\r|\n]*?)(?=(|#))', r'(;)+(.*)')
        # text = CommentDef(r'', r'')
        #All block comment should be indicated such that the closing
        #element of the comment is in a lookahead assertion to allow
        #for nested comments

        style_ext = [
            (['c', 'js', 'h', 'cc', 'cpp', 'hpp', 'cs', 'java', 'as', 'd', 'go', 'scala',
              'php', 'phtml', 'php4', 'php3', 'php5', 'phps'], cstyle),
            (['md', 'txt'], None) # text
        ]

        self.reference = {
            'py': python,
            'pl': perl,
            'rb': ruby,
            'lisp': lisp,
            'scm': lisp,
            }

        for s in style_ext:
            for ext in s[0]:
                self.reference[ext] = s[1]


    def parseAllComments(self, path, type):
        allComments = []
        buff_limit = 1024 * 1024
        if type in self.reference:
            comdef = self.reference[type]
            if comdef == None:
                with codecs.open(path, 'r', 'utf-8', errors='ignore') as corpus:
                    text_str = corpus.read()#.replace('\n', ' ')
                    allComments.append(text_str)
            else:
                lineRegex = comdef.lineRegex
                blockRegex = comdef.blockRegex
                with codecs.open(path, 'r', 'utf-8', errors='ignore') as corpus:
                    file_buff = StringIO.StringIO()
                    buff_size = 0
                    # parse Inline Comments
                    for line in corpus:
                        line_size = len(line)
                        if line_size > 2:
                            if buff_size < buff_limit:
                                file_buff.write(line)
                                buff_size += line_size
                            result = lineRegex.match(line)
                            if result:
                                if result.lastindex >= 2:
                                    gr = result.group(2)
                                    if gr:
                                        c = gr.strip()
                                        if len(c) != 0:
                                            allComments.append(c)

                    # Second time read file from buffer
                    if buff_size < buff_limit:
                        file_buff.seek(0)
                        buff = file_buff
                    else:
                        corpus.seek(0)
                        buff = corpus
                    # parse Block Comments
                    results = blockRegex.finditer(buff.read())
                    for result in results:
                        if result.lastindex >= 2:
                            res = result.group(2)
                            if len(res) != 0:
                                allComments.append(res)

        return allComments

    def parseInline(self, fileMappings):
        '''Assumes input is the result of the mapFilesToTypes method in
        cli.py. So long as there's a dictionary mapping file paths to file
        types it should be fine though. Returns all supported inline comments'''
        allComments = []
        for key in fileMappings:
            if fileMappings[key] in self.reference:
                regexPattern = self.reference[key].lineRegex
                with open(key, 'r') as corpus:
                    for line in corpus:
                        if re.match(regexPattern, line):
                            allComments.append(re.match(regexPattern, line).group(2))
        return allComments

    def parseBlock(self, fileMappings):
        '''Similar to parseInline, except this round looks for block comments'''
        allComments = []
        for key in fileMappings:
            if fileMappings[key] in self.reference:
                regexPattern = self.reference[key].blockRegex
                with open(key, 'r').read() as corpus:
                    results = re.finditer(regexPattern, corpus)
                    for result in results:
                        cleanedResult = []
                        result = result.group(2).split('\n')
                        for line in result:
                            cleanedResult.append(line.strip()[len(self.reference[key].blockContinuation):].lower())
                        allComments.append(" ".join(cleanedResult))
        return allComments
					
