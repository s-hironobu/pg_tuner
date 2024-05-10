# Quick Start

`pg_tuner` assumes the **PostgreSQL server on the remote server is already running**.


## 1. Editing the configuration File

`pg_tuner` uses a configuration file in TOML format.
A sample file named example.toml is provided.


The filename (e.g., example.toml) determines the name of the data repository directory. For example:
+ Using example.toml creates the directory ./data_repo/example/.
+ Using first_test.toml creates the directory ./data_repo/first_test/.


|file name        | data repository         |
| --------------- | ----------------------- |
| example.toml    | ./data_repo/example/    |
| first_test.toml | ./data_repo/first_test/ |


### 1.1. Trial configuration section

The target benchmark and the number of trials are specified in the `[trial]` section:

```
[trial]

target = "sysbench"
n_trials = 10
```

### 1.2. PostgreSQL Server Configuration

The `[postgresql_server]` section defines the parameters for the remote server and the PostgreSQL server itself:

+ **host**: Server IP address
+ **hostuser**: Username on the server
+ **port**: PostgreSQL port number
+ **user**: PostgreSQL username
+ **passwd**: PostgreSQL user password
+ **db**: Database name
+ **pg_ctl**: Absolute path to the pg_ctl command
+ **pgdata**: Absolute path to the database cluster directory
+ **pgdata_backup**: Absolute path to the backup of the database cluster directory

Replace placeholder values with your actual configuration details.

```
[postgresql_server]

# Server IP
host = "192.168.128.193"

# User on the server
hostuser = "postgres"

# PostgreSQL's port
port = 5432

# PostgreSQL's user
user =  "postgres"

# PostgreSQL user's password
# Set to "None" (not "") if PostgreSQL does not require a password.
# If PostgreSQL requires a password, but you don't want to store it here, comment out the following line.
# pg_tuner will prompt you for the PostgreSQL user's password when you run it.
passwd =  "None"

# Database name
db =  "testdb"

# Absolute path to the pg_ctl command
pg_ctl = "/usr/local/pgsql/bin/pg_ctl"

# Absolute path to the database cluster
pgdata =  "/usr/local/pgsql/data"

# Absolute path to the backup of the database cluster
pgdata_backup = "/usr/local/pgsql/data.backup"
```

### 1.3. PostgreSQL Configuration Parameters Section

This section defines a set of parameters for which we will find optimal values through trial runs.

#### Parameter Specification Format:

The parameters are specified in the following format:

```
[parameter_name, lowest_value, highest_value, unit]
```

- **parameter_name**: The name of the PostgreSQL configuration parameter.
- **lowest_value**: The minimum value to be considered during trials.
- **highest_value**: The maximum value to be considered during trials.
- **unit**: The unit of measurement for the parameter (e.g., MB, ms, min). Set "" if no unit.


#### Example:

To find the best value for temp_buffers within a range of 32MB to 1024MB, use this format:

```
["temp_buffers", 32, 1024, "MB"]
```


#### Configuration Sections:

The parameters are grouped into two sections based on their data type:

- **pg_config_int**: This section contains parameters that expect integer values.
- **pg_config_real**: This section contains parameters that expect floating-point values.


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


### 1.4. Benchmark Configuration and Scenario

This example uses sysbench, so we configure the `[benchmark.sysbench]` section:

+ **bindir**: Absolute path to the sysbench command
+ **sb_tables**: Number of sysbench tables
+ **sb_table_size**: Number of rows in each sysbench table
+ **scenario**: Benchmark scenario (details below)


```
[benchmark.sysbench]

# the path of sysbench
bindir =  "/usr/bin"

# sysbench's table size
sb_table_size =  500000

# the number of sysbench tables
sb_tables =  5

# Scenario
scenario = [
    # [start[sec], threads, duration[sec], command, table_size, tables]
    [ 0, 10, 25, "oltp_read_write", 500000, 3],
    [ 5, 10, 20, "oltp_read_write", 500000, 3],
    [10, 10, 15, "oltp_read_write", 500000, 3],
]
```

The scenario defines a set of tasks with the following parameters:

- **start_time** [sec]: How long to wait before starting this task (relative to the scenario start)
- **threads**: Number of threads used by the task
- **duration** [sec]: Duration of the task execution
- **command**: Command to be run by the task
- **table_size**: Number of rows used by the task
- **tables**: Number of tables used by the task


