"""
pg.py

  Copyright (c) 2024-2025, Hironobu Suzuki @ interdb.jp
"""

import warnings
import paramiko
import subprocess
import sys, os, shutil

from .common import Common, Log

class PG:
    def __init__(
        self,
        host,
        pg_ctl,
        pgdata,
        pgdata_backup,
        server_user=None,
        server_passwd=None,
    ):
        self.host = host
        self.pg_ctl = pg_ctl
        self.pgdata = Common.set_dir(pgdata)
        self.pgdata_backup = Common.set_dir(pgdata_backup)
        self.server_user = server_user
        self.server_passwd = server_passwd

        self.conf_filename = Common.ADDITIONAL_CONF
        self.pgconf_dir = Common.set_dir(Common.ADDITIONAL_CONF_DIR)

        self.banner_timeout = Common.BANNER_TIMEOUT
        self.auth_timeout = Common.AUTH_TIMEOUT
        self.channel_timeout = Common.CHANNEL_TIMEOUT

        warnings.simplefilter("ignore")

    def _stderr(self, stderr, msg):
        if len(stderr.read()) > 0:
            print("{}".format(str(msg)))
            return False
        else:
            return True


    def _exec_remote(self, command):

        with paramiko.SSHClient() as client:
            try:
                client.set_missing_host_key_policy(paramiko.WarningPolicy())
                client.connect(
                    self.host,
                    username=self.server_user,
                    password=self.server_passwd,
                    banner_timeout=self.banner_timeout,
                    auth_timeout=self.auth_timeout,
                    channel_timeout=self.channel_timeout,
                    timeout=self.channel_timeout,
                )
                try:
                    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
                    for line in stderr:
                        print(line, end="")
                    for line in stdout:
                        print(line, end="")
                finally:
                    client.close()

                return True

            except Exception as e:
                print("\nError: Cannot access to host with SSH:'{}'".format(str(self.host)))
                print("Detail: {}".format(str(e)))
                sys.exit(1)


    def _exist_remote_file(self, filename):
        ret = True
        with paramiko.SSHClient() as client:
            try:
                client.set_missing_host_key_policy(paramiko.WarningPolicy())

                client.connect(
                    self.host,
                    username=self.server_user,
                    password=self.server_passwd,
                    banner_timeout=self.banner_timeout,
                    auth_timeout=self.auth_timeout,
                    channel_timeout=self.channel_timeout,
                    timeout=self.channel_timeout,
                )
                try:
                    sftp_connection = client.open_sftp()
                    sftp_connection.stat(filename)
                except Exception as e:
                    ret = False
                finally:
                    client.close()
                del client

                if sftp_connection == None:
                    return False
                return ret

            except Exception as e:
                print("Error: Cannot access to host with SSH:'{}'".format(str(self.host)))
                print("Detail: {}".format(str(e)))
                sys.exit(1)


    def _copy_file(self, source, target):
        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: Copy file:")
            print("\tsource=", source)
            print("\ttarget=", target)

        if self.host == "localhost" or self.host == "127.0.0.1":
            cmd = "cp {} {}".format(str(source), str(target))
            try:
                ret = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print("Error: {}".format(str(e.stdout)))
                return False
            return True

        else:
            ret = True
            with paramiko.SSHClient() as client:
                try:
                    client.set_missing_host_key_policy(paramiko.WarningPolicy())

                    client.connect(
                        self.host,
                        username=self.server_user,
                        password=self.server_passwd,
                        banner_timeout=self.banner_timeout,
                        auth_timeout=self.auth_timeout,
                        channel_timeout=self.channel_timeout,
                        timeout=self.channel_timeout,
                    )
                    try:
                        sftp_connection = client.open_sftp()
                        sftp_connection.put(source, target)
                    except Exception as e:
                        ret = False
                    finally:
                        client.close()
                    del client

                    if sftp_connection == None:
                        return False
                    return ret

                except Exception as e:
                    print("Error: Cannot access to host with SSH:'{}'".format(str(self.host)))
                    print("Detail: {}".format(str(e)))
                    sys.exit(1)

    def _cmd(self, command):
        cmd = "{} -D {} {}".format(self.pg_ctl, self.pgdata, command)
        if self.host == "localhost" or self.host == "127.0.0.1":
            try:
                ret = subprocess.run(cmd, shell=True, capture_output=False, check=True)
            except subprocess.CalledProcessError as e:
                print("Error: {}".format(str(e.stdout)))
                return False
            return True
        else:
            return self._exec_remote(cmd)

    """
    Public methods
    """

    """
    # executes cmd locally
    """
    def exec_local(self, cmd, shell=True, return_output=False, check=True):
        if Log.debug1 <= Common.DEFAULT_LOG_LEVEL:
            print("Debug1: command '{}'".format(str(cmd)))
        try:
            ret = subprocess.run(cmd, shell=shell, check=check, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print("Error: {}".format(str(e.stdout)))
            return False
        if return_output:
            return ret.stdout
        else:
            return True

    """
    # Check the file/dir exists or not
    """
    def is_exist(self, filename):
        if self.host == "localhost" or self.host == "127.0.0.1":
            return os.path.isfile(filename)
        else:
            return self._exist_remote_file(filename)

    def is_dir_exist(self, dirname):
        if self.host == "localhost" or self.host == "127.0.0.1":
            return os.path.isdir(dirname)
        else:
            return self._exist_remote_file(dirname)

    """
    # remove pgdata directory
    """
    def rm_pgdata(self):

        if self.is_dir_exist(self.pgdata_backup) == False:
            print("Error: backup dir '{}' not found.".format(self.pgdata_backup))
            return False

        if self.host == "localhost" or self.host == "127.0.0.1":
            shutil.rmtree(self.pgdata)
            if Log.notice <= Common.DEFAULT_LOG_LEVEL:
                print("Notice: rm -rf {}".format(self.pgdata))
            return True
        else:
            cmd = "rm -rf {}".format(self.pgdata)
            return self._exec_remote(cmd)

    """
    # remove pgdata_backup dir
    """
    def rm_pgdata_backup(self):

        if self.is_dir_exist(self.pgdata_backup) == False:
            if Log.notice <= Common.DEFAULT_LOG_LEVEL:
                print("Notice: backup dir '{}' not found.".format(self.pgdata_backup))
            return False

        if self.host == "localhost" or self.host == "127.0.0.1":
            shutil.rmtree(self.pgdata_backup)
            if Log.notice <= Common.DEFAULT_LOG_LEVEL:
                print("Notice: rm -rf {}".format(self.pgdata_backup))
            return True
        else:
            cmd = "rm -rf {}".format(self.pgdata_backup)
            return self._exec_remote(cmd)


    """
    # make backup
    """
    def make_backup(self):
        force_remove = False

        if self.is_dir_exist(self.pgdata_backup):
            print("====== Confirmation Prompt =====")
            print("backup dir '{}' already exists.".format(self.pgdata_backup))
            print("Select the following options:")
            print("\t1: Quit this task.")
            print("\t2: Remove the backup dir and Continue this task.")
            answer = input("Enter 1 or 2: ").lower()
            if answer in ("1", "quit", "exit"):
                return False
            elif answer in ("2"):
                print("Are you sure you want to remove backup dir '{}'?".format(self.pgdata_backup))
                answer = input("Enter yes or no: ").lower()
                if answer in ("yes"):
                    force_remove = True
                else:
                    return False

        if force_remove:
            cmd = "rm -rf {}; cp -r {} {}".format(self.pgdata_backup, self.pgdata, self.pgdata_backup)
        else:
            cmd = "cp -r {} {}".format(self.pgdata, self.pgdata_backup)
        if self.host == "localhost" or self.host == "127.0.0.1":
            print("Currently running '{}'".format(cmd))
            ret = self.exec_local(cmd)
        else:
            print("Currently running '{}'".format(cmd))
            ret = self._exec_remote(cmd)

        if ret:
            print("... done.")
        else:
            print("... failed.")

        return ret

    """
    # recover backup file
    """
    def restore_backup(self):
        if self.is_dir_exist(self.pgdata_backup) == False:
            print("Error: backup dir '{}' not found.".format(self.pgdata_backup))
            return False

        if self.is_dir_exist(self.pgdata):
            if self.host == "localhost" or self.host == "127.0.0.1":
                shutil.rmtree(self.pgdata)
            else:
                cmd = "rm -rf {}".format(self.pgdata)
                if self._exec_remote(cmd) == False:
                    print("Error: Could not remove '{}'".format(self.pgdata))
                    return False

        cmd = "cp -r {} {}".format(self.pgdata_backup, self.pgdata)
        if self.host == "localhost" or self.host == "127.0.0.1":
            print("Currently running '{}'".format(cmd))
            ret = self.exec_local(cmd)
        else:
            print("Currently running '{}'".format(cmd))
            ret = self._exec_remote(cmd)

        if ret:
            print("... done.")
        else:
            print("... failed.")

        return ret

    """
    # server start
    """
    def start(self):
        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: PostgreSQL server start.")
        return self._cmd("start")

    """
    # server restart
    """
    def restart(self):
        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: PostgreSQL server restart.")
        return self._cmd("restart")

    """
    # server stop
    """
    def stop(self):
        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: PostgreSQL server stop.")
        return self._cmd("stop")

    """
    # server reload
    """
    def reload(self):
        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: PostgreSQL server reload.")
        return self._cmd("reload")


    """
    # get server status
    """
    def is_running(self):
        cmd = "{} -D {} status | grep 'no server running' | wc -l".format(
            self.pg_ctl, self.pgdata
        )

        if self.host == "localhost" or self.host == "127.0.0.1":
            ret = self.exec_local(cmd, return_output=True)
            if ret == False:
                sys.exit(1)
            if int(ret) == 1:  # no server running
                return False
            else:
                return True

        else:
            with paramiko.SSHClient() as client:
                try:
                    client.set_missing_host_key_policy(paramiko.WarningPolicy())
                    client.connect(
                        self.host,
                        username=self.server_user,
                        password=self.server_passwd,
                        banner_timeout=self.banner_timeout,
                        auth_timeout=self.auth_timeout,
                        channel_timeout=self.channel_timeout,
                        timeout=self.channel_timeout,
                    )
                    try:
                        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
                        for line in stdout:
                            ret = int(line)
                    finally:
                        client.close()

                    if ret == 1:
                        return False
                    else:
                        return True

                except Exception as e:
                    print("\nError: Cannot access to host with SSH:'{}'".format(str(self.host)))
                    print("Detail: {}".format(str(e)))
                    sys.exit(1)

    """
    # Creates additional conf file and copies to PostgreSQL server
    """
    def set_conf(self, conf_params, max_connections=None):

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: send additional configuration file to postgresql server.")

        # write test.conf
        with open(self.conf_filename, "w") as o:
            for row in conf_params:
                print("{} = {}".format(str(row[0]), str(row[1])), file=o)

            if max_connections != None:
                print("max_connections = {}".format(max_connections), file=o)

        ret = self._copy_file(self.conf_filename, self.pgdata + self.pgconf_dir + str(self.conf_filename))

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            if ret:
                print("Info: File sent.")
            else:
                print("Error: Failed to send file.")
        return ret

    """
    # Checks PostgreSQL server configuration
    """
    def check(self, restore_everytime, linux_monitoring):
        if self.host == "localhost" or self.host == "127.0.0.1":
            return self._check_local(restore_everytime, linux_monitoring)
        else:
            return self._check_remote(restore_everytime, linux_monitoring)


    def _check_local(self, restore_everytime, linux_monitoring):

        print("Server Check Start.")

        count = 1
        print("({}) Check directories:".format(count))
        for d in [self.pg_ctl, self.pgdata, self.pgdata + self.pgconf_dir]:
            _cmd = "ls {}".format(str(d))
            if self.exec_local(_cmd) == False:
                print("Error: '{}' not found.".format(d))
                sys.exit(1)

        print("ok.")

        if restore_everytime:
            count += 1
            print("({}) Check backup file:".format(count))
            if self.is_exist(self.pgdata_backup):
                print("backup file:'{}' exists.".format(self.pgdata_backup))
                print("ok.")
            else:
                print("backup file:'{}' not found.".format(self.pgdata_backup))
                print("Warning: Create a backup using the 'pg_tuner.py backup' command before running the task.".format(self.pgdata_backup))

        count += 1
        print("({}) Check preload libraries:".format(count))
        for module in Common.REQUIRED_MODULES:
            if linux_monitoring == False:
                # Skip this check
                break

            # This command cannot completely prevent module leakage.
            _cmd = 'grep "^shared_preload_libraries" {} | grep {} | wc -l'.format(
                str(self.pgdata) + "postgresql.conf", str(module)
            )
            ret = self.exec_local(_cmd, return_output=True)
            if ret == False:
                sys.exit(1)

            if int(ret) != 1:
                print("Error: {} module not found in shared_preload_libraries".format(module))
                sys.exit(1)

        print("ok.")

        # Get max_connections
        _conn = {
            "max_connections": Common.DEFAULT_MAX_CONNECTIONS,
            "reserved_connections": Common.DEFAULT_RESERVED_CONNECTIONS,
            "superuser_reserved_connections": Common.DEFAULT_SUPERUSERRESERVED_CONNECTIONS,
        }

        for _key in _conn.keys():
            _cmd = 'grep "^\s*{}" {}'.format(_key, str(self.pgdata) + "postgresql.conf")
            ret = self.exec_local(_cmd, return_output=True, check=False)
            if ret == False:
                continue

            for line in str(ret).split("\n"):
                if len(line) == 0:
                    break
                token = line.split("=")
                word = token[1].split()
                _conn[_key] = int(word[0])

                if Log.debug3 <= Common.DEFAULT_LOG_LEVEL:
                    print("Update: _conn[{}]={}".format(_key, _conn[_key]))

        for _key in _conn.keys():
            if Log.debug3 <= Common.DEFAULT_LOG_LEVEL:
                print("_conn[{}]={}".format(_key, _conn[_key]))
        print("ok.")

        count += 1
        print("({}) Check include_if_exists dir:".format(count))
        _cmd = "grep include_if_exists {} | grep '{}{}' | wc -l".format(
            str(self.pgdata) + "postgresql.conf", self.pgconf_dir, self.conf_filename
        )
        ret = self.exec_local(_cmd, return_output=True)
        if ret == False:
            sys.exit(1)

        if int(ret) != 1:
            print("Error: '{}{}' not set in include_if_exists".format(self.pgconf_dir, self.conf_filename))
            sys.exit(1)

        print("ok.")

        # start stop
        count += 1
        print("({}) Check postgresql server status:".format(count))

        _cmd = "{} -D {} status | grep 'no server running' | wc -l".format(
            self.pg_ctl, self.pgdata
        )
        ret = self.exec_local(_cmd, return_output=True)
        if ret == False:
            sys.exit(1)

        if int(ret) == 1:  # no server running
            print("Error: no server running. Start your postgresql server.")
            sys.exit(1)
        print("ok.")

        count += 1
        print("({}) postgresql server stop:".format(count))
        _cmd = "{} -D {} stop".format(self.pg_ctl, self.pgdata)
        if self.exec_local(_cmd) == False:
            sys.exit(1)
        print("ok.")

        count += 1
        print("({}) postgresql server start:".format(count))
        _cmd = "{} -D {} start".format(self.pg_ctl, self.pgdata)
        try:
            ret = subprocess.run(_cmd, shell=True, capture_output=False, check=True)
        except subprocess.CalledProcessError as e:
            print("Error: {}".format(str(e.stdout)))
            sys.exit(1)

        print("ok.")

        print("Server Check finished.")
        return True, [
            _conn["max_connections"],
            _conn["reserved_connections"],
            _conn["superuser_reserved_connections"],
        ]

    def _check_remote(self, restore_everytime, linux_monitoring):

        print("Server Check Start.")

        count = 1
        print("({}) Access to {}:".format(count, self.host))
        with paramiko.SSHClient() as client:
            try:
                client.set_missing_host_key_policy(paramiko.WarningPolicy())
                client.connect(
                    self.host,
                    username=self.server_user,
                    password=self.server_passwd,
                    banner_timeout=self.banner_timeout,
                    auth_timeout=self.auth_timeout,
                    channel_timeout=self.channel_timeout,
                    timeout=self.channel_timeout,
                )
            except Exception as e:
                print("Error: Cannot access to host with SSH:'{}'".format(str(self.host)))
                print("Detail: {}".format(str(e)))
                sys.exit(1)

            print("ok.")

            if restore_everytime:
                count += 1
                print("({}) Check backup file:".format(count))
                _cmd = "ls {}".format(self.pgdata_backup)
                stdin, stdout, stderr = client.exec_command(_cmd, get_pty=False)
                if self._stderr(stderr, "backup file:'{}' not found.".format(self.pgdata_backup)) == False:
                    print("\n** Warning **: Create a backup using the 'pg_tuner.py backup' command before running the task.\n".format(self.pgdata_backup))
                else:
                    print("backup file:'{}' exists.".format(self.pgdata_backup))
                    print("ok.")


            count += 1
            print("({}) Check directories:".format(count))
            for d in [self.pg_ctl, self.pgdata, self.pgdata + self.pgconf_dir]:
                _cmd = "ls {}".format(str(d))
                stdin, stdout, stderr = client.exec_command(_cmd, get_pty=False)
                if self._stderr(stderr, "Error: '{}' not found.".format(d)) == False:
                    sys.exit(1)

            print("ok.")

            count += 1
            print("({}) Check preload libraries:".format(count))
            for module in Common.REQUIRED_MODULES:

                if linux_monitoring == False:
                    # Skip this check
                    break

                # This command cannot completely prevent module leakage.
                _cmd = 'grep "^shared_preload_libraries" {} | grep {} | wc -l'.format(
                    str(self.pgdata) + "postgresql.conf", str(module)
                )
                stdin, stdout, stderr = client.exec_command(_cmd, get_pty=False)
                if (
                    self._stderr(stderr, "Error: '{}' returns error.".format(str(_cmd)))
                    == False
                ):
                    sys.exit(1)

                for line in stdout:
                    if int(line) != 1:
                        print("Error: {} module not found in shared_preload_libraries".format(module))
                        sys.exit(1)

            print("ok.")


            count += 1
            print("({}) Check max_connections:".format(count))
            # Get max_connections
            _conn = {
                "max_connections": Common.DEFAULT_MAX_CONNECTIONS,
                "reserved_connections": Common.DEFAULT_RESERVED_CONNECTIONS,
                "superuser_reserved_connections": Common.DEFAULT_SUPERUSERRESERVED_CONNECTIONS,
            }

            for _key in _conn.keys():
                _cmd = 'grep "^\s*{}" {}'.format(_key, str(self.pgdata) + "postgresql.conf")
                stdin, stdout, stderr = client.exec_command(_cmd, get_pty=False)
                if (
                    self._stderr(stderr, "Error: '{}' returns error.".format(str(_cmd)))
                    == False
                ):
                    sys.exit(1)

                for line in stdout:
                    token = line.split("=")
                    word = token[1].split()
                    _conn[_key] = int(word[0])

                    if Log.debug3 <= Common.DEFAULT_LOG_LEVEL:
                        print("Update: _conn[{}]={}".format(_key, _conn[_key]))

            for _key in _conn.keys():
                if Log.debug3 <= Common.DEFAULT_LOG_LEVEL:
                    print("_conn[{}]={}".format(_key, _conn[_key]))

            print("ok.")

            count += 1
            print("({}) Check include_if_exists dir:".format(count))
            _cmd = "grep include_if_exists {} | grep '{}{}' | wc -l".format(
                str(self.pgdata) + "postgresql.conf",
                self.pgconf_dir,
                self.conf_filename,
            )
            stdin, stdout, stderr = client.exec_command(_cmd, get_pty=False)
            if (
                self._stderr(stderr, "Error: '{}' returns error.".format(str(_cmd)))
                == False
            ):
                sys.exit(1)

            for line in stdout:
                if int(line) != 1:
                    print("Error: '{}{}' not set in include_if_exists".format(self.pgconf_dir, self.conf_filename))
                    sys.exit(1)

            print("ok.")

            # start stop
            count += 1
            print("({}) Check postgresql server status:".format(count))
            _cmd = "{} -D {} status | grep 'no server running' | wc -l".format(self.pg_ctl, self.pgdata)
            stdin, stdout, stderr = client.exec_command(_cmd, get_pty=False)
            if (
                self._stderr(stderr, "Error: '{}' returns error.".format(str(_cmd)))
                == False
            ):
                sys.exit(1)

            for line in stdout:
                if int(line) == 1:  # no server running
                    print("Error: no server running. Start your postgresql server.")
                    sys.exit(1)
            print("ok.")

            count += 1
            print("({}) postgresql server stop:".format(count))
            _cmd = "{} -D {} stop".format(self.pg_ctl, self.pgdata)
            stdin, stdout, stderr = client.exec_command(_cmd, get_pty=True)
            if (
                self._stderr(stderr, "Error: '{}' returns error.".format(str(_cmd)))
                == False
            ):
                sys.exit(1)
            print("ok.")

            count += 1
            print("({}) postgresql server start:".format(count))
            _cmd = "{} -D {} start".format(self.pg_ctl, self.pgdata)
            stdin, stdout, stderr = client.exec_command(_cmd, get_pty=True)
            if (
                self._stderr(stderr, "Error: '{}' returns error.".format(str(_cmd)))
                == False
            ):
                sys.exit(1)
            print("ok.")

        client.close()

        print("Server Check finished.")

        return True, [
            _conn["max_connections"],
            _conn["reserved_connections"],
            _conn["superuser_reserved_connections"],
        ]


if __name__ == "__main__":

    REMOTE = True

    if REMOTE == True:
        host = "192.168.128.193"
    else:
        host = "localhost"

    user = "postgres"
    passwd = "xxx"

    if REMOTE == True:
        pg_ctl = "/usr/local/pgsql/bin/pg_ctl"
        pgdata = "/usr/local/pgsql/data"
        pgdata_backup = "/usr/local/pgsql/data.tgz"
    else:
        pg_ctl = "/usr/local/pgsql/bin/pg_ctl"
        pgdata = "/usr/local/pgsql/data"
        pgdata_backup = "/usr/local/pgsql/data_backup"

    pg = PG(
        host,
        pg_ctl,
        pgdata,
        pgdata_backup,
        server_user=user,
        server_passwd=passwd,
    )

    conf_params = [
        ["wal_buffers", "128MB"],
        ["bgwriter_delay", "300ms"],
        ["bgwriter_lru_maxpages", "100"],
        ["bgwriter_lru_multiplier", "2.0"],
        ["wal_writer_delay", "300ms"],
        ["checkpoint_timeout", "10min"],
        ["checkpoint_completion_target", "0.8"],
        ["max_wal_size", "1GB"],
    ]

    pg.check()
    # pg.stop()
    # pg.set_conf(conf_params)
    # pg.start()
    # pg.restart()
    # pg.reload()
