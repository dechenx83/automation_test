"""
Test Engine
"""
import importlib
import threading
import os
from enum import Enum
from core.case.precondition import IsTestCaseType, IsTestCasePriority, IsPreCasePassed, IsHigherPriorityPassed
from core.config.setting import static_setting, SettingBase
from core.result.reporter import ResultReporter, StepResult
from core.case.base import TestCaseBase
from core.resource.error import ResourceNotMeetConstraintError, ResourceLoadError, ResourceNotRelease
from core.resource.pool import ResourcePool
from core.testengine.testlist import TestList
from core.config.logicmodule import ModuleManager, ModuleType
from core.result.logger import logger
from core.utilities.time import get_time_stamp


@static_setting.setting("CaseRunner")
class CaseRunnerSetting(SettingBase):
    """
    The case runner setting
    """
    default_case_setting_path = os.path.join(os.environ['HOME'], "test_settings")
    log_path = os.path.join(os.environ['HOME'], "ats_logs")
    case_log = os.path.join(os.environ['HOME'], "case_logs")
    log_level = "INFO"


class CaseImportError(Exception):
    def __init__(self, msg, inner_ex=None):
        super().__init__(msg)
        self.inner_ex = inner_ex


class TestEngineNotReadyError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class RunningStatus(Enum):
    Idle = 1
    Running = 3


