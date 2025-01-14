"""
conf.py

  Copyright (c) 2024-2025, Hironobu Suzuki @ interdb.jp
"""

import optuna
import getpass, time, sys
from utils import Common, Log, PG, Repository
from benchmark import Sysbench, SysbenchScenario, Pgbench, PgbenchScenario
from base_conf import BaseConf


class Conf(BaseConf):

    def __init__(self, conf_file):
        super().__init__(conf_file)

    """
    Public methods
    """

    """
    # Requires the postgresql server's password
    """

    def input_server_passwd(self):
        def pg_passwd():
            print("Enter postgresql passwd:")
            _passwd = getpass.getpass()
            if len(_passwd) == 0:
                _passwd = None
            self.pgsql_server["passwd"] = _passwd

        host = self.pgsql_server["host"]
        if host == "localhost" or host == "127.0.0.1":
            self.pgsql_server["hostpasswd"] = None
            return

        print("Enter server passwd:")
        _passwd = getpass.getpass()
        self.pgsql_server["hostpasswd"] = _passwd

        if "passwd" in self.pgsql_server:
            if self.pgsql_server["passwd"] != "None":
                pg_passwd()
        else:
            pg_passwd()


    """
    # Returns a scenario.
    """

    def get_scenario(self):
        return self.bench_scenario

    """
    # Writes the file contains best_value, best_params, best_trial and best_trials.
    """

    def dump_best_result(self, best_value, best_params, best_trial, best_trials):
        def write_dict(conf, conf_name):
            dic = conf.keys()
            f.write("\n{} = {{\n".format(str(conf_name)))
            for key in conf:
                f.write("\t")
                f.write("'{}': '{}'".format(key, conf[key]))
                f.write(",\n")

            f.write("}\n")

        if self.log_dir == None:
            return

        filename = self.base_dir + self.log_dir + Common.BEST_RESULT_FILE
        with open(filename, mode="w") as f:
            f.write("best_value={}\n".format(str(best_value)))
            write_dict(best_params, "best_params")
            f.write("The best trial in the study => {}\n".format(best_trial))
            f.write("Trials located at the Pareto front in the study => {}\n".format(best_trials))

    """
    # Writes the file contains the trials configuration.
    """

    def dump_conf(self):
        def write_dict(conf):
            dic = conf.keys()
            for key in conf:
                if "passwd" in key or "password" in key:
                    continue
                if isinstance(conf[key], int):
                    f.write("{} = {}\n".format(key, conf[key]))
                else:
                    f.write("{} = \"{}\"\n".format(key, conf[key]))

            f.write("\n")

        def write_list(conf, conf_name):
            if conf == "None" or conf == None:
                return
            f.write("\n{} = [\n".format(str(conf_name)))
            for l in conf:
                f.write("\t[")
                for s in l:
                    if isinstance(s, int) or isinstance(s, float):
                        f.write("{}, ".format(s))
                    else:
                        f.write("\"{}\", ".format(s))

                f.write("],\n")

            f.write("]\n")


        def write_title(title, section):
            f.write("\n#--------------------------------------------\n")
            f.write("# {}\n".format(str(title)))
            f.write("#--------------------------------------------\n")
            f.write("[{}]\n".format(section))

        def write_item(item, itemname, quote=False):
            if quote == True:
                f.write("{} = \"{}\"\n".format(itemname, str(item)))
            else:
                f.write("{} = {}\n".format(itemname, str(item)))

        if self.log_dir == None:
            return

        filename = self.base_dir + self.log_dir + Common.CONF_FILE

        with open(filename, mode="w") as f:

            write_title("Trial configuration section", "trial")
            write_item(self.target, "target", True)
            write_item(self.n_trials, "n_trials")
            write_item(self.sampling_mode, "sampling_mode", True)
            write_item(self.restore_everytime, "restore_everytime", True)

            write_title("Monitoring section", "monitoring")
            write_item(self.linux_monitoring, "linux_monitoring", True)
            write_item(self.monitoring_time, "monitoring_time")

            write_title("PostgreSQL server configuration section", "postgresql_server")
            write_dict(self.pgsql_server)

            write_title("PostgreSQL configuration parameters section", "postgresql_conf")
            write_list(self.config_int, "config_int")
            write_list(self.config_real, "config_real")

            write_title("Benchmark section", "benchmark")
            write_title("benchmark configuration", "benchmark.{}".format(self.target))
            write_dict(self.bench_conf)
            write_list(self.bench_scenario, "scenario")
            if self.additional_monitor_items is not None:
                write_list(self.additional_monitor_items, "additional_monitor_items")

    """
    # Prints connection information
    """

    def print_connection_info(self, required_max_connections, total_connections):
        if required_max_connections != None:
            print("\nRequired max connections = {}".format(required_max_connections))
        if total_connections != None:
            print("\nTotal number of connections per trial = {}".format(total_connections))
            print("Total number of connections           = {}".format(total_connections * self.n_trials))
        print("")

    """
    # Prints configuration information
    """

    def print_conf(self, duration, required_max_connections=None, total_connections=None):
        def print_dict(conf, conf_name):
            dic = conf.keys()
            print("{} = {{".format(str(conf_name)))
            for key in conf:
                print("\t", end="")
                print("'{}': '{}'".format(key, conf[key]), end="")
                print(",")
            print("}\n")

        def print_list(conf, conf_name):
            if conf == "None" or conf == None:
                return
            print("{} = [".format(str(conf_name)))
            for l in conf:
                if l[0] in Common.IGNORE_PARAMS:
                    continue
                print("\t[", end="")
                print(", ".join(map(str, l)), end="")
                print("],")
            print("]")

        def print_title(title):
            print("\n#--------------------------------------------")
            print("# {}".format(str(title)))
            print("#--------------------------------------------")

        print_title("Repository")
        print("base_dir = {}".format(self.base_dir))
        print("log_dir  = {}{}".format(self.base_dir, self.log_dir))

        print_title("Trials")
        print("n_trials = {}".format(self.n_trials))
        print("duration per trial = {} [sec]".format(duration))
        estimated_duration = duration * self.n_trials
        estimated_duration, unit = Common.pretty_time_format(estimated_duration)
        print("Estimated total duration = {:.1f} {}".format(estimated_duration, unit))

        print_title("Monitoring")
        print("linux_monitoring = {}".format(str(self.linux_monitoring)))
        print("sampling period = {} [sec]".format(self.monitoring_time))

        print_title("PostgreSQL server configuration")
        print("host          = '{}'".format(self.pgsql_server["host"]))
        print("hostuser      = '{}'".format(self.pgsql_server["hostuser"]))
        print("port          = {}".format(self.pgsql_server["port"]))
        print("user          = '{}'".format(self.pgsql_server["user"]))
        print("db            = '{}'".format(self.pgsql_server["db"]))
        print("pg_ctl        = '{}'".format(self.pgsql_server["pg_ctl"]))
        print("pgdata        = '{}'".format(self.pgsql_server["pgdata"]))
        print("pgdata_backup = '{}'".format(self.pgsql_server["pgdata_backup"]))

        print_title("PostgreSQL configuration parameters")
        print_list(self.config_int, "config_int")
        print_list(self.config_real, "config_real")

        print_title("benchmark configuration")
        print_list(self.bench_scenario, "scenario")
        if self.additional_monitor_items is not None:
            print_list(self.additional_monitor_items, "additional_monitor_items")
        self.print_connection_info(required_max_connections, total_connections)

    """
    # Creates PG instance
    """

    def create_pg(self):
        return PG(
            self.pgsql_server["host"],
            self.pgsql_server["pg_ctl"],
            self.pgsql_server["pgdata"],
            self.pgsql_server["pgdata_backup"],
            self.pgsql_server["hostuser"],
            # Note: "hostpasswd" should be entered using input_server_passwd().
            self.pgsql_server["hostpasswd"],
        )

    """
    # Creates Repository instance
    """

    def create_repository(self):
        return Repository(
            self.base_dir,
            self.log_dir,
        )

    """
    # Extracts the params from trial.
    """

    def extract_params_from(self, trial):
        conf_params = []

        if self.config_int != None:
            for i in range(len(self.config_int)):
                p = self.config_int[i]
                if p[0] in Common.IGNORE_PARAMS:
                    continue
                v = trial.suggest_int(p[0], p[1], p[2])
                if p[3] == "":
                    conf_params.append([str(p[0]), str(v)])
                else:
                    conf_params.append([str(p[0]), (str(v) + str(p[3]))])

        if self.config_real != None:
            for i in range(len(self.config_real)):
                p = self.config_real[i]
                v = trial.suggest_float(p[0], p[1], p[2])
                if p[3] == "":
                    conf_params.append([str(p[0]), str(v)])
                else:
                    conf_params.append([str(p[0]), (str(v) + str(p[3]))])

        return conf_params

    """
    # Get sampler
    """
    def get_sampler(self):
        if self.sampling_mode == 'TPE':
            sampler = optuna.samplers.TPESampler()
        elif self.sampling_mode == 'Random':
            sampler = optuna.samplers.RandomSampler()
        elif self.sampling_mode == 'Grid':
            sampler = optuna.samplers.GridSampler()
        elif self.sampling_mode == 'CmaEs':
            sampler = optuna.samplers.CmaEsSampler()
        elif self.sampling_mode == 'QMC':
            sampler = optuna.samplers.QMCSampler()
        elif self.sampling_mode == 'GP':
            sampler = optuna.samplers.GPSampler()
        else:
            print("Error: sampler mode '{}' not supported.".format(self.sampling_mode))
            sys.exit(1)
        return sampler
