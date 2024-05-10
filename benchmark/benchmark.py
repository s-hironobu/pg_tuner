"""
benchmark.py

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

from abc import ABC, ABCMeta, abstractmethod

class Benchmark(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def check(self):
        pass

    @classmethod
    @abstractmethod
    def create_bench(self):
        pass

    @classmethod
    @abstractmethod
    def drop_bench(self):
        pass

    @classmethod
    @abstractmethod
    def run(self):
        pass

    @classmethod
    @abstractmethod
    def parse_result(self):
        pass

    @classmethod
    @abstractmethod
    def get_col_name(self):
        pass