In this example,
1. The first task starts just after the scenario begins and runs for 25 seconds.
2. The second task starts 5 seconds after the scenario begins, waits an additional 5 seconds, and then runs for 20 seconds.
3. The third task starts 10 seconds after the scenario begins, waits an additional 10 seconds, and then runs for 15 seconds.


![Image backup](/img/fig-quick-start-scenario.png)


All tasks use the "oltp_read_write" command, process 500,000 rows, and operate on 3 tables (`sbtable1` to `sbtable3`).


## 2. Viewing Configuration with `pg_tuner.py show`

Use the `show` command with pg_tuner.py to display the current configuration settings.

```
$ python pg_tuner.py show --conf example.toml

#--------------------------------------------
# Repository
#--------------------------------------------
base_dir = data_repo/
log_dir  = data_repo/example/

#--------------------------------------------
# Trials
#--------------------------------------------
n_trials = 10
duration per trial = 25 [sec]
Estimated total duration = 4.2 minutes

#--------------------------------------------
# Monitoring
#--------------------------------------------
linux_monitoring = True
sampling period = 10 [sec]

#--------------------------------------------
# PostgreSQL server configuration
#--------------------------------------------
host          = '192.168.128.193'
hostuser      = 'postgres'
port          = 5432
user          = 'postgres'
db            = 'testdb'
pg_ctl        = '/usr/local/pgsql/bin/pg_ctl'
pgdata        = '/usr/local/pgsql/data/'
pgdata_backup = '/usr/local/pgsql/data.backup/'

#--------------------------------------------
# PostgreSQL configuration parameters
#--------------------------------------------
config_int = [
	[temp_buffers, 32, 1024, MB],
	[work_mem, 32, 1024, MB],
	[maintenance_work_mem, 32, 512, MB],
	[bgwriter_delay, 100, 1000, ms],
	[bgwriter_lru_maxpages, 0, 1000, ],
	[wal_buffers, 32, 512, MB],
	[wal_writer_delay, 10, 10000, ms],
	[checkpoint_timeout, 1, 10, min],
	[effective_cache_size, 4, 8, GB],
	[default_statistics_target, 100, 2048, ],
	[autovacuum_naptime, 20, 200, s],
	[autovacuum_vacuum_threshold, 1000, 500000, ],
	[autovacuum_vacuum_insert_threshold, 1000, 500000, ],
	[autovacuum_analyze_threshold, 1000, 500000, ],
]
config_real = [
	[checkpoint_completion_target, 0.1, 0.9, ],
	[autovacuum_vacuum_scale_factor, 0.0, 0.1, ],
	[autovacuum_vacuum_insert_scale_factor, 0.0, 0.1, ],
	[autovacuum_analyze_scale_factor, 0.0, 0.1, ],
]

#--------------------------------------------
# benchmark configuration
#--------------------------------------------
scenario = [
	[0, 10, 20, oltp_write_only, 500000, 3],
	[5, 10, 15, oltp_write_only, 500000, 3],
	[10, 10, 10, oltp_write_only, 500000, 3],
]
additional_monitor_items = [
]

Required max connections = 30

Total number of connections per trial = 30
Total number of connections           = 300
```

## 3. Creating Benchmark Tables with `pg_tuner.py create`

Run the `create` command on the remote server to create the benchmark tables.

```
$ python pg_tuner.py create --conf example.toml
```

## 4. Backing Up the Database Cluster

Create a backup of the database cluster before starting a trial. This ensures consistent initial conditions for each trial run.

```
$ python pg_tuner.py backup --conf example.toml
```

![Image backup](/img/fig-quick-start-backup.png)


#### Reason for Backup:
The backup is used to restore the database cluster to a known state before each trial run,
ensuring fair comparisons between different configurations.


#### Backup Method:
The backup is created using the copy command, not a tar-based archiving tool.
This is because tar-based methods can be time-consuming for large database clusters.



## 5. Checking Configuration with `pg_tuner.py check`

Use the `check` command to verify the trial configuration. This command checks:

+ Accessibility to the remote server
+ PostgreSQL server configuration
+ Benchmark configuration


```
$ python pg_tuner.py check --conf example.toml
Enter server passwd:
Password:
Server Check Start.
(1) Access to 192.168.128.193:
ok.
(2) Check backup file:
backup file:'/usr/local/pgsql/data.backup/' exists.
ok.
(3) Check directories:
ok.
(4) Check preload libraries:
ok.
(5) Check include_if_exists dir:
ok.
(6) Check postgresql server status:
Error: no server running. Start your postgresql server.
```

The check command terminates immediately if it encounters any errors.


