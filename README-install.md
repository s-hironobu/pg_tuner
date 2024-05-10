# Installation

Assumptions:

This guide assumes the following machine and network configuration:


![Image Install](/img/fig-install-01.png)


## Requirements

+ Python 3.11 or later
+ optuna 3.5.0 or later
+ paramiko 3.4 or later
+ psycopg2-binary 2.9 or later
+ sysbench 1.0 or 1.1

## 1. Local Server Setup

### 1.1. Installing pg_tuner and Required Modules

Clone the pg_tuner repository from GitHub:

```
$ git clone https://github.com/s-hironobu/pg_tuner.git
$ cd pg_tuner
```

Install the required Python modules using pip:

```
$ pip install optuna paramiko psycopg2-binary
```

Install sqlite3 (Ubuntu/Debian):

```
$ sudo apt-get install -y sqlite3
```

### 1.2. Installing sysbench

sysbench is a scriptable multi-threaded benchmark tool.
Supported versions are 1.0 and 1.1. Using other versions might cause errors.

On Ubuntu/Debian:

1. Update package lists:
```
$ sudo apt-get update -y
```
2. Install sysbench:
```
$ sudo apt-get install -y sysbench
```
3. Verify installation:
```
$ which sysbench
```

OnmacOS:

1. Install Lua and LuaJIT using Homebrew:
```
$ brew install lua luajit
```
2. Clone the sysbench repository:
```
$ git clone https://github.com/akopytov/sysbench.git
```
3. Build and install sysbench:
```
$ ./autogen.sh
$ ./configure --with-pgsql --without-mysql
$ export MACOSX_DEPLOYMENT_TARGET=XX.XX  # Replace XX.XX with your target macOS version
$ make
$ make install
```
4. Verify installation:
```
$ which sysbench
```

### 1.3. Using pgbench (Optional)

pgbench is a simple benchmark tool included with PostgreSQL.

If you want to use pgbench, you need to install PostgreSQL on your local machine.

Note: If the remote server's PostgreSQL requires a password, set the PGPASSWORD environment variable before running pgbench commands.

```
export PGPASSWORD="your_password"
```

## 2. Remote Server Setup

### 2.1. Port Access

This guide assumes the remote server allows incoming connections on ports 22 (SSH) and 5432 (PostgreSQL) from other servers.

### 2.2. Installing and Configuring PostgreSQL

Assumptions:

The PostgreSQL base directory on the remote server is `/usr/local/pgsql`.

1. Clone the postgres repository from GitHub:
```
$ git clone https://github.com/postgres/postgres.git
$ cd postgres
```
2. Configure PostgreSQL installation:
```
$ ./configure --prefix=/usr/local/pgsql --without-icu
```
3. Build and install PostgreSQL:
```
$ make
$ sudo make install
```

#### 2.2.1. Installing pg_linux_stats

pg_tuner requires the [pg_linux_stats](https://github.com/s-hironobu/pg_linux_stats.git) extension.

1. Navigate to the contrib directory:
```
$ cd contrib
```
2. Clone the pg_linux_stats repository:
```
$ git clone https://github.com/s-hironobu/pg_linux_stats.git
$ cd pg_linux_stats
```
3. Build and install pg_linux_stats:
```
$ make
$ make install
```

#### 2.2.2. Configuring postgresql.conf

Before starting the PostgreSQL server, edit the postgresql.conf file and set the following parameters:
```
listen_addresses = '*'
include_if_exists = './conf.d/trial.conf'
shared_preload_libraries = 'pg_linux_stats'
```

Note: Replace `./conf.d/trial.conf` with the actual path to your configuration file if it's located elsewhere.

#### 2.2.3. Configuring pg_hba.conf

Edit the pg_hba.conf file to allow connections from specific IP addresses or networks. Here's an example configuration that allows local connections.

```
# IPv4 local connections:
host    all             all             192.168.128.0/24            trust
```

#### 2.2.4. mkdir conf.d

Make `conf.d`.

```
$ pwd
/usr/local/pgsql/data
$ mkdir conf.d
```
