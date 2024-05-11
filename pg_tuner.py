#!/usr/bin/env python3
"""
pg_tuner.py

Usage:
 pg_tuner.py show --conf conf.toml
 pg_tuner.py check --conf conf.toml
 pg_tuner.py run --conf conf.toml
 pg_tuner.py create --conf conf.toml
 pg_tuner.py drop --conf conf.toml
 pg_tuner.py backup --conf conf.toml
 pg_tuner.py analyze --db PATH/study.db

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

import argparse
import time, sys, csv, os
import optuna

from utils import Common, Log, PG, Repository
from conf import Conf
from benchmark import Sysbench, SysbenchScenario
from benchmark import Pgbench, PgbenchScenario

try:
    import sqlite3
except:
    pass


class PgTuner:
    def __init__(self):
        self.conf = None
        self.pg = None
        self.sc = None
        self.repo = None

        self.max_connections = None

    def _objective(self, trial):
        conf_params = self.conf.extract_params_from(trial)

        # 0. restore database cluster
        if self.conf.restore_everytime:
            self.pg.restore_backup()

        # 1. set conf
        if self.pg.set_conf(conf_params, self.max_connections) != True:
            sys.exit(1)

        # 2. pg start
        self.pg.start()
        time.sleep(5) # Wait until Postgres is operational.

        # 3. benchmark run
        _log_dir = self.repo.get_log_dir(trial.number)

        cmd = "mv {} {}".format(Common.ADDITIONAL_CONF, _log_dir)
        self.pg.exec_local(cmd)

        score, ret = self.sc.play(
            self.conf.bench_scenario,
            _log_dir,
            self.conf.monitoring_time,
            self.conf.linux_monitoring,
            self.conf.additional_monitor_items,
        )

        ret_file = "{}{}".format(_log_dir, Common.RESULT_FILE)
        with open(ret_file, "w") as f:
            writer = csv.writer(f, quotechar="'", quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(["no"] + self.sc.get_col_name())
            for [no, scenario, result] in ret:
                writer.writerow([no] + result)

        score_file = "{}{}".format(_log_dir, Common.SCORE_FILE)
        with open(score_file, "w") as f:
            f.write(str(score) + "\n")

        # 4. pg stop
        self.pg.stop()

        return float(score)

    def _confirm_duration(self, duration, n_trials, show_only=False):
        estimated_time = duration * n_trials
        if estimated_time > 10 * 60:  # over 10 [min]
            estimated_time, unit = Common.pretty_time_format(estimated_time)

            print(
                "Estimated Time: This task is estimated to take approximately {:.1f} {} to complete.".format(
                    estimated_time, unit
                )
            )
            if show_only == True:
                return True

            print("Confirmation: Do you want to proceed with this task?")
            while True:
                answer = input("Enter yes or no: ").lower()
                if answer in ("yes"):
                    return True
                else:
                    return False

    """
    # Checks the max connections
    """

    def _check_max_connections(self, connections, required_max_connections):
        [
            max_connections,
            reserved_connections,
            superuser_reserved_connections,
        ] = connections

        if required_max_connections <= (
            max_connections - reserved_connections - superuser_reserved_connections
        ):
            return True
        else:
            new_max_connections = (
                required_max_connections
                + reserved_connections
                + superuser_reserved_connections
                + 2
            )  # 1 is for monitoring, and another is margin.
            print(
                "Error: Although max_connections is set to {}, your scenario requires {} connections maximum.".format(
                    max_connections, new_max_connections
                )
            )
            print(
                "Hint: Consider adjusting the number of threads in your scenario to stay within the connection limit."
            )
            return False

    def _check_conf_file(self, args):
        conf_file = args.conf
        if os.path.isfile(conf_file) == False:
            print("Error: configuration file '{}' not found".format(conf_file))
            sys.exit(1)
        return conf_file


    """
    Public methods
    """

    """
    # show command:
    """

    def show(self):
        conf_file = self._check_conf_file(args)

        self.conf = Conf(conf_file)
        self.sc = self.conf.create_bench_scenario()

        (
            total_duration,
            required_max_connections,
            total_connections,
        ) = self.sc.check_scenario(self.conf.get_scenario())

        self.conf.print_conf(
            total_duration, required_max_connections, total_connections
        )

        del self.conf, self.sc

    """
    # check command:
    """

    def check(self):
        conf_file = self._check_conf_file(args)

        self.conf = Conf(conf_file)
        self.conf.input_server_passwd()

        self.pg = self.conf.create_pg()
        self.sc = self.conf.create_bench_scenario()

        [
            max_connections,
            reserved_connections,
            superuser_reserved_connections,
        ] = self.conf.check()

        (
            total_duration,
            required_max_connections,
            total_connections,
        ) = self.sc.check_scenario(self.conf.get_scenario())
        self._confirm_duration(total_duration, self.conf.n_trials, show_only=True)

        self.conf.print_connection_info(required_max_connections, total_connections)

        del self.conf, self.pg, self.sc

    """
    # create command:
    """

    def create(self):
        conf_file = self._check_conf_file(args)

        self.conf = Conf(conf_file)
        self.sb = self.conf.create_bench()

        self.sb.create_bench()
        if self.conf.restore_everytime:
            print("Notice: *** Create a backup using the 'pg_tuner.py backup' command before running the task. ***")
        del self.sb, self.conf

    """
    # drop command:
    """

    def drop(self):
        conf_file = self._check_conf_file(args)

        self.conf = Conf(conf_file)
        self.sb = self.conf.create_bench()

        print("Confirmation: Do you want to drop benchmark tables?")
        answer = input("Enter yes or no: ").lower()
        if answer in ("yes"):
            self.sb.drop_bench()
        del self.sb, self.conf

    """
    # backup command:
    """
    def backup(self):
        conf_file = self._check_conf_file(args)

        self.conf = Conf(conf_file)

        if self.conf.restore_everytime == False:
            print("Error: parameter 'restore_everytime' is  False.")
            sys.exit(1)

        self.conf.input_server_passwd()
        self.pg = self.conf.create_pg()

        # Gets pg_ctl status
        pg_status = self.pg.is_running()

        # Stops PostgreSQL server if running.
        if pg_status == True:
            self.pg.stop()

        # pg.make_backup
        self.pg.make_backup()

        # Restart if pg_status == True
        if pg_status == True:
            self.pg.start()


    """
    # run command:
    """

    def run(self):
        conf_file = self._check_conf_file(args)

        self.conf = Conf(conf_file)

        # Check repository
        self.repo = self.conf.create_repository()

        if self.repo.check_repo() == False:
            sys.exit(0)

        #
        self.conf.input_server_passwd()

        self.pg = self.conf.create_pg()
        self.sc = self.conf.create_bench_scenario()

        # check
        [
            max_connections,
            reserved_connections,
            superuser_reserved_connections,
        ] = self.conf.check()

        (
            total_duration,
            required_max_connections,
            total_connections,
        ) = self.sc.check_scenario(self.conf.get_scenario())

        # Confirm duration
        if self._confirm_duration(total_duration, self.conf.n_trials) == False:
            del self.sc, self.pg, self.conf
            sys.exit(0)

        # Check max_connection
        if (
            self._check_max_connections(
                [max_connections, reserved_connections, superuser_reserved_connections],
                required_max_connections,
            )
            == False
        ):
            del self.sc, self.pg, self.conf
            sys.exit(0)

        self.conf.print_conf(total_duration, required_max_connections, total_connections)
        self.conf.dump_conf()

        # Cold start
        self.pg.stop()

        # Optimize parameters
        sampler = self.conf.get_sampler()

        if "sqlite3" in sys.modules:
            storage = "sqlite:///{}{}{}".format(
                self.conf.base_dir, self.conf.log_dir, Common.STUDY_DB
            )
            study = optuna.create_study(
                direction="maximize", study_name=self.conf.log_dir, storage=storage, sampler=sampler,
            )
        else:
            study = optuna.create_study(direction="maximize", sampler=sampler)
        study.optimize(self._objective, n_trials=self.conf.n_trials)

        # Store result
        self.conf.dump_best_result(study.best_value, study.best_params, study.best_trial, study.best_trials)
        print("Best objective value: {}".format(study.best_value))
        print("Best parameter: {}".format(study.best_params))

        #
        self.pg.start()

        del self.conf, self.pg, self.sc, self.repo

    """
    # restart command:
    """

    def restart(self):
        if "sqlite3" not in sys.modules:
            print("Error: sqlite3 module not found.")
            sys.exit(1)

        conf_file = args.conf
        if os.path.isfile(conf_file) == False:
            print("Error: configuration file '{}' not found".format(conf_file))
            sys.exit(1)

        # How to restart pg_tuner.py
        #
        # (1) Get latest trial_id from  trials in study.db.
        #
        # sqlite> SELECT max(number) FROM trials WHERE state = 'RUNNING' OR state = 'FAIL';
        # 42    (e.g.  max_number := 42)
        #
        # (2) Delete latest trial data.
        #
        # sqlite> DELETE FROM trials WHERE number >= max_number;
        # sqlite> DELETE FROM trial_values WHERE trial_id > max_number;
        # sqlite> DELETE FROM trial_params WHERE trial_id > max_number;
        #
        # (3) Remove latest trial data directory.
        #
        # $ rm -rf data_repo/self.conf.log_dir/00XX  (e.g. 00XX = max_number.zfill(4))
        #
        # (4) Set remaining number of trails
        #
        # study.optimize(self._objective, n_trials=(self.conf.n_trials - max_number - 1))

        self.conf = Conf(conf_file)
        self.repo = self.conf.create_repository()

        self.conf.input_server_passwd()

        self.pg = self.conf.create_pg()
        self.sc = self.conf.create_bench_scenario()

        # check
        [
            max_connections,
            reserved_connections,
            superuser_reserved_connections,
        ] = self.conf.check()

        (
            total_duration,
            required_max_connections,
            total_connections,
        ) = self.sc.check_scenario(self.conf.get_scenario())

        # Cold start
        self.pg.stop()

        # Optimize parameters
        sampler = self.conf.get_sampler()
        storage = "sqlite:///{}{}{}".format(self.conf.base_dir, self.conf.log_dir, Common.STUDY_DB)
        study = optuna.load_study(storage=storage, study_name=self.conf.log_dir, sampler=sampler)

        # Set remaining number of trails
        study.optimize(self._objective, n_trials=(self.conf.n_trials - 42))

        # Store result
        self.conf.dump_best_result(study.best_value, study.best_params, study.best_trial, study.best_trials)
        print("Best objective value: {}".format(study.best_value))
        print("Best parameter: {}".format(study.best_params))

        #
        self.pg.start()

        del self.conf, self.pg, self.sc, self.repo


#
# Creates the script "important_params.py" that executes optuna.visualization.plot_param_importances()
# to visualize the importance of configuration parameters using the specified study.db.
#
# Reference: link to optuna.visualization.plot_param_importances:
# https://optuna.readthedocs.io/en/stable/reference/visualization/generated/optuna.visualization.plot_param_importances.html
#
def analyze_study_db(atgs):

    if "sqlite3" not in sys.modules:
        print("Error: analyze command requires 'sqlite3' module, however, this script did not import it.")
        sys.exit(1)

    db = args.db
    if os.path.isfile(db) == False:
        print("Error: study db '{}' not found".format(db))
        sys.exit(1)

    filename = Common.DEFAULT_IMPORTANT_PARAMS_FILE

    con = sqlite3.connect(db)
    cur = con.cursor()
    res = cur.execute("SELECT study_name FROM studies")
    study_name = res.fetchone()

    res = cur.execute("SELECT param_name FROM trial_params WHERE trial_id = 1")
    param_name = res.fetchall()

    with open(filename, "w") as f:
        print("import optuna\n", file=f)
        print(
            'study = optuna.load_study(storage="sqlite:///{}", study_name="{}")'.format(
                db, study_name[0]
            ),
            file=f,
        )

        print("\nret = optuna.importance.get_param_importances(study=study,params=[", file=f)
        for key in param_name:
            print('\t"{}",'.format(key[0]), file=f)
        print("])", file=f)
        print("print(ret)\n", file=f)

        print("\noptuna.visualization.plot_param_importances(study=study,params=[", file=f)
        for key in param_name:
            print('\t"{}",'.format(key[0]), file=f)
        print("]).show()", file=f)

    print("Created: '{}'.".format(filename))


if __name__ == "__main__":

    def show(args):
        pgt = PgTuner()
        pgt.show()
        del pgt

    def check(args):
        pgt = PgTuner()
        pgt.check()
        del pgt

    def run(args):
        pgt = PgTuner()
        pgt.run()
        del pgt

    # Hidden command
    def restart(args):
        pgt = PgTuner()
        pgt.restart()
        del pgt

    def create(args):
        pgt = PgTuner()
        pgt.create()
        del pgt

    def drop(args):
        pgt = PgTuner()
        pgt.drop()
        del pgt

    def backup(args):
        pgt = PgTuner()
        pgt.backup()
        del pgt

    # Create command parser.
    parser = argparse.ArgumentParser(
        description="This is another automated PostgreSQL database tuning tool."
    )
    subparsers = parser.add_subparsers()

    # show command.
    parser_show = subparsers.add_parser("show", help="show configuration")
    parser_show.add_argument("--conf", nargs="?")
    parser_show.set_defaults(handler=show)

    # check command.
    parser_check = subparsers.add_parser("check", help="check configuration")
    parser_check.add_argument("--conf", nargs="?")
    parser_check.set_defaults(handler=check)

    # run command.
    parser_run = subparsers.add_parser("run", help="run")
    parser_run.add_argument("--conf", nargs="?")
    parser_run.set_defaults(handler=run)

    """
    # Hidden command
    # restart command.
    parser_restart = subparsers.add_parser("restart", help="restart study")
    parser_restart.add_argument("--conf", nargs="?")
    parser_restart.set_defaults(handler=restart)
    """

    # create benchmark.
    parser_create = subparsers.add_parser("create", help="create benchmark")
    parser_create.add_argument("--conf", nargs="?")
    parser_create.set_defaults(handler=create)

    # drop benchmark.
    parser_drop = subparsers.add_parser("drop", help="drop benchmark")
    parser_drop.add_argument("--conf", nargs="?")
    parser_drop.set_defaults(handler=drop)

    # backup data cluster.
    parser_backup = subparsers.add_parser("backup", help="backup data cluster")
    parser_backup.add_argument("--conf", nargs="?")
    parser_backup.set_defaults(handler=backup)

    # analyze study.db.
    parser_analyze = subparsers.add_parser("analyze", help="analyze study.db")
    parser_analyze.add_argument(
        "--db",
        nargs="?",
        default="./study.db",
        help='Analyze the specified study.db and create the script "important_params.py" that visualizes the importance of configuration parameters',
    )
    parser_analyze.set_defaults(handler=analyze_study_db)

    # Main procedure.
    args = parser.parse_args()
    if hasattr(args, "handler"):
        args.handler(args)
    else:
        parser.print_help()
