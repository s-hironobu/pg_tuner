# Commands

## [1] SHOW

This command displays the configuration settings specified in your configuration file.

### Usage

```
pg_tuner.py show [--conf [conf.toml]]
```


## [2] CREATE

This command creates the benchmark tables on the remote PostgreSQL server.

### Usage

```
pg_tuner.py create [--conf [conf.toml]]
```


## [3] DROP

This command drops the benchmark tables on the remote PostgreSQL server.

### Usage

```
pg_tuner.py drop [--conf [conf.toml]]
```

## [4] BACKUP

This command Creates a backup of the database cluster before starting a trial.
This ensures consistent initial conditions for each trial run.

### Usage

```
pg_tuner.py backup [--conf [conf.toml]]
```

##### Backup Method:
The backup is created using the copy command, not a tar-based archiving tool.
This is because tar-based methods can be time-consuming for large database clusters.


## [5] CHECK

This command verifys the trial configuration.

### Usage

```
pg_tuner.py check [--conf [conf.toml]]
```

### Check Items

+ Accessibility to the remote server
+ PostgreSQL server configuration
+ Benchmark configuration


## [6] RUN

This command runs the trials to recommend the optimal configuration parameters.

### Usage

```
pg_tuner.py run [--conf [conf.toml]]
```


### Repository

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

Each trial directory (NNN) contains the following files:
+ **score.txt**: This file holds the score of this specific trial run. The score represents the performance metric used to evaluate each configuration.
+ **trial.conf**: This is the additional configuration file for PostgreSQL that was used in this particular trial.
+ **csv files**: These files contain detailed statistics collected during the trial (details below).


### Details of Collected Statistics

The following sections show examples of collected statistics and their corresponding SQL queries used to retrieve them.


#### Basic Statistics

#### 1. timestamp:

```
SELECT current_timestamp::timestamp(0);

```

**Example:**

```
$ cat data_repo/first_test/0000/timestamp.csv
current_timestamp
2024-04-22 22:23:58
2024-04-22 22:24:08
2024-04-22 22:24:18
2024-04-22 22:24:28
2024-04-22 22:24:38
2024-04-22 22:24:48
2024-04-22 22:24:58
2024-04-22 22:25:08
2024-04-22 22:25:18
2024-04-22 22:25:28
2024-04-22 22:25:38
2024-04-22 22:25:49

... snip ...
```

#### 2. numconnections:

```
SELECT sum(numbackends) AS numconnections FROM pg_stat_database;
```

**Example:**

```
$ cat data_repo/first_test/0000/numconnections.csv
numconnections
31
46
46
46
46
46
71
72
72
92
91
71
86
86
86
86

... snip ...
```

#### 3. checkpointer:

```
SELECT num_timed, num_requested, write_time, sync_time, buffers_written FROM pg_stat_checkpointer;
```

**Example:**

```
$ cat data_repo/first_test/0000/checkpointer.csv
num_timed,num_requested,write_time,sync_time,buffers_written
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5045,102997886.0,5581103.0,217314175
1362,5046,103039339.0,5587871.0,217344722
1362,5046,103039339.0,5587871.0,217344722
1362,5046,103039339.0,5587871.0,217344722
1362,5046,103039339.0,5587871.0,217344722
1362,5046,103039339.0,5587871.0,217344722

... snip ...
```

#### 4. bgwriter:

```
SELECT buffers_clean, maxwritten_clean, buffers_alloc FROM pg_stat_bgwriter;
```

**Example:**

```
$ cat data_repo/first_test/0000/bgwriter.csv
buffers_clean,maxwritten_clean,buffers_alloc
37614343,55638,586916859
37614343,55638,586957506
37618970,55641,586987762
37627436,55657,587006522
37638111,55689,587027532
37648085,55720,587045295
37657355,55750,587063779
37667243,55782,587112319
37677131,55814,587163930
37686710,55845,587214743
37692272,55863,587235372
37696289,55876,587249721
37700306,55889,587266349

... snip ...
```

#### 5. wal:

```
SELECT wal_records, wal_fpi, wal_bytes, wal_buffers_full, wal_write, wal_sync, wal_write_time, wal_sync_time FROM pg_stat_wal;
```

**Example:**

```
$ cat data_repo/first_test/0000/wal.csv
wal_records,wal_fpi,wal_bytes,wal_buffers_full,wal_write,wal_sync,wal_write_time,wal_sync_time
2306997450,262602947,2035547854455,225988,13698002,13348778,0.0,0.0
2307066911,262620286,2035692204830,225988,13698399,13349175,0.0,0.0
2307207971,262638722,2035854023990,225988,13699433,13350208,0.0,0.0
2307313099,262647229,2035932654602,225988,13699923,13350698,0.0,0.0
2307440957,262654081,2035999765365,225988,13700808,13351583,0.0,0.0
2307545334,262658078,2036041480955,225988,13701275,13352050,0.0,0.0
2307647709,262660964,2036073908427,225988,13701737,13352512,0.0,0.0
2307806851,262664882,2036119656337,225988,13702534,13353308,0.0,0.0
2307944926,262667437,2036152990789,225988,13703033,13353807,0.0,0.0
2308084581,262669251,2036180347661,225988,13703539,13354313,0.0,0.0
2308269040,262697775,2036415724941,225988,13703903,13354677,0.0,0.0
2308320453,262710019,2036515436370,225988,13704026,13354800,0.0,0.0
2308363251,262716492,2036569728278,225988,13704152,13354926,0.0,0.0
2308437677,262723993,2036635074113,225988,13704357,13355131,0.0,0.0
2308514188,262729322,2036683696440,225988,13704583,13355357,0.0,0.0
2308621906,262734667,2036735232755,225988,13704909,13355682,0.0,0.0
2308749979,262739387,2036783813488,225988,13705301,13356073,0.0,0.0

... snip ...
```


#### 6. autovacuum:

```
SELECT sum(reads) AS reads, sum(writes) AS writes, sum(writebacks) AS writebacks, sum(extends) AS extends, sum(hits) AS hits, sum(evictions) AS evictions, sum(reuses) AS reuses, sum(fsyncs) as fsyncs FROM pg_stat_io WHERE backend_type LIKE 'autovacuum%';
```

**Example:**

```
$ cat data_repo/first_test/0000/autovacuum.csv
reads,writes,writebacks,extends,hits,evictions,reuses,fsyncs
67629693,9989255,0,23812,326949374,762026,66559619,0
67629693,9989255,0,23812,326949374,762026,66559619,0
67629693,9989255,0,23812,326949374,762026,66559619,0
67629777,9989255,0,23812,326950783,762110,66559619,0
67629777,9989255,0,23812,326950783,762110,66559619,0
67629777,9989255,0,23812,326950783,762110,66559619,0
67629777,9989255,0,23812,326950783,762110,66559619,0
67634741,9992020,0,23812,326990759,762603,66564090,0
67636522,9992362,0,23812,327004324,762775,66565699,0
67643603,9995554,0,23812,327057807,763223,66572332,0

... snip ...
```

#### 7. io:

```
SELECT sum(reads) AS reads, sum(writes) AS writes, sum(writebacks) AS writebacks, sum(extends) AS extends, sum(hits) AS hits, sum(evictions) aS evictions, sum(reuses) AS reuses, sum(fsyncs) as fsyncs FROM pg_stat_io WHERE backend_type !~* '(autovacuum)|(checkpointer)|(background writer)';
```

**Example:**

