"""
sysbench.py

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

import subprocess
import psycopg2
import sys, os

from .benchmark import Benchmark

sys.path.append("..")
from utils import Common, Psql, Log


class Sysbench(Benchmark):
    def __init__(
        self,
        host,
        port,
        user,
        password,
        db,
        sysbench_table_size,
        sysbench_tables,
        sysbench_bindir,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.sysbench_table_size = sysbench_table_size
        self.sysbench_tables = sysbench_tables
        self.sysbench_bindir = Common.set_dir(sysbench_bindir)


    """
    Public methods
    """

    """
    # Initializes sysbench
    """

    def create_bench(self, type="oltp_common"):

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: Initialize sysbench tables.")

        psql = Psql(self.host, self.port, self.user, self.db, self.password)
        if psql.connect() == False:
            sys.exit(1)

        _sql = "SELECT count(c.relname) FROM pg_catalog.pg_class c WHERE c.relkind IN ('r') AND c.relname LIKE 'sbtest%';"
        num_sbtest = 0
        cur = psql.exec_select_cmd(_sql)
        if cur == None:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: Cannot issue sql:'{}'".format(_sql))
            sys.exit(1)

        for _row in cur:
            num_sbtest = _row[0]
        cur.close()
        psql.close()

        if num_sbtest != 0:
            print("Error: {} already exists".format("sysbench tables"))
            sys.exit(1)

        if self.password == None:
            PG_CONN = "--db-driver=pgsql --pgsql-host={} --pgsql-user={} --pgsql-db={}".format(
                str(self.host), str(self.user), str(self.db)
            )
        else:
            PG_CONN = "--db-driver=pgsql --pgsql-host={} --pgsql-user={} --pgsql-password={} --pgsql-db={}".format(
                str(self.host), str(self.user), str(self.password), str(self.db)
            )

        SYSBENCH_OPTIONS = "--table_size={} --tables={}".format(
            self.sysbench_table_size, self.sysbench_tables
        )
        cmd = "{}sysbench {} {} {} prepare".format(
            self.sysbench_bindir, str(type), PG_CONN, SYSBENCH_OPTIONS
        )

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: command '{}'".format(str(cmd)))

        try:
            completed_process = subprocess.run(
                cmd, shell=True, check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print("Error: {}".format(str(e.stdout)))
            sys.exit(1)

        return True

    """
    # Drops pgbench
    """

    def drop_bench(self):
        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: Drop sysbench tables.")

        psql = Psql(self.host, self.port, self.user, self.db, self.password)
        if psql.connect() == False:
            sys.exit(1)

        _sql = "SELECT count(c.relname) FROM pg_catalog.pg_class c WHERE c.relkind IN ('r') AND c.relname LIKE 'sbtest%';"
        num_sbtest = 0
        cur = psql.exec_select_cmd(_sql)
        if cur == None:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: Cannot issue sql:'{}'".format(_sql))
            sys.exit(1)

        for _row in cur:
            num_sbtest = _row[0]
        cur.close()
        if num_sbtest == 0:
            print("Error: {} not found".format("sysbench tables"))
            psql.close()
            sys.exit(1)

        with psql.connection.cursor() as cur:
            for i in range(1, num_sbtest + 1):
                tbl = "sbtest{}".format(str(i))
                _sql = "DROP TABLE {} CASCADE;".format(tbl)
                if psql.exec_sql(cur, _sql) == False:
                    psql.close()
                    sys.exit(1)

            if psql.exec_sql(cur, "VACUUM;") == False:
                psql.close()
                sys.exit(1)

        cur.close()
        psql.close()
        del psql

        return True

    """
    # Checks sysbench configuration
    """

    def check(self):

        print("Sysbench-Check Start.")

        print("(1) Check sysbench dir:")
        if os.path.isdir(self.sysbench_bindir) == False:
            print("Error: sysbench_bindir: '{}' not found.".format(self.sysbench_bindir))
            sys.exit(1)

        print("ok.")

        print("(2) Access to {}:".format(self.host))
        psql = Psql(self.host, self.port, self.user, self.db, self.password)
        if psql.connect() == False:
            sys.exit(1)

        print("ok.")

        print("(3) Check sysbench tables:")
        _sql = "SELECT count(c.relname) FROM pg_catalog.pg_class c WHERE c.relkind IN ('r') AND c.relname LIKE 'sbtest%';"
        num_sbtest = 0
        cur = psql.exec_select_cmd(_sql)
        if cur == None:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: Cannot issue sql:'{}'".format(_sql))
            return

        for _row in cur:
            num_sbtest = _row[0]
        cur.close()
        if num_sbtest == 0:
            print("Error: {} not found".format("sysbench tables"))
            cur.close()
            sys.exit(1)

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: number of sysbench table = ", num_sbtest)

        print("ok.")

        print("(4) Check sysbench table's row:")
        _sql = "SELECT count(id) FROM sbtest1;"
        num_sbtest_row = 0
        cur = psql.exec_select_cmd(_sql)
        if cur == None:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: Cannot issue sql:'{}'".format(_sql))
                sys.exit(1)

        for _row in cur:
            num_sbtest_row = _row[0]
        cur.close()

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: number of sysbench table row = ", num_sbtest_row)

        psql.close()

        if num_sbtest < self.sysbench_tables:
            print(
                "Error: The actual number of sbtests ({}) is less than the specified number ({}).".format(
                    str(num_sbtest), str(self.sysbench_tables)
                )
            )
            sys.exit(1)

        if num_sbtest_row < self.sysbench_table_size:
            print(
                "Error: The actual row number of sbtest ({}) is less than the specified row number ({}).".format(
                    str(num_sbtest_row), str(self.sysbench_table_size)
                )
            )
            sys.exit(1)

        print("ok.")

        print("Sysbench-Check finished.")

        return num_sbtest, num_sbtest_row

    def command_type_check(self, command):
        command_list = [
            "oltp_delete",
            "oltp_insert",
            "oltp_read_only",
            "oltp_read_write",
            "oltp_point_select",
            "oltp_update_index",
            "oltp_update_non_index",
            "oltp_write_only",
        ]
        if command not in command_list:
            return False
        return True

    """
    # Runs sysbench
    """

    def run(self, sysbench_threads, sysbench_time, sysbench_command="oltp_read_write"):

        if self.command_type_check(sysbench_command) == False:
            print("Error: command '{}' not supported.".format(str(sysbench_command)))
            sys.exit(1)

        if self.password == None:
            PG_CONN = "--db-driver=pgsql --pgsql-host={} --pgsql-user={} --pgsql-db={}".format(
                str(self.host), str(self.user), str(self.db)
            )
        else:
            PG_CONN = "--db-driver=pgsql --pgsql-host={} --pgsql-user={} --pgsql-password={} --pgsql-db={}".format(
                str(self.host), str(self.user), str(self.password), str(self.db)
            )

        SYSBENCH_OPTIONS = "--table_size={} --tables={} --threads={} --time={}".format(
            self.sysbench_table_size,
            self.sysbench_tables,
            sysbench_threads,
            sysbench_time,
        )

        cmd = "{}sysbench {} {} {} run".format(
            self.sysbench_bindir, sysbench_command, PG_CONN, SYSBENCH_OPTIONS
        )
        if Log.debug1 <= Common.DEFAULT_LOG_LEVEL:
            print("Debug1: command '{}'".format(str(cmd)))

        try:
            completed_process = subprocess.run(
                cmd, shell=True, check=True, capture_output=True
            )
            lines = completed_process.stdout.decode("utf-8").splitlines()
        except subprocess.CalledProcessError as e:
            print("Error: {}".format(str(e.stdout)))
            sys.exit(1)

        if Log.debug1 <= Common.DEFAULT_LOG_LEVEL:
            print("Debug1: sysbench lines=", lines)

        return self.parse_result(lines)

    """
    # Returns the result as a list

    Note: There are differences in the output between versions 1.1 and 1.0.
    Sample output for each version is provided at the end of this class.
    """

    def parse_result(self, lines):
        sql_read = sql_write = sql_other = sql_total = sql_transactions = None
        sql_queries = sql_ignored = sql_reconnects = None
        throughput_events = throughput_time = throughput_total = None
        latency_min = latency_avg = latency_max = latency_95 = latency_sum = None
        threads_events = threads_execution = None

        for l in lines:
            l = l.split()
            if l == []:
                continue

            if l[0] == "read:":
                sql_read = l[1]
            elif l[0] == "write:":
                sql_write = l[1]
            elif l[0] == "other:":
                sql_other = l[1]
            elif l[0] == "total:":
                sql_total = l[1]
            elif l[0] == "transactions:":
                sql_transactions = l[1]
            elif l[0] == "queries:":
                sql_queries = l[1]
            elif l[0] == "ignored":
                sql_ignored = l[2]
            elif l[0] == "reconnects:":
                sql_reconnects = l[1]
            elif l[0] == "events/s": # ver 1.1 or later.
                throughput_events = l[2]
            elif (l[0] == "time" and l[1] == "elapsed:") or (l[0] == "total" and l[1] == "time:"):
                throughput_time = l[2].rstrip()  # remove 's'
            elif l[0] == "total" and l[1] == "number":
                throughput_total = l[4]
            elif l[0] == "min:":
                latency_min = l[1]
            elif l[0] == "avg:":
                latency_avg = l[1]
            elif l[0] == "max:":
                latency_max = l[1]
            elif l[0] == "95th":
                latency_95 = l[2]
            elif l[0] == "sum:":
                latency_sum = l[1]
            elif l[0] == "events":
                threads_events = l[2]
            elif l[0] == "execution":
                threads_execution = l[3]

        return [
            sql_read,
            sql_write,
            sql_other,
            sql_total,
            sql_transactions,
            sql_queries,
            sql_ignored,
            sql_reconnects,
            throughput_events,
            throughput_time,
            throughput_total,
            latency_min,
            latency_avg,
            latency_max,
            latency_95,
            latency_sum,
            threads_events,
            threads_execution,
        ]

    """
    # Returns column name list
    """

    def get_col_name(self):
        return [
            "sql_read",
            "sql_write",
            "sql_other",
            "sql_total",
            "sql_transactions",
            "sql_queries",
            "sql_ignored",
            "sql_reconnects",
            "throughput_events",
            "throughput_time",
            "throughput_total",
            "latency_min",
            "latency_avg",
            "latency_max",
            "latency_95",
            "latency_sum",
            "threads_events",
            "threads_execution",
        ]


"""