class CaseRunner():
    """
    测试用例执行器
    """
    def __init__(self):
        self.resource_pool = None
        self.list_setting = None
        self.test_list = None
        self.case_tree = dict()
        self.priority_list = list()
        self.pre_conditions = list()
        self.status = RunningStatus.Idle
        self.module_manager = ModuleManager()
        self.running_thread = None
        self.logger = logger.register("CaseRunner", filename=
                                      os.path.join(CaseRunnerSetting.log_path, "CaseRunner.log"),
                                      default_level=CaseRunnerSetting.log_level)
        self.result_report = ResultReporter(self.logger)
        self.logger.info("执行器装载完毕")
        self.case_log_folder = None
        self.case_result = dict()

    def load_resource(self, file_name, username):
        self.resource_pool = ResourcePool()
        try:
            self.resource_pool.load(file_name, username)
            for key, device in self.resource_pool.topology.items():
                if device.pre_connect:
                    device_instance = device.get_comm_instance()
                    if hasattr(device_instance, "connect"):
                        device_instance.connect()
        except ResourceLoadError as rle:
            #资源文件读取错误
            self.logger.exception(rle)
            self.resource_pool = None
        except ResourceNotRelease as rnr:
            #资源文件被占用
            self.logger.exception(rnr)
            self.resource_pool = None
        except Exception as ex:
            self.logger.exception(ex)
            self.resource_pool = None
        self.logger.info("测试资源装载完毕")

    @property
    def resource_ready(self):
        return self.resource_pool is not None

    @property
    def test_list_ready(self):
        return self.test_list is not None

    def load_test(self, test_name) -> TestCaseBase:
        """
        实例化测试用例
        """
        #获取测试用例的模块名和类名
        case_module_name = ".".join(test_name.split(".")[0: -1])
        case_name = test_name.split(".")[-1]
        try:
            case_module = importlib.import_module(case_module_name)
            return getattr(case_module, case_name)(self.result_report)
        except Exception as ex:
            # 导入测试用例失败，抛出异常
            raise CaseImportError("Failed to Import Test Case %s" % test_name, ex)

    def set_test_list(self, test_list: TestList):
        """
        #装载测试列表
        """
        self.test_list = test_list
        self.list_setting = None
        self.case_tree.clear()
        self._import_list_case(self.case_tree, self.test_list)
        if any(self.test_list.setting.priority_to_run):
            self.priority_list = self.test_list.setting.priority_to_run
        self.logger.info("测试列表装载完毕")

    def start(self):
        """
        测试引擎开始执行
        """
        if self.status == RunningStatus.Running:
            return
        if not self.resource_ready:
            raise TestEngineNotReadyError("测试引擎未准备就绪，测试资源未装载")
        if self.test_list is None:
            raise TestEngineNotReadyError("测试引擎未准备就绪，测试列表未装载")
        self.status = RunningStatus.Running
        self.case_log_folder = os.path.join(CaseRunnerSetting.case_log, get_time_stamp())
        self.running_thread = threading.Thread(target=self.__main_test_thread)
        self.running_thread.start()

    def wait_for_test_done(self):
        self.running_thread.join()

    def run_case_lcm(self, test: TestCaseBase):
        """
        执行测试用例生命周期管理
        这个方法应该在子线程被运行
        """
        self.__init_precondition(test)
        if not self.__pre_check(test):
            return
        self.module_manager.run_module(ModuleType.PRE)
        self.module_manager.run_module(ModuleType.PARALLEL)
        self.__run_case(test)
        self.module_manager.stop_module()
        self.module_manager.run_module(ModuleType.POST)

    def _import_list_case(self, case_tree_node, test_list, log_path=None):
        """
        递归导入测试列表中的测试用例
        """
        case_log_path = test_list.test_list_name
        if log_path:
            case_log_path = log_path + "/" + case_log_path
        case_tree_node["list_name"] = test_list.test_list_name
        case_tree_node["test_cases"] = list()
        for testcase in test_list.test_cases:
            if testcase.strip() == "":
                continue
            case_descriptor = dict()
            case_entry = testcase.split(",")
            case_name = case_entry[0]
            case_setting_file = ""
            if len(case_entry) > 1:
                case_setting_file = case_entry[1]
            try:
                # 导入测试用例
                case_descriptor['case'] = self.load_test(case_name)
                case_descriptor['case_name'] = case_name.split(".")[-1]
                case_descriptor['log_path'] = case_log_path
                case_descriptor['setting_file'] = case_setting_file
                # 设置测试用例配置文件路径
                if test_list.setting.case_setting_path:
                    case_descriptor['setting_path'] = test_list.setting.case_setting_path
                else:
                    case_descriptor['setting_path'] = CaseRunnerSetting.default_case_setting_path
                case_priority = getattr(case_descriptor['case'], "priority", 999)
                if case_priority not in self.priority_list:
                    self.priority_list.append(case_priority)
            except CaseImportError as cie:
                # 测试用例导入失败
                self.logger.error(f"不能导入测试用例{case_name}")
                self.logger.exception(cie)
            case_tree_node['test_cases'].append(case_descriptor)
        case_tree_node['sub_list'] = list()
        for sub_list in test_list.sub_list:
            sub_list_dict = dict()
            case_tree_node['sub_list'].append(sub_list_dict)
            self._import_list_case(sub_list_dict, sub_list, log_path=case_log_path)

    def __init_precondition(self, test: TestCaseBase):
        self.pre_conditions.clear()
        self.pre_conditions.append(IsTestCaseType(self.test_list.setting.run_type))
        if any(self.test_list.setting.priority_to_run):
            self.pre_conditions.append(IsTestCasePriority(self.test_list.setting.priority_to_run))
        if any(test.pre_tests):
            self.pre_conditions.append(IsPreCasePassed(self.case_result))
        self.pre_conditions.append(IsHigherPriorityPassed(test.priority, self.case_result))

    def __pre_check(self, test:TestCaseBase):
        for condition in self.pre_conditions:
            if not condition.is_meet(test, self.result_report):
                self.result_report.add(StepResult.INFO, f"{test.__class__.__name__}不能执行！")
                return False
        return True

    def __get_case_log(self, path, case_name):
        log_path = os.path.join(self.case_log_folder, path, f"{case_name}.log")
        return logger.register(case_name, filename=log_path, is_test=True)


    def __main_test_thread(self):
        try:
            self.__run_test_list(self.case_tree)
        finally:
            self.status = RunningStatus.Idle

    def __run_test_list(self, testlist):
        self.result_report.add_list(testlist['list_name'])
        for test in testlist['test_cases']:
            test["case"].get_setting(test["setting_path"], test["setting_file"])
            self.result_report.case_logger = self.__get_case_log(test['log_path'], test['case_name'])
            self.case_result[test["case_name"]] = dict()
            self.case_result[test["case_name"]]['priority'] = test["case"].priority
            self.case_result[test["case_name"]]['result'] = False
            self.run_case_lcm(test['case'])
            self.result_report.case_logger = None
            logger.unregister(test['case_name'])
        for list in testlist['sub_list']:
            self.__run_test_list(list)
        self.result_report.end_list()

    def __run_case(self, test: TestCaseBase):
        """
        测试用例执行线程
        """
        self.result_report.add_test(test.__class__.__name__)
        _continue = True
        try:
            self.result_report.add_step_group("收集测试资源")
            test.collect_resource(self.resource_pool)
        except ResourceNotMeetConstraintError as rnce:
            self.result_report.add(StepResult.EXCEPTION, "测试资源不满足条件", str(rnce))
            _continue = False
        except Exception as e:
            self.result_report.add(StepResult.EXCEPTION, "捕获异常！", str(e))
            _continue = False
        finally:
            self.result_report.end_step_group()

        if not _continue:
            self.result_report.end_test()
            return

        try:
            self.result_report.add_step_group("SETUP")
            test.setup()
            self.result_report.end_step_group()
        except Exception as e:
            self.result_report.add(StepResult.EXCEPTION, "捕获异常!", str(e))
            self.result_report.end_step_group()
            self.__call_cleanup(test)
            return

        try:
            self.result_report.add_step_group("TEST")
            test.test()
            self.result_report.end_step_group()
        except Exception as e:
            self.result_report.add(StepResult.EXCEPTION, "捕获异常!", str(e))
            self.result_report.end_step_group()
            self.__call_cleanup(test)
            return
        self.__call_cleanup(test)

    def __call_cleanup(self, test: TestCaseBase):
        """
        执行清除操作
        """
        try:
            self.result_report.add(StepResult.INFO, "CLEANUP")
            test.cleanup()
        except Exception as e:
            self.result_report.add(StepResult.EXCEPTION, "EXCEPTION!", str(e))
        finally:
            self.result_report.pop()
            self.case_result[test.__class__.__name__]['result'] = \
                self.result_report.recent_case.status == StepResult.PASS
            self.result_report.end_test()