```
$ python pg_tuner.py check --conf example.toml
Enter server passwd:
Password:
Server Check Start.
(1) Access to 192.168.128.193:
ok.
(2) Check backup file:
backup file:'/usr/local/pgsql/data.backup/' exists.
ok.
(3) Check directories:
ok.
(4) Check preload libraries:
ok.
(5) Check include_if_exists dir:
ok.
(6) Check postgresql server status:
ok.
(7) postgresql server stop:
ok.
(8) postgresql server start:
ok.
Server Check finished.

Sysbench-Check Start.
(1) Check sysbench dir:
ok.
(2) Access to 192.168.128.193:
ok.
(3) Check sysbench tables:
ok.
(4) Check sysbench table's row:
ok.
Sysbench-Check finished.

Sysbench configuration check start.
(1) Sysbench configuration:
ok.
(2) Sysbench scenario:
ok.
Sysbench configuration check finished.

Required max connections = 30

Total number of connections per trial = 30
Total number of connections           = 300

```

## 6. Running Trials with `pg_tuner.py run`

Run the tuning trials using the `run` command.


```
$ python pg_tuner.py run --conf example.toml
Enter server passwd:
Password:
Server Check Start.

... check again ...

[I 2024-04-26 02:55:00,082] A new study created in RDB with name: example/
Currently running 'cp -r /usr/local/pgsql/data.backup/ /usr/local/pgsql/data/'
... done.
waiting for server to start....2024-04-26 02:55:05.600 JST [433728] LOG:  redirecting log output to logging collector process
2024-04-26 02:55:05.600 JST [433728] HINT:  Future log output will appear in directory "log".
 done
server started
waiting for server to shut down...... done
server stopped
[I 2024-04-26 02:55:34,719] Trial 0 finished with value: 6098.0 and parameters: {'temp_buffers': 230, 'work_mem': 279, 'maintenance_work_mem': 336, 'bgwriter_delay': 122, 'bgwriter_lru_maxpages': 73, 'wal_buffers': 131, 'wal_writer_delay': 1619, 'checkpoint_timeout': 10, 'effective_cache_size': 7, 'default_statistics_target': 225, 'autovacuum_naptime': 100, 'autovacuum_vacuum_threshold': 291078, 'autovacuum_vacuum_insert_threshold': 349085, 'autovacuum_analyze_threshold': 106076, 'checkpoint_completion_target': 0.8313743732876618, 'autovacuum_vacuum_scale_factor': 0.04865056246849177, 'autovacuum_vacuum_insert_scale_factor': 0.023154882623376716, 'autovacuum_analyze_scale_factor': 0.038530016203082364}. Best is trial 0 with value: 6098.0.
Currently running 'cp -r /usr/local/pgsql/data.backup/ /usr/local/pgsql/data/'
... done.
waiting for server to start....2024-04-26 02:55:45.416 JST [434056] LOG:  redirecting log output to logging collector process
2024-04-26 02:55:45.416 JST [434056] HINT:  Future log output will appear in directory "log".
... done
server started
waiting for server to shut down...... done
server stopped

... snip ...

waiting for server to shut down......... done
server stopped
[I 2024-04-26 03:02:06,608] Trial 8 finished with value: 2148.0 and parameters: {'temp_buffers': 904, 'work_mem': 934, 'maintenance_work_mem': 34, 'bgwriter_delay': 150, 'bgwriter_lru_maxpages': 982, 'wal_buffers': 113, 'wal_writer_delay': 204, 'checkpoint_timeout': 2, 'effective_cache_size': 5, 'default_statistics_target': 953, 'autovacuum_naptime': 97, 'autovacuum_vacuum_threshold': 107484, 'autovacuum_vacuum_insert_threshold': 346756, 'autovacuum_analyze_threshold': 97808, 'checkpoint_completion_target': 0.5866537761428244, 'autovacuum_vacuum_scale_factor': 0.0693346351520014, 'autovacuum_vacuum_insert_scale_factor': 0.04516949462916279, 'autovacuum_analyze_scale_factor': 0.029667468878086467}. Best is trial 0 with value: 6098.0.
Currently running 'cp -r /usr/local/pgsql/data.backup/ /usr/local/pgsql/data/'
... done.
waiting for server to start.....2024-04-26 03:02:19.766 JST [436693] LOG:  redirecting log output to logging collector process
2024-04-26 03:02:19.766 JST [436693] HINT:  Future log output will appear in directory "log".
.... done
server started
waiting for server to shut down....... done
server stopped
[I 2024-04-26 03:02:56,773] Trial 9 finished with value: 2096.0 and parameters: {'temp_buffers': 784, 'work_mem': 323, 'maintenance_work_mem': 485, 'bgwriter_delay': 933, 'bgwriter_lru_maxpages': 18, 'wal_buffers': 488, 'wal_writer_delay': 7906, 'checkpoint_timeout': 10, 'effective_cache_size': 7, 'default_statistics_target': 1183, 'autovacuum_naptime': 198, 'autovacuum_vacuum_threshold': 143126, 'autovacuum_vacuum_insert_threshold': 441320, 'autovacuum_analyze_threshold': 45625, 'checkpoint_completion_target': 0.8293865094414276, 'autovacuum_vacuum_scale_factor': 0.030118294270354208, 'autovacuum_vacuum_insert_scale_factor': 0.08685316136814247, 'autovacuum_analyze_scale_factor': 0.08308168356269717}. Best is trial 0 with value: 6098.0.
Best objective value: 6098.0
Best parameter: {'temp_buffers': 230, 'work_mem': 279, 'maintenance_work_mem': 336, 'bgwriter_delay': 122, 'bgwriter_lru_maxpages': 73, 'wal_buffers': 131, 'wal_writer_delay': 1619, 'checkpoint_timeout': 10, 'effective_cache_size': 7, 'default_statistics_target': 225, 'autovacuum_naptime': 100, 'autovacuum_vacuum_threshold': 291078, 'autovacuum_vacuum_insert_threshold': 349085, 'autovacuum_analyze_threshold': 106076, 'checkpoint_completion_target': 0.8313743732876618, 'autovacuum_vacuum_scale_factor': 0.04865056246849177, 'autovacuum_vacuum_insert_scale_factor': 0.023154882623376716, 'autovacuum_analyze_scale_factor': 0.038530016203082364}
waiting for server to start....2024-04-26 03:02:57.844 JST [436830] LOG:  redirecting log output to logging collector process
2024-04-26 03:02:57.844 JST [436830] HINT:  Future log output will appear in directory "log".
 done
server started
```

