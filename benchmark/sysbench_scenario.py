"""
sysbench_scenario.py

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

import queue
import threading
import time, sys

from .sysbench import Sysbench
from .scenario import Scenario

sys.path.append("..")
from utils import Common, Log, Monitor


class SysbenchScenario(Sysbench, Scenario):
    def __init__(
        self,
        host,
        port,
        user,
        password,
        db,
        sysbench_bindir,
    ):

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.sysbench_bindir = Common.set_dir(sysbench_bindir)


    """
    Public methods
    """

    """
    #  Analyzes the scenario and returns the following metrics:
    #     total_duration, required_max_connections, total_connections.
    """

    @Scenario.check_scenario_template
    def check_scenario(self, sc):
        if len(sc) != 6:
            print("Format Error: {}".format(sc))
            sys.exit(1)
        if type(sc[0]) is not int or sc[0] < 0:
            print("Value Error: wait must be positive integer:{}".format(sc))
            sys.exit(1)
        if type(sc[1]) is not int or sc[1] < 0:
            print("Value Error: threads must be positive integer:{}".format(sc))
            sys.exit(1)
        if type(sc[2]) is not int or sc[2] < 0:
            print("Value Error: duration must be positive integer:{}".format(sc))
            sys.exit(1)
        if type(sc[3]) is not str:
            print("Value Error: command must be string:{}".format(sc))
            sys.exit(1)
        if type(sc[4]) is not int or sc[4] < 0:
            print("Value Error: table_size must be positive integer:{}".format(sc))
            sys.exit(1)
        if type(sc[5]) is not int or sc[5] < 0:
            print("Value Error: tables must be positive integer:{}".format(sc))
            sys.exit(1)

    """
    # Score function
    #
    # Note: Based on the data obtained, an appropriate score can be set.
    #       This function returns total number of executed transactions.
    """

    def score(self, msg_list):
        _score = 0
        for item in msg_list:
            # sc_no = item[0]
            sc_param = item[1]
            sc_result = item[2]

            sc_threads = int(sc_param[1])
            sc_duration = int(sc_param[2])

            sc_ret_total = int(sc_result[3])
            sc_ret_transaction = int(sc_result[4])
            sc_ret_queries = int(sc_result[5])

            # Note: Based on the data obtained, an appropriate score can be set.
            _score += sc_ret_transaction

        return _score

    """
    # Runs one of the scnenario and returns result.
    # This is invoked in the play()@scenario.py
    """

    def bench(self, no, queue, sc):
        [wait, threads, duration, command, table_size, tables] = sc

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: sysbench thread[{}] created.".format(no))

        if int(wait) > 0:
            time.sleep(int(wait))

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: sysbench thread[{}] started.".format(no))

        sb = Sysbench(
            self.host,
            self.port,
            self.user,
            self.password,
            self.db,
            table_size,
            tables,
            self.sysbench_bindir,
        )
        ret = sb.run(int(threads), int(duration), str(command))

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: sysbench thread[{}] terminated.".format(no))

        del sb
        queue.put([no, sc, ret])
