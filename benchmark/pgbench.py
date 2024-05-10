"""
pgbench.py

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

import subprocess
import psycopg2
import sys, os

from .benchmark import Benchmark

sys.path.append("..")
from utils import Common, Psql, Log


class Pgbench(Benchmark):
    def __init__(
        self,
        host,
        port,
        user,
        db,
        pgbench_scale,
        pgbench_bindir,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.db = db
        self.pgbench_scale = pgbench_scale
        self.pgbench_bindir = Common.set_dir(pgbench_bindir)


    """
    Public methods
    """

    """
    # Initializes pgbench
    """

    def create_bench(self, scale=1):

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: Initialize pgbench.")

        psql = Psql(self.host, self.port, self.user, self.db)
        if psql.connect() == False:
            sys.exit(1)

        _sql = "SELECT count(c.relname) FROM pg_catalog.pg_class c WHERE c.relkind IN ('r') AND c.relname LIKE 'pgbench%';"
        cur = psql.exec_select_cmd(_sql)
        if cur == None:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: Cannot issue sql:'{}'".format(_sql))
            sys.exit(1)

        for _row in cur:
            if _row[0] != 0:
                print("Error: {} already exists".format("pgbench tables"))
                sys.exit(1)

        cur.close()
        psql.close()

        """
        We assume that the password of postgresql server is set to PGPASSWORD environment variable.

        ```
        export PGPASSWORD="passwd"
        ```
        """

        cmd = "{}pgbench -i -h {} -U {} -p {} -s {} {}".format(
            self.pgbench_bindir,
            str(self.host),
            str(self.user),
            self.port,
            self.pgbench_scale,
            self.db,
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
            print("Info: Drop pgbench tables.")

        psql = Psql(self.host, self.port, self.user, self.db)
        if psql.connect() == False:
            sys.exit(1)

        _sql = "SELECT count(c.relname) FROM pg_catalog.pg_class c WHERE c.relkind IN ('r') AND c.relname LIKE 'pgbench%';"
        cur = psql.exec_select_cmd(_sql)
        if cur == None:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: Cannot issue sql:'{}'".format(_sql))
            sys.exit(1)

        for _row in cur:
            if _row[0] == 0:
                print("Error: {} not found".format("pgbench tables"))
                psql.close()
                sys.exit(1)

        cur.close()

        with psql.connection.cursor() as cur:
            _sql = "DROP TABLE {}, {}, {}, {} CASCADE;".format(
                "pgbench_accounts",
                "pgbench_branches",
                "pgbench_history",
                "pgbench_tellers",
            )
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
    # Checks pgbench configuration
    """

    def check(self):

        print("Pgbench-Check Start.")

        print("(1) Check pgbench dir:")
        if os.path.isdir(self.pgbench_bindir) == False:
            print("Error: pgbench_bindir: '{}' not found.".format(self.pgbench_bindir))
            sys.exit(1)

        print("ok.")

        print("(2) Access to {}:".format(self.host))
        psql = Psql(self.host, self.port, self.user, self.db)
        if psql.connect() == False:
            sys.exit(1)

        print("ok.")

        print("(3) Check pgbench tables:")
        _sql = "SELECT count(c.relname) FROM pg_catalog.pg_class c WHERE c.relkind IN ('r') AND c.relname LIKE 'pgbench%';"
        cur = psql.exec_select_cmd(_sql)
        if cur == None:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: Cannot issue sql:'{}'".format(_sql))
            return

        for _row in cur:
            if _row[0] == 0:
                print("Error: {} not found".format("pgbench tables"))
                cur.close()
                sys.exit(1)
        cur.close()

        print("ok.")

        print("(4) Check pgbench_accounts table's row:")
        _sql = "SELECT count(*) FROM pgbench_accounts;"
        num_pgbench_accounts = 0
        cur = psql.exec_select_cmd(_sql)
        if cur == None:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: Cannot issue sql:'{}'".format(_sql))
                sys.exit(1)

        for _row in cur:
            num_pgbench_accounts = _row[0]
        cur.close()

        if Log.info <= Common.DEFAULT_LOG_LEVEL:
            print("Info: number of pgbench_accounts table row = ", num_pgbench_accounts)

        psql.close()

        if num_pgbench_accounts < self.pgbench_scale * 100000:
            print(
                "Error: The actual row number of pgbench_accounts ({}) is less than the specified row number ({}: scale={}).".format(
                    num_pgbench_accounts,
                    self.pgbench_scale * 100000,
                    self.pgbench_scale,
                )
            )
            sys.exit(1)

        print("ok.")

        print("Pgbench-Check finished.")

        return num_pgbench_accounts

    """
    # Runs pgbench
    """

    def run(
        self,
        pgbench_threads,
        pgbench_time,
        pgbench_scale=None,
    ):

        """
        We assume that the password of postgresql server is set to PGPASSWORD environment variable.
        ```
        export PGPASSWORD="passwd"
        ```

        -c, --client=NUM         number of concurrent database clients (default: 1)
        -n, --no-vacuum          do not run VACUUM before tests
        -R, --rate=NUM           target rate in transactions per second
        -s, --scale=NUM          report this scale factor in output
        -t, --transactions=NUM   number of transactions each client runs (default: 10)
        -T, --time=NUM           duration of benchmark test in seconds
        --max-tries=NUM          max number of tries to run transaction (default: 1)
        """

        cmd = "{}pgbench -h {} -U {} -p {} -s {} -T {} -c {} --no-vacuum {}".format(
            self.pgbench_bindir,
            str(self.host),
            str(self.user),
            self.port,
            self.pgbench_scale,
            pgbench_time,
            pgbench_threads,
            self.db,
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
    # Returns result as a list
    """

    def parse_result(self, lines):

        """
        pgbench (17devel)
        starting vacuum...end.
        transaction type: <builtin: TPC-B (sort of)>
        scaling factor: 1
        query mode: simple
        number of clients: 10
        number of threads: 1
        maximum number of tries: 1
        duration: 10 s
        number of transactions actually processed: 4469
        number of failed transactions: 0 (0.000%)
        latency average = 22.280 ms
        initial connection time = 69.648 ms
        tps = 448.828707 (without initial connection time)
        """

        num_tx = latency_avg = init_conn = tps = None

        for l in lines:
            l = l.split()
            if l == []:
                continue

            if l[0] == "number":
                if l[2] == "transactions":
                    num_tx = l[5]
            elif l[0] == "latency":
                latency_avg = l[3]
            elif l[0] == "initial":
                init_conn = l[4]
            elif l[0] == "tps":
                tps = l[2]

        return [num_tx, latency_avg, init_conn, tps]

    """
    # Returns column name list
    """

    def get_col_name(self):
        return [
            "number_of_transactions",
            "latency_average",
            "initial_connection_time",
            "tps",
        ]


if __name__ == "__main__":

    host = "192.168.128.193"
    user = "postgres"
    port = 5432
    db = "testdb"
    pgbench_scale = 1
    pgbench_bindir = "/usr/local/pgsql/bin"

    pb = Pgbench(host, port, user, db, pgbench_scale, pgbench_bindir)

    # pb.drop_bench()
    pb.check()

    # pb.create_bench()

    # ret = pb.run(3, 2)
    # print(ret)
