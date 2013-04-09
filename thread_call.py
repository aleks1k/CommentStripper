import StringIO
import codecs
import multiprocessing
import re


def timeout(func, args=(), kwds={}, timeout=1, default=None):
    pool = multiprocessing.Pool(processes=1)
    result = pool.apply_async(func, args=args, kwds=kwds)
    try:
        val = result.get(timeout=timeout)
    except multiprocessing.TimeoutError:
        pool.terminate()
        pool.close()
        pool.join()
        return default
    else:
        pool.close()
        pool.join()
        return val

def parseFile(path, lineRegex=None, blockRegex = None):
    buff_limit = 512 * 1024
    allComments = []
    # if os.path.getsize(path) > self.buff_limit:
    #     return []
    with codecs.open(path, 'r', 'utf-8', errors='ignore') as corpus:
        if blockRegex:
            file_buff = StringIO.StringIO()
            buff_size = 0
        if lineRegex:
            # parse Inline Comments
            for line in corpus:
                line_size = len(line)
                if line_size > 2:
                    if blockRegex and buff_size < buff_limit:
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

        if blockRegex:
            # Second time read file from buffer
            if buff_size < buff_limit and lineRegex:
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

def parseFile_(path, lineRegex=None, blockRegex=None):
    parseFile(path, re.compile(lineRegex), re.compile(blockRegex))

def parseFileInProcess(path, lineRegex=None, blockRegex=None):
    return timeout(parseFile, args=(path, lineRegex, blockRegex,), default=[])

def test_big_file():
    bigcss = 'D:\\repo\\github\\adobe\\brackets\\test\\spec\\ExtensionUtils-test-files\\sub dir\\second.css'
    smallcss = 'D:\\repo\\github\\adobe\\brackets\\test\\spec\\ExtensionUtils-test-files\\sub dir\\fourth.css'
    print parseFileInProcess(bigcss, re.compile(r'([/]{2})(.*)'), re.compile(r'(/\*)((.|\r|\n)*?)(?=\*/)'))
    print parseFileInProcess(smallcss, re.compile(r'([/]{2})(.*)'), re.compile(r'(/\*)((.|\r|\n)*?)(?=\*/)'))

def main():
    test_big_file()

if __name__ == "__main__":
    main()


