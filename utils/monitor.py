"""
monitor.py

  Copyright (c) 2024-2025, Hironobu Suzuki @ interdb.jp
"""

import sys, os
from .common import Log, Common
from .psql import Psql


class Monitor(Psql):
    def __init__(
        self,
        host,
        port,
        user,
        database,
        password,
        log_dir,
        linux_monitoring,
        additional_monitor_items=None,
    ):
        super().__init__(host, port, user, database, password)
        self.log_dir = Common.set_dir(log_dir)
        self.linux_monitoring = linux_monitoring
        self.additional_monitor_items = additional_monitor_items

        self.connection = None
        self.count = 0

    """
    Public methods
    """

    """
    # get monitoring items
    """
    def get_basic_monitoring_items(self):
        return ["timestamp", "numconnections", "checkpointer", "bgwriter", "wal", "autovacuum", "io"]

    def get_linux_monitoring_items(self):
        return ["vmstat", "mpstat", "free", "iostat", "netstat"]

    """
    # Connects to the PostgreSQL server.
    """

    def start(self):

        if self.connect():
            if Log.info <= Common.DEFAULT_LOG_LEVEL:
                print("Info: Monitor: Connection established.")
            return True
        else:
            return False

    """
    # Executes queries to monitor PostgreSQL server statistics and saves the results.
    """

    def monitoring(self):

        _print_column = True if self.count == 0 else False
        self.count += 1

        sql = [
            ["timestamp", "SELECT current_timestamp::timestamp(0);"],
            [
                "numconnections",
                "SELECT sum(numbackends) AS numconnections FROM pg_stat_database;",
            ],
            [
                "checkpointer",
                "SELECT num_timed, num_requested, write_time, sync_time, buffers_written FROM pg_stat_checkpointer;",
            ],
            [
                "bgwriter",
                "SELECT buffers_clean, maxwritten_clean, buffers_alloc FROM pg_stat_bgwriter;",
            ],
            [
                "wal",
                "SELECT wal_records, wal_fpi, wal_bytes, wal_buffers_full, wal_write, wal_sync, wal_write_time, wal_sync_time FROM pg_stat_wal;",
            ],
            [
                "autovacuum",
                "SELECT sum(reads) AS reads, sum(writes) AS writes, sum(writebacks) AS writebacks, sum(extends) AS extends, sum(hits) AS hits, sum(evictions) AS evictions, sum(reuses) AS reuses, sum(fsyncs) as fsyncs FROM pg_stat_io WHERE backend_type LIKE 'autovacuum%';",
            ],
            [
                "io",
                "SELECT sum(reads) AS reads, sum(writes) AS writes, sum(writebacks) AS writebacks, sum(extends) AS extends, sum(hits) AS hits, sum(evictions) aS evictions, sum(reuses) AS reuses, sum(fsyncs) as fsyncs FROM pg_stat_io WHERE backend_type !~* '(autovacuum)|(checkpointer)|(background writer)';",
            ],
        ]

        # Add linux stats monitoring using pg_linux_stats module
        if self.linux_monitoring == True:
            sql += [
                ["vmstat", "SELECT * FROM pg_vmstat();"],
                ["mpstat", "SELECT * FROM pg_mpstat() WHERE cpu = 'all';"],
                ["free", "SELECT * FROM pg_free();"],
                [
                    "iostat",
                    "SELECT sum(tps) AS tps, sum(kb_read_s) AS kb_read_s, sum(kb_wrtn_s) AS lb_wrtn_s, sum(kb_dscd_s) AS kb_dscd_s, sum(kb_read) AS kb_read, sum(kb_wrtn) AS kb_wrtn, sum(kb_dscd) AS kb_dscd  FROM pg_iostat() WHERE device NOT LIKE 'loop%';",
                ],
                [
                    "netstat",
                    "SELECT sum(rx_ok) AS rx_ok, sum(tx_ok) AS tx_ok FROM pg_netstat();",
                ],
            ]

        # Add additional monitor items
        if self.additional_monitor_items != None:
            sql += self.additional_monitor_items

        # Main loop
        for [item, sql] in sql:
            cur = self.exec_select_cmd(sql)
            if cur == None:
                if Log.error <= Common.DEFAULT_LOG_LEVEL:
                    print("Error: Monitor failed to issue sql:'{}'".format(sql))
                return False

            if cur.rowcount == 0:
                if Log.info <= Common.DEFAULT_LOG_LEVEL:
                    print("Info: sql:'{}' returns 0 row".format(sql))
                continue

            _file = self.log_dir + str(item) + ".csv"
            try:
                with open(_file, "a") as f:
                    try:
                        if _print_column:
                            colnames = [col.name for col in cur.description]
                            f.write(",".join(map(str, colnames)) + "\n")
                        for row in cur:
                            f.write(",".join(map(str, row)) + "\n")
                    except Exception as e:
                        if Log.error <= Common.DEFAULT_LOG_LEVEL:
                            print("Error: Monitor failed to write file:'{}'".format(_file))
                        return False
            except Exception as ee:
                if Log.error <= Common.DEFAULT_LOG_LEVEL:
                    print("Error: Monitor could not open file:'{}'".format(_file))
                return False

        return True

    """
    # Disconnects the PostgreSQL server.
    """

    def stop(self):
        with self.connection.cursor() as cur:
            if Log.info <= Common.DEFAULT_LOG_LEVEL:
                print("Info: Monitor: Execute Checkpoint command.")
            self.exec_sql(cur, "vacuum; checkpoint;")

        self.connection.close()
        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: Monitor: Connection closed.")


if __name__ == "__main__":

    host = "192.168.128.193"
    user = "postgres"
    db = "testdb"
    log_dir = "../data_repo/test/"

    mon = Monitor(host, 5432, user, db, None, log_dir)

    ret = mon.start()
    print("mon.start()={}".format(str(ret)))
    ret = mon.monitoring()
    print("mon.monitor()={}".format(str(ret)))
    mon.stop()
