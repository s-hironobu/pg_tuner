"""
common.py

  Copyright (c) 2024-2025, Hironobu Suzuki @ interdb.jp
"""

from enum import IntEnum


class Log(IntEnum):
    error = 0
    warning = 1
    notice = 2
    info = 3
    debug1 = 4
    debug2 = 5
    debug3 = 6
    debug4 = 7
    debug5 = 8


class Common:
    def __init__(self):
        pass

    """
    # PostgreSQL
    """
    ADDITIONAL_CONF = "trial.conf"
    ADDITIONAL_CONF_DIR = "./conf.d/"
    REQUIRED_MODULES = ["pg_linux_stats"]

    BANNER_TIMEOUT = 5
    AUTH_TIMEOUT = 5
    CHANNEL_TIMEOUT = 5

    IGNORE_PARAMS = ["max_connections", "shared_buffers"]

    """
    # Repository
    """
    REPOSITORY_DIR = "data_repo"
    CONF_FILE = "benchmark.conf"
    BEST_RESULT_FILE = "best_result"
    STAT_FILE = "stat.dat"
    RESULT_FILE = "result.csv"
    SCORE_FILE = "score.txt"

    STUDY_DB = "study.db"

    """
    # psql
    """
    CONNECTION_TIMEOUT = 5

    """
    # benchmark
    """
    TIMEOUT_MARGIN = 20

    """
    # postgresql default params
    """
    DEFAULT_MAX_CONNECTIONS = 100
    DEFAULT_RESERVED_CONNECTIONS = 0
    DEFAULT_SUPERUSERRESERVED_CONNECTIONS = 3

    """
    #
    """
    DEFAULT_LOG_LEVEL = Log.notice

    """
    #
    """
    DEFAULT_IMPORTANT_PARAMS_FILE = "important_params.py"

    # ["TPE" |  "Random" | "Grid" | "CmaEs" | "QMC" | "GP" ]
    # https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
    DEFAULT_SAMPLING_MODE = "TPE"

    """
    Public methods
    """

    """
    Input: time [sec]
    Return: time, unit
    """
    def pretty_time_format(time):
        unit = "minutes"
        time /= 60
        if time > 120:
            time /= 60
            unit = "hours"

        return time, unit


    """
    # Appends a trailing slash to the directory path if it's missing.
    """
    def set_dir(dirname):
        if dirname[-1] != '/':
            dirname += '/'
        return dirname

    """
    # Estimates the maximum number of concurrent connections the scenario will require.
    """
    def compute_max_connections(scenario, margin=5):
        max_connections = 0
        connections = 0
        hist = {}

        for s in scenario:
            _s = s[0]  # start timestamp
            _c = s[1]  # connections
            _e = s[2] + _s + margin  # end timestamp

            if _s in hist:
                hist[_s] += _c
            else:
                hist[_s] = _c

            if _e in hist:
                hist[_e] -= _c
            else:
                hist[_e] = -1 * _c

        keys = sorted(hist.keys())
        for k in keys:
            connections += hist[k]
            if connections > max_connections:
                max_connections = connections
        return max_connections
