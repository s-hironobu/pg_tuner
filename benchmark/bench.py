"""
bench.py

  Copyright (c) 2024, Hironobu Suzuki @ interdb.jp
"""

from abc import ABC, ABCMeta, abstractmethod

class Benchmark:

    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def create_bench(self):
        pass

    @abstractmethod
    def drop_bench(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def parse_result(self):
        pass

    @abstractmethod
    def get_col_name(self):
        pass
