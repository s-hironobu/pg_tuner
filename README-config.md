# Configuration

`pg_tuner` uses a configuration file in TOML format.
A sample file named example.toml is provided.


The filename (e.g., example.toml) determines the name of the data repository directory. For example:
+ Using example.toml creates the directory ./data_repo/example/.
+ Using first_test.toml creates the directory ./data_repo/first_test/.


|file name        | data repository         |
| --------------- | ----------------------- |
| example.toml    | ./data_repo/example/    |
| first_test.toml | ./data_repo/first_test/ |



## 1. Trial Section

+ **target** (str): Target benchmark to use. Valid options are "sysbench" or "pgbench".
+ **n_trials** (int): Number of trials to run for optimization.
+ **sampling_mode** (str): Sampling mode for hyperparameter optimization. Options include "TPE", "Random", "Grid", "CMA-ES", "QMC", or "GP". Defaults to "TPE". You can find more details about these samplers in the Optuna documentation https://optuna.readthedocs.io/.
+ **restore_everytime** (bool, default=True): Whether to restore the database cluster from the backup before each trial. This ensures a consistent starting point for each optimization run.


![Image RESTORE](/img/fig-config-restore.png)


## 2. Monitoring

+ **linux_monitoring** (bool, default=True): Whether to monitor Linux system statistics during trials. Requires the [pg_linux_stats](https://github.com/s-hironobu/pg_linux_stats.git) module.
+ **monitoring_time** (int): Interval (in seconds) between monitoring samples.

## 3. PostgreSQL Server Configuration

+ **host** (str): Server IP address
+ **hostuser** (str): Username on the server
+ **port** (int): PostgreSQL port number
+ **user** (str): PostgreSQL username
+ **passwd** (str): PostgreSQL user password. Set to "None" (not an empty string) if passwordless authentication is enabled. Otherwise, comment out this line and pg_tuner will prompt you for the password during execution.
+ **db** (str): Database name
+ **pg_ctl** (str): Absolute path to the pg_ctl command
+ **pgdata** (str): Absolute path to the database cluster directory
+ **pgdata_backup** (str): Absolute path to the backup of the database cluster directory. If `restore_everytime` is `true`, the database cluster is restored from the backup before each trial. Before trial, it should be made the backup using pg_tuner's backup command.


**Example:**

```
[postgresql_server]

host = "192.168.128.193"
hostuser = "postgres"
port = 5432
user =  "postgres"
passwd =  "None"
db =  "testdb"
pg_ctl = "/usr/local/pgsql/bin/pg_ctl"
pgdata =  "/usr/local/pgsql/data"
pgdata_backup = "/usr/local/pgsql/data.backup"
```


## 4. PostgreSQL Configuration Parameters

This section defines a set of parameters that will be optimized during the trials.

#### Parameter Specification Format:

Each parameter is specified in the following format:
```
[parameter_name, lowest_value, highest_value, unit (optional)]
```

- **parameter_name** (str): The name of the PostgreSQL configuration parameter.
- **lowest_value** (float): The minimum value to be considered during trials.
- **highest_value** (float): The maximum value to be considered during trials.
- **unit** (str): The unit of measurement for the parameter (e.g., MB, ms, min). Set "" if no unit.

#### Configuration Sections:

The parameters are grouped into two sections based on their data type:


- **pg_config_int**: This section contains parameters that expect integer values.
- **pg_config_real**: This section contains parameters that expect floating-point values.

**Example:**

```
[postgresql_conf]

pg_config_int = [
    ["temp_buffers", 32, 1024, "MB"],
    ["work_mem", 32, 1024, "MB"],
    ["maintenance_work_mem", 32, 512, "MB"],
    ["bgwriter_delay", 100, 1000, "ms"],
    ["bgwriter_lru_maxpages", 0, 1000, ""],
    ["wal_buffers", 32, 512, "MB"],
    ["wal_writer_delay", 10, 10000, "ms"],
    ["checkpoint_timeout", 1, 10, "min"],
    ["effective_cache_size", 4, 8, "GB"],
    ["default_statistics_target", 100, 2048, ""],
    ["autovacuum_naptime", 20, 200, "s"],
    ["autovacuum_vacuum_threshold", 1000, 500000, ""],
    ["autovacuum_vacuum_insert_threshold", 1000, 500000, ""],
    ["autovacuum_analyze_threshold", 1000, 500000, ""],
]

pg_config_real = [
    ["checkpoint_completion_target", 0.1, 0.9, ""],
    ["autovacuum_vacuum_scale_factor", 0.0, 0.1, ""],
    ["autovacuum_vacuum_insert_scale_factor", 0.0, 0.1, ""],
    ["autovacuum_analyze_scale_factor", 0.0, 0.1, ""],
]
```

## 5. Benchmark Configuration and Scenario

This section configures the benchmark tool (either sysbench or pgbench) and defines the workload scenario for the trials.

### 5.1. Sysbench Configuration

+ **bindir** (str): Absolute path to the sysbench command
+ **sb_tables** (int): Number of sysbench tables
+ **sb_table_size** (int): Number of rows in each sysbench table
+ **scenario**: Benchmark scenario (details below)
+ **additional_monitor_items**:
+ **additional_monitor_items** (list, optional): Additional monitoring items to collect during trials.


#### Sysbench Scenario Format:

Each task within the Sysbench scenario is defined using the following parameters:

```
[start_time[sec], threads, duration[sec], command, table_size, tables]
```

- **start_time** [sec]: How long to wait before starting this task (relative to the scenario start)
- **threads**: Number of threads used by the task
- **duration** [sec]: Duration of the task execution
- **command**: Command to be run by the task
- **table_size**: Number of rows used by the task
- **tables**: Number of tables used by the task


**Example:**

```
[benchmark.sysbench]
bindir =  "/usr/bin"
sb_table_size =  500000
sb_tables =  5
scenario = [
    [ 0, 10, 25, "oltp_read_write", 500000, 3],
    [ 5, 10, 20, "oltp_read_write", 500000, 3],
    [10, 10, 15, "oltp_read_write", 500000, 3],
]
```

![Image backup](/img/fig-quick-start-scenario.png)


### 5.2. pgbench Configuration:

+ **bindir** (str): Absolute path to the pgbench command
+ **scale** (int): The scale factor used by pgbench for workload generation.
+ **scenario**: Similar to Sysbench, defines the benchmark scenario using a set of tasks. Details on the scenario format are provided below.
+ **additional_monitor_items** (list, optional): Additional monitoring items to collect during trials.


#### pgbench Scenario Format:

Each task within the pgbench scenario is defined using the following parameters:

```
[start_time[sec], threads, duration[sec], scale]
```

- **start_time** [sec]: Time to wait before starting the task (relative to scenario start)
- **threads**: Number of threads used by the task
- **duration** [sec]: Duration of the task execution
- **scale**: Scale factor used by the task

**Example:**

```
[benchmark.pgbench]

bindir = "/usr/local/pgsql/bin"
scale = 1
scenario = [
    [ 0, 10, 20, 1],
    [ 5, 10, 15, 1],
    [10, 10, 10, 1],
]
```