# sysbench 1.1:

SQL statistics:
    queries performed:
        read:                            345576
        write:                           98734
        other:                           49368
        total:                           493678
    transactions:                        24683  (2467.60 per sec.)
    queries:                             493678 (49353.78 per sec.)
    ignored errors:                      1      (0.10 per sec.)
    reconnects:                          0      (0.00 per sec.)

Throughput:
    events/s (eps):                      2467.5990
    time elapsed:                        10.0028s
    total number of events:              24683

Latency (ms):
         min:                                    2.19
         avg:                                    4.05
         max:                                   29.15
         95th percentile:                        0.00
         sum:                               100000.36

Threads fairness:
    events (avg/stddev):           2468.3000/5.40
    execution time (avg/stddev):   10.0000/0.00

# sysbench 1.0:

SQL statistics:
    queries performed:
        read:                            18270
        write:                           5213
        other:                           2613
        total:                           26096
    transactions:                        1303   (433.54 per sec.)
    queries:                             26096  (8682.86 per sec.)
    ignored errors:                      2      (0.67 per sec.)
    reconnects:                          0      (0.00 per sec.)

General statistics:
    total time:                          3.0034s
    total number of events:              1303

Latency (ms):
         min:                                    3.16
         avg:                                    4.60
         max:                                   36.99
         95th percentile:                        8.58
         sum:                                 5999.21

Threads fairness:
    events (avg/stddev):           651.5000/0.50
    execution time (avg/stddev):   2.9996/0.00

"""

if __name__ == "__main__":

    host = "192.168.128.193"
    user = "postgres"
    passwd = None
    port = 5432
    db = "testdb"
    table_size = 100000
    tables = 3
    sysbench_bindir = "/usr/bin"

    sb = Sysbench(
        host, port, user, passwd, db, table_size, tables, sysbench_bindir
    )

    # sb.create_bench()
    # sb.drop_bench()
    sb.check()

    # ret = sb.run(3, 2)
    # print(ret)
