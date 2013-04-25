import os
import errno
from pprint import pprint
import stat
import traceback
import pymongo
import sys
import config
import git

__author__ = 'Alexey'


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def get_path(id):
    path = config.GITHUB_REPOS_CLONE_PATH + ('/%(user)s/%(repo)s' % id)
    make_sure_path_exists(path)
    return path

class LogRemoteProgress(git.RemoteProgress):

    def __init__(self, name):
        git.RemoteProgress.__init__(self)
        self.procces_name = name

    def line_dropped(self, line):
        """Called whenever a line could not be understood and was therefore dropped."""
        pass

    def update(self, op_code, cur_count, max_count=None, message=''):
        """Called whenever the progress changes

        :param op_code:
            Integer allowing to be compared against Operation IDs and stage IDs.

            Stage IDs are BEGIN and END. BEGIN will only be set once for each Operation
            ID as well as END. It may be that BEGIN and END are set at once in case only
            one progress message was emitted due to the speed of the operation.
            Between BEGIN and END, none of these flags will be set

            Operation IDs are all held within the OP_MASK. Only one Operation ID will
            be active per call.
        :param cur_count: Current absolute count of items

        :param max_count:
            The maximum count of items we expect. It may be None in case there is
            no maximum number of items or if it is (yet) unknown.

        :param message:
            In case of the 'WRITING' operation, it contains the amount of bytes
            transferred. It may possibly be used for other purposes as well.

        You may read the contents of the current line in self._cur_line"""
        if max_count != None and max_count != '':
            try:
                progress = float(cur_count) / int(max_count) * 100
                sys.stdout.write("%s progress: %d%%   \r" % (self.procces_name, progress))
                sys.stdout.flush()
            except:
                pass
            # print persent_complete

def git_update(id):
    remote_path = 'git://github.com/%(user)s/%(repo)s.git'
    path = get_path(id)
    repo = git.Repo.init(path, bare=False)
    # repo = Repo(path)
    # origin = repo.create_remote('origin', 'git@github.com:aleks1k/ec2_tools.git')
    origin_exist = False
    for r in repo.remotes:
        if r.name == 'origin':
            origin_exist = True
            origin = r
            break
    if not origin_exist:
        origin = repo.create_remote('origin', remote_path % id)

    origin.fetch(progress=LogRemoteProgress('Fetch'))                       # fetch, pull and push from and to the remote
    # origin.pull('refs/heads/master:refs/heads/origin', progress=LogRemoteProgress('Pull'))

def git_fetch(id):
    path = get_path(id)
    repo = git.Repo(path)
    for remote in repo.remotes:
        print remote.name
        remote.fetch(progress=LogRemoteProgress('Fetch'))

def git_pull(id, save_update=None):
    path = get_path(id)
    repo = git.Repo(path)
    remote = repo.remotes.origin
    # print remote.name
    old_commit = str(repo.head.commit)
    os.environ['GIT_PYTHON_TRACE'] = 'full'
    remote.pull()#progress=LogRemoteProgress('Pull'))
    new_commit = str(repo.head.commit)
    if save_update and old_commit != new_commit:
        save_update(old_commit, new_commit)

def git_clone(id):
    remote_path = 'git://github.com/%(user)s/%(repo)s.git'
    path = get_path(id)
    git.Repo.clone_from(remote_path % id, path, progress=LogRemoteProgress('Clone'))

def check_git_repo_exist(path):
    return os.path.exists(path + '/.git')

def get_changed_files(diff):
    res = dict()
    for t in ['A', 'D', 'M']:
        files = []
        for diff_added in diff.iter_change_type(t):
            if t == 'A':
                files.append(diff_added.b_blob.path)
            else:
                files.append(diff_added.a_blob.path)
        res[t] = files
    return res

def git_diff(path, old_commit, new_commit):
    repo = git.Repo(path)
    hcommit = repo.head.commit
    # idiff = hcommit.diff()          # diff tree against index
    tdiff = hcommit.diff(old_commit)  # diff tree against previous tree
    # for diff_added in tdiff.iter_change_type('M'):
    res = get_changed_files(tdiff)
    return res
    # pprint(res)

def drop_dir(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))

def main():
    mongoConn = pymongo.MongoClient(config.DB_HOST, 27017)
    db = mongoConn[config.DB_NAME]
    modules_collection = db['modules']
    modules = modules_collection.find().limit(50)



    count = modules.count()
    i = 0
    err_modules = open('not_cloned_modules.txt', 'w')
    for module in modules:
        id = dict(user=module['owner'], repo=module['module_name'])
        i += 1
        try:
            print '(%d/%d)' % (i, count), '%(user)s/%(repo)s' % id
            if check_git_repo_exist(get_path(id)):
                def save_update_to_db(old_commit, new_commit):
                    module_id = module['_id']
                    updates = db['module_updates']
                    item = updates.find_one(module_id) # id update item equal module id
                    if not item:
                        item = dict(_id=module_id, old_commit=old_commit, new_commit=new_commit)
                    else:
                        item['new_commit'] = new_commit

                    updates.save(item)

                # git_diff(id)
                git_pull(id, save_update_to_db)
            else:
                git_clone(id)
            sys.stdout.write("Done!\n")
            sys.stdout.flush()
        except git.exc.GitCommandError as ex:
            if ex.status == 128:
                sys.stdout.write("Repository not found.\n")
                sys.stdout.flush()
                drop_dir(get_path(id))
            err_modules.write('%(user)s/%(repo)s\n' % id)
            err_modules.write(traceback.format_exc())
            err_modules.flush()
        except Exception as ex:
            try:
                print 'try make clone repo again...\n'
                drop_dir(get_path(id))#, ignore_errors=True)
                git_clone(id)
                sys.stdout.write("Done!\n")
                sys.stdout.flush()
            except Exception as ex:
                    err_modules.write('%(user)s/%(repo)s\n' % id)
                    err_modules.write(traceback.format_exc())
                    err_modules.flush()
    err_modules.close()

    updates = db['module_updates']
    for d in updates.find():
        module = modules_collection.find_one(dict(_id=d['_id']))
        id = dict(user=module['owner'], repo=module['module_name'])
        if check_git_repo_exist(get_path(id)):
            git_diff(id, d['old_commit'], d['new_commit'])


if __name__ == "__main__":
    main()