```
$ cat data_repo/first_test/0000/io.csv
reads,writes,writebacks,extends,hits,evictions,reuses,fsyncs
586322067,47046767,978,945455,90491551350,527012341,975639,0
586361473,47046767,978,945838,90491834209,527012341,975639,0
586391832,47047161,978,946444,90492520456,527026483,975639,0
586409850,47047161,978,946812,90493086504,527044869,975639,0
586430773,47047602,978,947199,90493781894,527066179,975639,0
586449064,47047905,978,947508,90494394774,527084779,975639,0
586467108,47050310,978,947787,90495015806,527103102,975639,0
586514390,47071063,978,948258,90496113489,527150855,975639,0
586563753,47092898,978,948555,90497207447,527200515,975639,0
586613978,47115563,978,948782,90498320858,527250965,975639,0
586636515,47124591,978,948861,90498888568,527273584,975639,0
586651086,47129196,978,948881,90499240004,527288175,975639,0
586665817,47133729,978,948930,90499589743,527302956,975639,0
586690283,47140164,978,949015,90500250539,527327506,975639,0
586714599,47146628,978,949077,90500936341,527351884,975639,0

... snip ...
```


#### Linux Statistics (required [pg_linux_stats](https://github.com/s-hironobu/pg_linux_stats.git) module)

#### 1. vmstat:

```
SELECT * FROM pg_vmstat();
```

**Example:**

```
$ cat data_repo/first_test/0000/vmstat.csv
r,b,swpd,free,buff,cache,si,so,bi,bo,interrupts,cs,us,sy,id,wa,st
2,1,256,1360484,215492,5415808,0,0,12,2520,93,89,21,11,62,6,0
5,1,256,952736,215512,5744832,0,0,12,2521,93,89,21,11,62,6,0
2,1,256,792732,215524,5870804,0,0,12,2521,94,90,21,11,62,6,0
13,1,256,785164,215532,5874120,0,0,12,2522,94,90,21,11,62,6,0
0,1,256,780908,215540,5877172,0,0,12,2522,95,91,21,11,62,6,0
1,2,256,776624,215556,5879764,0,0,12,2522,95,92,21,11,62,6,0
25,2,256,680436,215568,5882044,0,0,12,2522,96,92,21,11,62,6,0
35,3,256,652760,215576,5886052,0,0,12,2523,96,93,21,11,62,6,0
24,1,256,648228,215588,5888664,0,0,12,2523,97,94,21,11,62,6,0
46,1,256,574060,215612,5890528,0,0,12,2523,98,95,21,11,62,6,0
76,4,256,454916,215720,5978584,0,0,12,2524,98,95,21,11,62,6,0
0,2,256,365336,215824,6079760,0,0,12,2525,98,96,21,11,62,6,0
0,2,256,251612,215872,6147484,0,0,12,2526,99,96,21,11,62,6,0
25,2,256,192384,215908,6198656,0,0,12,2527,99,97,21,11,62,6,0
61,3,256,138504,216244,6249504,0,0,12,2527,99,97,21,11,62,6,0
0,3,256,288288,216492,6102584,0,0,12,2527,100,98,21,11,62,6,0

... snip ...
```

#### 2. mpstat:

```
SELECT * FROM pg_mpstat() WHERE cpu = 'all';
```

**Example:**

```
$ cat data_repo/first_test/0000/mpstat.csv
cpu,usr,nice,sys,iowait,irq,soft,steal,guest,gnice,idle
all,20.91,0.0,7.34,6.08,0.0,3.56,0.0,0.0,0.0,62.11
all,20.91,0.0,7.34,6.08,0.0,3.56,0.0,0.0,0.0,62.11
all,20.91,0.0,7.34,6.08,0.0,3.56,0.0,0.0,0.0,62.1
all,20.92,0.0,7.34,6.08,0.0,3.56,0.0,0.0,0.0,62.1
all,20.92,0.0,7.34,6.08,0.0,3.56,0.0,0.0,0.0,62.09
all,20.92,0.0,7.35,6.08,0.0,3.56,0.0,0.0,0.0,62.08
all,20.93,0.0,7.35,6.08,0.0,3.56,0.0,0.0,0.0,62.08
all,20.93,0.0,7.35,6.09,0.0,3.56,0.0,0.0,0.0,62.07
all,20.94,0.0,7.35,6.09,0.0,3.57,0.0,0.0,0.0,62.06
all,20.94,0.0,7.35,6.09,0.0,3.57,0.0,0.0,0.0,62.05
all,20.94,0.0,7.35,6.09,0.0,3.57,0.0,0.0,0.0,62.05
all,20.95,0.0,7.35,6.09,0.0,3.57,0.0,0.0,0.0,62.04
all,20.95,0.0,7.35,6.1,0.0,3.57,0.0,0.0,0.0,62.03
all,20.95,0.0,7.36,6.1,0.0,3.57,0.0,0.0,0.0,62.03

... snip ...
```



