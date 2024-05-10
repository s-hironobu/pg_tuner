"""
pgbench_scenario.py

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

import queue
import threading
import time, sys

from .pgbench import Pgbench
from .scenario import Scenario

sys.path.append("..")
from utils import Common, Log, Monitor


class PgbenchScenario(Pgbench, Scenario):
    def __init__(
        self,
        host,
        port,
        user,
        password,
        db,
        pgbench_bindir,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.pgbench_bindir = Common.set_dir(pgbench_bindir)


    """
    Public methods
    """

    """
    #  Analyzes the scenario and returns the following metrics:
    #     total_duration, required_max_connections, total_connections.
    """

    @Scenario.check_scenario_template
    def check_scenario(self, sc):
        if len(sc) != 4:
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
        if type(sc[3]) is not int or sc[3] < 0:
            print("Value Error: pgbench_scale must be positive integer:{}".format(sc))
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

            sc_ret_transactions = int(sc_result[0])
            sc_ret_latency = float(sc_result[1])
            sc_ret_connection_time = float(sc_result[2])
            sc_ret_tps = float(sc_result[3])

            _score += sc_ret_transactions

        return _score

    """
    # Runs one of the scnenario and returns result.
    # This is invoked in the play()@scenario.py
    """

    def bench(self, no, queue, sc):
        [wait, threads, duration, scale] = sc

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: sysbench thread[{}] created.".format(no))

        if int(wait) > 0:
            time.sleep(int(wait))

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: sysbench thread[{}] started.".format(no))

        pb = Pgbench(
            self.host,
            self.port,
            self.user,
            self.db,
            scale,
            self.pgbench_bindir,
        )
        ret = pb.run(int(threads), int(duration), int(scale))

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: sysbench thread[{}] terminated.".format(no))

        del pb
        queue.put([no, sc, ret])
