"""
base_conf.py

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

import getpass, time, sys, os
from utils import Common, Log, PG, Repository
from benchmark import Sysbench, SysbenchScenario, Pgbench, PgbenchScenario

try:
    import tomllib
except:
    from pip._vendor import tomli as tomllib
from pprint import pprint


def check_template(check_func):
    def wrapper(self, *args, **kwargs):
        pg = self.create_pg()
        ret, [
            max_connections,
            reserved_connections,
            superuser_reserved_connections,
        ] = pg.check(self.restore_everytime, self.linux_monitoring)
        if ret == False:
            sys.exit(1)
        time.sleep(5)  # Waiting for PostgreSQL to start up.

        check_func(self)

        del pg
        return [max_connections, reserved_connections, superuser_reserved_connections]

    return wrapper


class BaseConf:
    def __init__(self, conf_file):

        self.target = None
        self.n_trials = 10
        # ["TPE" |  "Random" | "Grid" | "CmaEs" | "QMC" | "GP" ]
        # https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
        self.sampling_mode = Common.DEFAULT_SAMPLING_MODE
        self.restore_everytime = True

        self.linux_monitoring = False
        self.monitoring_time = 10

        self.base_dir = Common.set_dir(Common.REPOSITORY_DIR)
        self.log_dir = None

        self.pgsql_server = {}

        self.config_real = []
        self.config_int = []

        self.bench_conf = {}
        self.bench_scenario = []

        self.additional_monitor_items = []

        ## --------------------------------------------
        ## Parse configure toml file
        ## --------------------------------------------
        filename = os.path.basename(conf_file)
        filename, _ = os.path.splitext(filename)
        self.repository = filename
        self.log_dir = Common.set_dir(filename)

        with open(conf_file, mode="rb") as f:
            try:
                data = tomllib.load(f)
                # pprint(data)
                # print(data)

                # ------------------------
                # trial
                # ------------------------
                trial = data["trial"]
                if trial == None:
                    print("Error: '{}' section not found.".format("trial"))
                    sys.exit(1)

                if "target" in trial:
                    self.target = trial["target"]
                    if self.target not in ["sysbench", "pgbench"]:
                        print("Error: '{}' not supported.".format(self.target))
                        sys.exit(1)
                else:
                    print("Error: 'target' key not found.")
                    sys.exit(1)

                if "n_trials" in trial:
                    self.n_trials = trial["n_trials"]
                else:
                    self.n_trials = 10

                if "sampling_mode" in trial:
                    self.sampling_mode = trial["sampling_mode"]

                if "restore_everytime" in trial:
                    self.restore_everytime = trial["restore_everytime"]
                else:
                    self.restore_everytime = True

                # ------------------------
                # monitoring
                # ------------------------
                monitoring = data["monitoring"]
                if monitoring == None:
                    print("Error: '{}' section not found.".format("monitoring"))
                    sys.exit(1)

                if "linux_monitoring" in monitoring:
                    self.linux_monitoring = monitoring["linux_monitoring"]
                else:
                    self.linux_monitoring = False

                if "monitoring_time" in monitoring:
                    self.monitoring_time = monitoring["monitoring_time"]
                else:
                    self.monitoring_time = 10

                # ------------------------
                # postgresql_server
                # ------------------------
                pgsql_server = data["postgresql_server"]
                if pgsql_server == None:
                    print("Error: '{}' section not found.".format("postgresql_server"))
                    sys.exit(1)

                keys = ["host", "hostuser", "port", "user", "db", "pg_ctl"]
                for key in keys:
                    if key in pgsql_server:
                        self.pgsql_server[key] = pgsql_server[key]
                    else:
                        print("Error: '{}' key not found in [postgresql_server] section.".format(key))
                        sys.exit(1)

                keys = ["pgdata", "pgdata_backup"]
                for key in keys:
                    if key in pgsql_server:
                        self.pgsql_server[key] = Common.set_dir(pgsql_server[key])
                    else:
                        print("Error: '{}' key not found in [postgresql_server] section.".format(key))
                        sys.exit(1)

                if "passwd" in pgsql_server:
                    self.pgsql_server["passwd"] = pgsql_server["passwd"]
                else:
                    self.pgsql_server["passwd"] = None

                # ------------------------
                # postgresql_conf
                # ------------------------
                pgsql_conf = data["postgresql_conf"]
                if pgsql_conf == None:
                    print("Error: '{}' section not found.".format("postgresql_conf"))
                    sys.exit(1)

                if "pg_config_int" in pgsql_conf:
                    self.config_int = pgsql_conf["pg_config_int"]
                else:
                    self.config_int = []

                if "pg_config_real" in pgsql_conf:
                    self.config_real = pgsql_conf["pg_config_real"]
                else:
                    self.config_real = []

                for item in self.config_int:
                    if len(item) != 4:
                        print("Error: item '{}' has {} items, but the list of pg_config_int requires 4 items.".format(item, len(item)))
                        sys.exit(1)
                    if type(item[0]) is not str:
                        print("Error: item[0] '{}' should be string in [pg_config_int].".format(item[0]))
                        sys.exit(1)
                    if type(item[1]) is not int:
                        print("Error: item[1] '{}' should be integer in [pg_config_int].".format(item[1]))
                        sys.exit(1)
                    if type(item[2]) is not int:
                        print("Error: item[2] '{}' should be integer in [pg_config_int].".format(item[2]))
                        sys.exit(1)
                    if type(item[3]) is not str:
                        print("Error: item[3] '{}' should be string or empty string in [pg_config_int].".format(item[3]))
                        sys.exit(1)

                for item in self.config_real:
                    if len(item) != 4:
                        print("Error: item '{}' has {} items, but the list of pg_config_real requires 4 items.".format(item, len(item)))
                        sys.exit(1)
                    if type(item[0]) is not str:
                        print("Error: item[0] '{}' should be string in [pg_config_real].".format(item[0]))
                        sys.exit(1)
                    if type(item[1]) is not float:
                        print("Error: item[1] '{}' should be float in [pg_config_real].".format(item[1]))
                        sys.exit(1)
                    if type(item[2]) is not float:
                        print("Error: item[2] '{}' should be float in [pg_config_real].".format(item[2]))
                        sys.exit(1)
                    if type(item[3]) is not str:
                        print("Error: item[3] '{}' should be string or empty string in [pg_config_real].".format(item[3]))
                        sys.exit(1)

                # ------------------------
                # benchmark
                # ------------------------
                benchmark = data["benchmark"]
                if benchmark == None:
                    print("Error: '{}' section not found.".format("benchmark"))
                    sys.exit(1)

                if self.target not in benchmark:
                    print("Error: '[benchmark.{}]' subsection not found in [benckmark] section.".format(self.target))
                    sys.exit(1)

                else:
                    target_benchmark = benchmark[self.target]

                if "host" in target_benchmark:
                    self.bench_conf["host"] = target_benchmark["host"]
                else:
                    self.bench_conf["host"] = "localhost"

                if "bindir" in target_benchmark:
                    self.bench_conf["bindir"] = Common.set_dir(target_benchmark["bindir"])
                else:
                    print("Error: 'bindir' key not found in [benchmark.{}] section.".format(self.target))
                    sys.exit(1)

                if self.target == "sysbench":
                    if "sb_table_size" in target_benchmark:
                        self.bench_conf["sb_table_size"] = target_benchmark["sb_table_size"]
                    else:
                        print("Error: 'sb_table_size' key not found in [benchmark.{}] section.".format(self.target))
                        sys.exit(1)

                    if "sb_tables" in target_benchmark:
                        self.bench_conf["sb_tables"] = target_benchmark["sb_tables"]
                    else:
                        print("Error: 'sb_tables' key not found in [benchmark.{}] section.".format(self.target))
                        sys.exit(1)

                elif self.target == "pgbench":
                    if "scale" in target_benchmark:
                        self.bench_conf["scale"] = target_benchmark["scale"]
                    else:
                        print("Error: 'scale' key not found in [benchmark.{}] section.".format(self.target))
                        sys.exit(1)

                else:
                    # never reached.
                    sys.exit(1)

                if "scenario" in target_benchmark:
                    self.bench_scenario = target_benchmark["scenario"]
                else:
                    print("Error: 'scenario' key not found in [benchmark.{}] section.".format(self.target))
                    sys.exit(1)

                if "additional_monitor_items" in target_benchmark:
                    _additional_monitor_items = target_benchmark["additional_monitor_items"]
                    for item in _additional_monitor_items:
                        self.additional_monitor_items.append(item)
                else:
                    self.additional_monitor_items = None

            except FileNotFoundError as err:
                print("Error: '{}' not found.".format(conf_file))
                sys.exit(1)

    """
    Public methods
    """

    def create_bench(self):
        if self.target == "sysbench":
            return Sysbench(
                self.pgsql_server["host"],
                self.pgsql_server["port"],
                self.pgsql_server["user"],
                self.pgsql_server["passwd"],
                self.pgsql_server["db"],
                self.bench_conf["sb_table_size"],
                self.bench_conf["sb_tables"],
                self.bench_conf["bindir"],
            )
        elif self.target == "pgbench":
            return Pgbench(
                self.pgsql_server["host"],
                self.pgsql_server["port"],
                self.pgsql_server["user"],
                self.pgsql_server["db"],
                self.bench_conf["scale"],
                self.bench_conf["bindir"],
            )
        else:
            print("Error: self.target:'{}' not allowed.".format(self.target))
            sys.exit(1)

    def create_bench_scenario(self):
        if self.target == "sysbench":
            return SysbenchScenario(
                self.pgsql_server["host"],
                self.pgsql_server["port"],
                self.pgsql_server["user"],
                self.pgsql_server["passwd"],
                self.pgsql_server["db"],
                self.bench_conf["bindir"],
            )
        elif self.target == "pgbench":
            return PgbenchScenario(
                self.pgsql_server["host"],
                self.pgsql_server["port"],
                self.pgsql_server["user"],
                self.pgsql_server["passwd"],
                self.pgsql_server["db"],
                self.bench_conf["bindir"],
            )
        else:
            print("Error: self.target:'{}' not allowed.".format(self.target))
            sys.exit(1)

    """
    # Analyzes benchmark configuration.
    """

    def check(self):
        if self.target == "sysbench":
            return self._sysbench_check(self)
        elif self.target == "pgbench":
            return self._pgbench_check(self)
        else:
            print("Error: self.target:'{}' not allowed.".format(self.target))
            sys.exit(1)

    @check_template
    def _sysbench_check(self):

        print("\nSysbench check start.")
        print("(1) Sysbench bindir:")
        _sysbench_path = self.bench_conf["bindir"] + "sysbench"
        if os.path.isfile(_sysbench_path) == False:
            print("Error: '{}' not found.".format(_sysbench_path))
            sys.exit(1)
        else:
            print("ok.")
        print("Sysbench check finished.\n")

        sysbench = self.create_bench()
        print("")
        num_sbtest, num_sbtest_row = sysbench.check()

        print("\nSysbench configuration check start.")

        print("(1) Sysbench configuration:")
        if self.bench_conf["sb_table_size"] > num_sbtest_row:
            print(
                "Error: 'bench_conf['sb_table_size']={}' must be less than or equal to {}".format(
                    str(self.bench_conf["sb_table_size"]), str(num_sbtest_row)
                )
            )
            sys.exit(1)

        if self.bench_conf["sb_tables"] > num_sbtest:
            print("Error: 'bench_conf['sb_tables']' must be less than or equal to {}".format(str(num_sbtest)))
            sys.exit(1)
        print("ok.")

        print("(2) Sysbench scenario:")
        for s in self.bench_scenario:
            # command
            if sysbench.command_type_check(s[3]) == False:
                print("Error: '{}' not supported in scenario['sb_command']".format(s[3]))
                sys.exit(1)

            # table_size
            if s[4] > num_sbtest_row:
                print("Error: 'scenario['table_size']' must be less than or equal to {}".format(str(num_sbtest_row)))
                sys.exit(1)

            # tables
            if s[5] > num_sbtest:
                print("Error: 'scenario['tables']' must be less than or equal to {}".format(str(num_sbtest)))
                sys.exit(1)
        print("ok.")

        print("Sysbench configuration check finished.")

        del sysbench

    @check_template
    def _pgbench_check(self):

        print("\npgbench check start.")
        print("(1) pgbench bindir:")
        _pgbench_path = self.bench_conf["bindir"] + "pgbench"
        if os.path.isfile(_pgbench_path) == False:
            print("Error: '{}' not found.".format(_pgbench_path))
            sys.exit(1)
        else:
            print("ok.")
        print("pgbench check finished.\n")

        pgbench = self.create_bench()
        print("")
        num_pgbench_accounts = pgbench.check()

        print("\npgbench configuration check start.")

        print("(1) pgbench configuration:")
        if self.bench_conf["scale"] * 100000 > num_pgbench_accounts:
            print(
                "Error: 'pgbench_conf['scale']={}' must be less than or equal to {}".format(
                    str(self.bench_conf["scale"]),
                    str(int(num_pgbench_accounts / 100000)),
                )
            )
            sys.exit(1)
        print("ok.")

        print("pgbench configuration check finished.")

        del pgbench