#### 3. free:

```
SELECT * FROM pg_free();
```

**Example:**

```
$ cat data_repo/first_test/0000/free.csv
total,used,free,shared,buff,available,swap_total,swap_used,swap_free
8037212,1045932,1359980,673464,5631300,6011276,2097148,256,2096892
8037212,1125112,950724,1000152,5961376,5605236,2097148,256,2096892
8037212,1158404,792480,1120220,6086328,5452024,2097148,256,2096892
8037212,1162396,785164,1120328,6089652,5447940,2097148,256,2096892
8037212,1164096,780404,1120376,6092712,5446184,2097148,256,2096892
8037212,1165520,776372,1120368,6095320,5444784,2097148,256,2096892
8037212,1260424,679176,1120400,6097612,5349832,2097148,256,2096892
8037212,1287612,647972,1120452,6101628,5322600,2097148,256,2096892
8037212,1284984,647976,1120592,6104252,5325088,2097148,256,2096892
8037212,1357516,573556,1120580,6106140,5252576,2097148,256,2096892
8037212,1388496,454412,1123644,6194304,5218532,2097148,256,2096892
8037212,1376292,365336,1123660,6295584,5230720,2097148,256,2096892
8037212,1422496,251360,1123764,6363356,5184412,2097148,256,2096892
8037212,1430516,192132,1123780,6414564,5176376,2097148,256,2096892

... snip ...
```



#### 4. iostat:

```
SELECT sum(tps) AS tps, sum(kb_read_s) AS kb_read_s, sum(kb_wrtn_s) AS lb_wrtn_s, sum(kb_dscd_s) AS kb_dscd_s, sum(kb_read) AS kb_read, sum(kb_wrtn) AS kb_wrtn, sum(kb_dscd) AS kb_dscd  FROM pg_iostat() WHERE device NOT LIKE 'loop%';
```

**Example:**

```
$ cat data_repo/first_test/0000/iostat.csv
tps,kb_read_s,lb_wrtn_s,kb_dscd_s,kb_read,kb_wrtn,kb_dscd
423.4,45.39,9997.03,0.0,3005188,661814557,0
423.35,45.39,9999.3,0.0,3005188,662065541,0
423.39,45.38,10001.7,0.0,3005188,662325121,0
423.47,45.37,10002.52,0.0,3005188,662479737,0
423.59,45.37,10003.49,0.0,3005188,662645189,0
423.69,45.36,10003.86,0.0,3005188,662770505,0
423.79,45.35,10004.12,0.0,3005188,662888829,0
424.06,45.35,10006.47,0.0,3005188,663145289,0
424.16,45.34,10006.73,0.0,3005188,663263617,0
424.26,45.33,10007.01,0.0,3005188,663382441,0
424.42,45.33,10013.45,0.0,3005188,663912197,0
424.54,45.32,10017.71,0.0,3005188,664296185,0
424.65,45.31,10020.57,0.0,3005188,664586977,0

... snip ...
```


#### 5. netstat:

```
SELECT sum(rx_ok) AS rx_ok, sum(tx_ok) AS tx_ok FROM pg_netstat();
```

**Example:**

```
$ cat data_repo/first_test/0000/netstat.csv
rx_ok,tx_ok
745927980,696207085
746050091,696303910
746317893,696533695
746545125,696733801
746804460,696961058
747040250,697171743
747282117,697386189
747686877,697758256
748075853,698121733
748462760,698480173
748631456,698634810
748754199,698748595
748889821,698877526
749113206,699091679
749323477,699297644

... snip ...
```
