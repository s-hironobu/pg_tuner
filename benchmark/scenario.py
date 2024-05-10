"""
scenario.py

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

import multiprocessing as mp
import time, sys

sys.path.append("..")
from utils import Common, Log, Monitor


class Scenario:
    def __init__(
        self,
        host,
        port,
        user,
        password,
        db,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db

    """
    Public methods
    """

    """
    # decoration function for check_scenario
    """

    def check_scenario_template(check_scenario):
        def wrapper(self, args, **kwargs):
            scenario = args
            total_duration = 0
            total_connections = 0

            # Check parameters
            for sc in scenario:
                check_scenario(self, sc)

                tmp_duration = sc[0] + sc[2]
                if tmp_duration > total_duration:
                    total_duration = tmp_duration
                total_connections += sc[1]

            # Compute required_max_connections
            required_max_connections = Common.compute_max_connections(
                ([scenario[0:3] for scenario in scenario])
            )

            return total_duration, required_max_connections, total_connections

        return wrapper

    """
    # Monitoring function.
    #
    # This function runs on the monitor process.
    # For each monitoring interval (`monitoring_time` in seconds),
    # it retrieves PostgreSQL server statistics and saves the results.
    # When it receives a message via `_queue_mon`, it terminates monitoring.
    """

    def monitor(
        self,
        host,
        port,
        user,
        db,
        password,
        log_dir,
        monitoring_time,
        linux_monitoring,
        additional_monitor_items,
        _queue_mon,
    ):

        # TODO: Need retry feature.
        mon = Monitor(
            host,
            port,
            user,
            db,
            password,
            log_dir,
            linux_monitoring,
            additional_monitor_items,
        )
        if mon.start() == False:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: Monitor process did not establish connection.")
            del mon
            sys.exit(1)

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: monitor process created.")

        while True:
            time.sleep(monitoring_time)
            if _queue_mon.empty() == False:
                if Log.info <= Common.DEFAULT_LOG_LEVEL:
                    print('Info: monitor process terminated by "stop" message.')
                break
            mon.monitoring()
            if Log.info <= Common.DEFAULT_LOG_LEVEL:
                print("Info: monitor process retrieves the statistics.")

        mon.stop

    """
    # Runs scenario-specific benchmarks and launches monitoring as needed.
    """

    def play(
        self,
        scenario,
        log_dir=None,
        monitoring_time=None,
        linux_monitoring=False,
        additional_monitor_items=None,
    ):
        total_duration, _, _ = self.check_scenario(scenario)
        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: total_duration = {}[sec]".format(total_duration))

        # Don't set: `mp.set_start_method("spawn")`
        _queue = mp.Queue()

        # Create and Start benchmark threads.
        no = 0
        process_list = []
        for sc in scenario:
            process = mp.Process(name=str(no), target=self.bench, args=(no, _queue, sc), daemon=True)
            process.start()
            no += 1
            process_list.append(process)

        msg_list = []

        # Create and Start monitor process
        if log_dir != None:
            _queue_mon = mp.Queue()

            process_mon = mp.Process(
                target=self.monitor,
                args=(
                    self.host,
                    self.port,
                    self.user,
                    self.db,
                    self.password,
                    log_dir,
                    monitoring_time,
                    linux_monitoring,
                    additional_monitor_items,
                    _queue_mon,
                ),
                daemon=True,
            )
            process_mon.start()

        # Join processes
        for ps in process_list:
            ps.join(timeout=total_duration + Common.TIMEOUT_MARGIN)

        # benchmark (sysbench or pgbench) processes are blocking this process ....

        # Stop monitor process
        if log_dir != None:
            _queue_mon.put("stop")
            del _queue_mon

        # Check message queue
        while _queue.empty() == False:
            val = _queue.get()
            msg_list.append(val)

        for ps in process_list:
            ps.terminate()

        if log_dir != None:
            process_mon.terminate()

        return self.score(msg_list), sorted(msg_list, key=lambda x: (x[0]))
