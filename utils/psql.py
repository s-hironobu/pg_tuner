"""
psql.py

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

import psycopg2, sys
from .common import Common, Log

class Psql:
    def __init__(self, host, port, user, database, password=None):
        self.host = host
        self.port = port
        self.user = user
        self.database = database
        self.password = password

        self.connection = None

    """
    Public methods
    """

    """
    # Creates a connection to the PostgreSQL server.
    """
    def connect(self, autocommit=True):
        _conn = "host='{}' port={} user='{}' dbname='{}'".format(
            str(self.host), self.port, str(self.user), str(self.database)
        )
        if self.password != None:
            _conn += " password='{}'".format(str(self.password))

        if Log.debug3 <= Common.DEFAULT_LOG_LEVEL:
            print("Debug3: psql: conn=", _conn)

        try:
            _connection = psycopg2.connect(_conn, connect_timeout=Common.CONNECTION_TIMEOUT)
        except psycopg2.OperationalError as e:
            print("Error: Could not connect to '{}'".format(self.host))
            print(e)
            return False

        if autocommit:
            _connection.autocommit = True

        self.connection = _connection
        return True

    """
    # Closes the connection.
    """
    def close(self):
        if self.connection != None:
            self.connection.close()

    """
    # Executes a SELECT query and returns the results.
    """
    def exec_select_cmd(self, sql):
        if self.connection == None:
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("Error: connection is None.")
            return None

        _cur = self.connection.cursor()
        try:
            _cur.execute(sql)
        except Exception as err:
            _cur.close()
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("SQL Error:'{}'".format(sql))
            return None

        return _cur

    """
    # Executes an SQL statement without returning results.
    """
    def exec_sql(self, cur, sql):
        try:
            cur.execute(sql)
        except Exception as err:
            cur.close()
            if Log.error <= Common.DEFAULT_LOG_LEVEL:
                print("SQL Error:'{}'".format(sql))
            return False
        return True

if __name__ == "__main__":

    host = "192.168.128.193"
    #host = "localhost"
    user = "postgres"
    db = "testdb"
    log_dir = "../data_repo/test/"

    psql = Psql(host, 5432, user, db)

    psql.connect()

    """
    with psql.connection.cursor() as cur:
        psql.exec_sql(cur, "checkpoint;")
    """

    #sql = "SELECT * FROM pgbench_history;"
    sql = "SELECT filler FROM pgbench_accounts;"
    cur = psql.exec_select_cmd(sql)
    if cur == None:
        print("Error:  sql:'{}'".format(sql))
    for row in cur:
        print("row=", row)

    psql.close()
