"""
The Test Case Base File for the Test engine
"""

from abc import abstractmethod, ABCMeta
from enum import IntEnum


class TestType(IntEnum):
    UNIT = 1
    SANITY = 2
    FEATURE = 4
    REGRESSION = 8
    SYSTEM = 16
    ALL = 255


class TestCaseBase(metaclass=ABCMeta):
    """
    The test case base class
    User should implement the below 3 methods:
        setup: for test setup
        test: The main test body
        cleanup: Clean the test
    """
    def __init__(self, reporter):
        self.reporter = reporter
        self._output_var = dict()
        self.setting = None
        self.logger = reporter.case_logger
        self.test_data_var = dict()
        self.result = None

    @abstractmethod
    def collect_resource(self, pool):
        """
        Collect Test Resource
        """
        pass

    @abstractmethod
    def setup(self, *args):
        pass

    @abstractmethod
    def test(self, *args):
        pass

    @abstractmethod
    def cleanup(self, *args):
        pass

    @property
    def output_var(self):
        """
        The test case output variable
        Can be collected by Test Engine
        :return:
        """
        return self._output_var

    def get_setting(self, setting_path, setting_file):
        """
        Get test case setting instance
        """
        for k,v in self.__class__.__dict__.items():
            if hasattr(v, "__base__") and v.__base__.__name__ == "TestSettingBase":
                self.setting = v(setting_path, setting_file)
                self.setting.load()
