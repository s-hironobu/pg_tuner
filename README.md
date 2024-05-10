# pg_tuner

`pg_tuner` is another automated PostgreSQL database parameter tuning tool based on the Bayesian Optimization technique, utilizing the [Optuna](https://optuna.org/) library.


As mentioned in the [References](https://github.com/s-hironobu/pg_tuner#references) section, several RDBMS tuning tools already exist.

Here are some key features of `pg_tuner`:

+ **PostgreSQL-specific:** Designed specifically for tuning PostgreSQL databases.

+ **Scenario-Based Workloads:** Simulates realistic workloads by scheduling tasks (e.g., Multiple tasks can run concurrently. Task A starts at 1 minute, runs for 10 minutes; Task B starts at 5 minutes, runs for 8 minutes, etc.)

+ **Extensible Benchmark Support:** Currently supports [sysbench](https://github.com/akopytov/sysbench) and [pgbench](https://www.postgresql.org/docs/current/pgbench.html), but allows adding custom benchmarks through similar classes.

+ **Comprehensive Monitoring:** Captures not only RDBMS statistics but also OS (Linux only) statistics by leveraging the [pg_linux_stats](https://github.com/s-hironobu/pg_linux_stats) module (optional).


## Installation

See [README: Installation](./README-install.md).

## Quick Start

See [README: Quick Start](./README-quick-start.md).

## Configuration

See [README: Configulation](./README-config.md).


## Commands

See [README: Commands](./README-command.md).


## History

Initially, I was looking for a set of PostgreSQL statistics to utilize as training data for automating PostgreSQL management through reinforcement learning and deep learning techniques.
However, it is very difficult for an individual to acquire a large volume of statistical information about practical systems.
As a result, I decided to develope a data generator along with a set of tools for collecting statistical information.


Later, when I was considering this tool, I realized its potential to not only generate data but also optimize PostgreSQL configuration parameters.

Many parameter optimization tools find the best settings through numerous trials, essentially discarding the results from all but the winning configuration.
In contrast, my tool collects statistics from all trials and, as a by-product, identifies the optimal configuration parameters.


All the data collected is valuable for my purposes.
For example, statistical information from trials with poor performance due to parameter tuning failures can be used as training data for diagnosing anomalies in machine learning or reinforcement learning.


The name `pg_tuner` reflects the functionality of the by-product rather than its original purpose.


## References


- Bayesian Optimization (BO) based Models:
  + [postgres_opttune](https://github.com/ssl-oyamata/postgres_opttune)
  + [Ottertune](https://ottertune.com/) [paper](https://www.cs.cmu.edu/~ggordon/van-aken-etal-parameters.pdf)
  + [Tuneful](https://research-information.bris.ac.uk/ws/portalfiles/portal/252529452/untitled.pdf)
  + [ResTune](https://www.cl.cam.ac.uk/~ey204/teaching/ACS/R244_2023_2024/papers/ZHANG_SIGMOD_2021.pdf) (BO + meta-learning)
  + [RelM](https://arxiv.org/abs/2002.11780) (BO + Deep Distributed Policy Gradient:DDPG)
  + [CGPTuner](https://15799.courses.cs.cmu.edu/spring2022/papers/07-knobs2/p1401-cereda.pdf) (Contextual Gaussian Process Bandit Optimisation:CGPBO, extension of BO)


- Reinforcement Learning (RL) based models:
  + [DMSConfig](https://arxiv.org/pdf/2302.09146.pdf)
  + [CDBTune](https://github.com/HustAIsGroup/CDBTune/blob/master/An%20End-to-End%20Automatic%20Cloud%20Database%20Tuning%20System%20Using%20Deep%20Reinforcement%20Learning.pdf)
  + [QTune](https://www.vldb.org/pvldb/vol12/p2118-li.pdf)


## Change Log

10.May.2014: Version 1.0 Released.
