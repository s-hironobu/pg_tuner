"""
repository.py

  Copyright (c) 2024-2025, Hironobu Suzuki @ interdb.jp
"""

import sys, os, shutil
from .common import Common, Log


class Repository(Common):
    def __init__(self, base_dir, log_dir):
        self.base_dir = Common.set_dir(base_dir)
        self.log_dir = Common.set_dir(log_dir)

    DEFAULT_DIR_MODE = 0o770
    DEFAULT_HOSTS_CONF_MODE = 0o640


    def _fill_dir(self, num):
        return str(num).zfill(4)


    """
    Public methods
    """

    def check_repo(self):

        # Check self.base_dir
        dirname = self.base_dir
        if os.path.isdir(dirname) == False:
            os.mkdir(dirname, mode=self.DEFAULT_DIR_MODE)
            if Log.notice <= Common.DEFAULT_LOG_LEVEL:
                print("Notice: '{}' created.".format(dirname))

        # Check self.base_dir/self.log_dir
        dirname = self.base_dir + self.log_dir
        if os.path.isdir(dirname) == False:
            os.mkdir(dirname, mode=self.DEFAULT_DIR_MODE)
            if Log.notice <= Common.DEFAULT_LOG_LEVEL:
                print("Notice: '{}' created.".format(dirname))
            return True

        if sum(os.path.exists(os.path.join(dirname, name)) for name in os.listdir(dirname)) == 0:
            if Log.notice <= Common.DEFAULT_LOG_LEVEL:
                print("No files or directories found in ''.".format(dirname))
            return True

        print("====== Confirmation Prompt =====")
        print("Files or directories found in '{}'.".format(dirname))
        print("Select the following options:")
        print("\t1: Quit this task.")
        print("\t2: Remove files and directories and Continue this task.")
        answer = input("Enter 1 or 2: ").lower()
        if answer in ("1", "quit", "exit"):
            return False
        elif answer in ("2"):
            print("Are you sure you want to remove all files and directories in '{}'?".format(dirname))
            answer = input("Enter yes or no: ").lower()
            if answer in ("yes"):
                shutil.rmtree(dirname)
                if Log.notice <= Common.DEFAULT_LOG_LEVEL:
                    print("Notice: rm -rf {}".format(dirname))
                os.mkdir(dirname, mode=self.DEFAULT_DIR_MODE)
                if Log.notice <= Common.DEFAULT_LOG_LEVEL:
                    print("Notice: mkdir {}".format(dirname))
                return True
            else:
                print("Hint: To continue, you have two options:")
                print("\t1. Set a new directory path for `self.log_dir` in conf.py.")
                print("\t2. Back up the existing files in the current log directory yourself.")
                return False


    def get_log_dir(self, num):
        _log_dir = self.base_dir + self.log_dir + self._fill_dir(num) + "/"
        if Log.debug1 <= Common.DEFAULT_LOG_LEVEL:
            print("log_dir=", _log_dir)
        if os.path.exists(_log_dir) == False:
            os.mkdir(_log_dir, mode=self.DEFAULT_DIR_MODE)
        return _log_dir

    """
    def create_base_repo(self):
        # Make repository directory.
        if os.path.exists(self.base_dir) == False:
            os.mkdir(self.base_dir, mode=self.DEFAULT_DIR_MODE)
        # Change permission
        os.chmod(self.base_dir, self.DEFAULT_DIR_MODE)

    def secure_check(self, path, ref_mode):
        if os.path.exists(path) == False:
            if Log.notice <= Common.DEFAULT_LOG_LEVEL:
                print("Notice: '{}' is not found.".format(path))
            return True
        MASK = int(0o777)
        _mode = int(os.stat(path).st_mode & MASK)
        _mode |= ref_mode
        _mode ^= ref_mode
        return True if int(_mode) == 0 else False
    """


if __name__ == "__main__":

    base_dir = "./data_repo"
    log_dir = "test"
    repo = Repository(base_dir, log_dir)

    # repo.check_repo()