After running trials, `pg_tuner` recommends the optimal configuration parameters.


## 7. Repository

The results of the trials are stored in a data repository named data_repo.
This repository helps you track and analyze the optimization process.

```
$ ls -1 data_repo/example/
0000
0001
0002
...
benchmark.conf
best_result
study.db
```

The repository contains the following files and subdirectories:
+ **benchmark.conf**: This file stores the benchmark configuration, which is identical to the configuration file in TOML format.
+ **best_result**: This file contains the recommended optimal configuration parameters found by pg_tuner.
+ **study.db**: This is an sqlite3 database that stores the data used by the optimization algorithm (optuna).
+ **NNN**: Subdirectories named NNN (e.g., 0001, 0002) store the results of each individual trial.


Each trial directory (NNN) contains the following files:
+ **score.txt**: This file holds the score of this specific trial run. The score represents the performance metric used to evaluate each configuration.
+ **trial.conf**: This is the additional configuration file for PostgreSQL that was used in this particular trial.
+ **csv files**: These files contain detailed statistics collected during the trial (details can be found in the README-command.md file).

```
$ ls -1 data_repo/example/0000/
autovacuum.csv
bgwriter.csv
checkpointer.csv
free.csv
io.csv
iostat.csv
mpstat.csv
netstat.csv
numconnections.csv
result.csv
score.txt
timestamp.csv
trial.conf
vmstat.csv
wal.csv
```

Here's an example of the optimal parameter set obtained by pg_tuner after 10 trials.

```
$ cat data_repo/example/best_result
best_value=6098.0

best_params = {
	'temp_buffers': '230',
	'work_mem': '279',
	'maintenance_work_mem': '336',
	'bgwriter_delay': '122',
	'bgwriter_lru_maxpages': '73',
	'wal_buffers': '131',
	'wal_writer_delay': '1619',
	'checkpoint_timeout': '10',
	'effective_cache_size': '7',
	'default_statistics_target': '225',
	'autovacuum_naptime': '100',
	'autovacuum_vacuum_threshold': '291078',
	'autovacuum_vacuum_insert_threshold': '349085',
	'autovacuum_analyze_threshold': '106076',
	'checkpoint_completion_target': '0.8313743732876618',
	'autovacuum_vacuum_scale_factor': '0.04865056246849177',
	'autovacuum_vacuum_insert_scale_factor': '0.023154882623376716',
	'autovacuum_analyze_scale_factor': '0.038530016203082364',
}
... snip ...
```
