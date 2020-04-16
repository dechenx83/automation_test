import json
import time
import os
import logging

from enum import Enum


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ResultType(Enum):
    PASS = "Passed"
    FAIL = "Failed"
    ERROR = "Errored"
    BLOCK = "Blocked"
    SKIP = "Skipped"
    INFO = "Information"


class StepEnd(Exception):
    def __init__(self, result):
        self.result = result


class NodeEntry:
    """
    代表一般节点，比如测试列表
    """
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb:
            self.message += str(exc_tb)

    def __init__(self, headline, parent=None, message="", update_action=None):
        self.headline = headline
        self.message = message
        self.parent = parent
        self.children = list()
        self.timestamp = time.localtime()
        self.update_action = update_action

    def start_node(self, headline, message=""):
        ret = NodeEntry(headline, parent=self, message=message, update_action=self.update_action)
        self.children.append(ret)
        if self.update_action is not None:
            self.update_action()
        return ret

    def start_case(self, headline):
        ret = CaseEntry(headline, parent=self)
        ret.update_action = self.update_action
        self.children.append(ret)
        if self.update_action is not None:
            self.update_action()
        return ret

    def get_json(self):
        json_obj = dict()
        json_obj["headline"] = self.headline
        json_obj["message"] = self.message
        json_obj['timestamp'] = time.strftime(TIME_FORMAT, self.timestamp)
        json_obj["children"] = list()
        for child in self.children:
            json_obj["children"].append(child.get_json())
        return json_obj

    def get_friend_print(self, indent=0):
        ret = "" * indent
        ret += self.__str__()
        for child in self.children:
            ret += child.get_friend_print(indent+4)
        return ret

    def __str__(self):
        return self.headline + "[" + time.strftime(TIME_FORMAT, self.timestamp) + "]" + os.linesep


class CaseEntry(NodeEntry):
    """
    代表测试用例的节点
    """
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.update_result()
            if self.result is None:
                self.result = ResultType.PASS
            if self.update_action:
                self.update_action()
            return
        if exc_type is StepEnd:
            self.result = exc_val.result
            if self.result != ResultType.PASS:
                self.message += exc_tb
        else:
            self.result = ResultType.ERROR
            self.message = str(exc_tb)
        if self.update_action:
            self.update_action()
        return True

    def __str__(self):
        return self.headline + "[" + time.strftime(TIME_FORMAT, self.timestamp) + "]"

    def _get_result_headline(self, width, indent, headline_max=59):
        self.update_result()
        head_str = self.__str__()
        if len(head_str) > headline_max:
            head_str = head_str[0, headline_max] + "..."
        space_count = width - indent - len(head_str)
        ret = (" " * indent) + head_str + ("-" * space_count) + self.result.value.upper()
        return ret

    def start(self, headline, message, prefix=None):
        entry = CaseStepEntry(headline=headline, parent=self, message=message)
        entry.update_action = self.update_action
        if prefix is not None:
            entry.step_prefix = prefix
        self.children.append(entry)
        if self.update_action is not None:
            self.update_action()
        return entry

    def passed(self, message):
        self.message += message + os.linesep
        if self.update_action is not None:
            self.update_action()
        raise StepEnd(ResultType.PASS)

    def failed(self, message):
        self.message += message + os.linesep
        if self.update_action is not None:
            self.update_action()
        raise StepEnd(ResultType.FAIL)

    def blocked(self, message):
        self.message += message + os.linesep
        if self.update_action is not None:
            self.update_action()
        raise StepEnd(ResultType.BLOCK)

    def skipped(self, message):
        self.message += message + os.linesep
        if self.update_action is not None:
            self.update_action()
        raise StepEnd(ResultType.SKIP)

    def errored(self, message):
        self.message += message + os.linesep
        if self.update_action is not None:
            self.update_action()
        raise StepEnd(ResultType.ERROR)

    def info(self, message):
        if self.update_action is not None:
            self.update_action()
        self.message += "INFO: " + message + os.linesep

    def __init__(self, headline, parent=None, message=""):
        super().__init__(headline, parent, message)
        self.result = None

    def get_json(self):
        self.update_result()
        json_obj = super().get_json()
        json_obj['result'] = self.result.value
        return json_obj

    def get_friend_print(self, indent=0):
        ret = self._get_result_headline(100, indent, ) + os.linesep
        for child in self.children:
            ret += child.get_friend_print(indent + 4)
        return ret

    def update_result(self):
        if not any(self.children):
            return
        has_error = False
        has_failed = False
        has_block = False
        has_pass = False

        for child in self.children:
            child.update_result()
            if child.result == ResultType.ERROR:
                has_error = True
            elif child.result == ResultType.FAIL:
                has_failed = True
            elif child.result == ResultType.BLOCK:
                has_block = True
            elif child.result == ResultType.PASS:
                has_pass = True

        if has_block:
            self.result = ResultType.BLOCK
        elif has_error:
            self.result = ResultType.ERROR
        elif has_failed:
            self.result = ResultType.FAIL
        elif has_pass:
            self.result = ResultType.PASS
        else:
            self.result = ResultType.INFO


class CaseStepEntry(CaseEntry):
    """
    测试步骤节点
    """
    def __init__(self, headline, parent=None, message="", step_prefix="", step_no=1, _continue=False):
        super().__init__(headline, parent, message)
        self.result = None
        self.step_prefix = step_prefix
        self.step_no = step_no
        self._continue = _continue

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.update_result()
            if self.result is None:
                self.result = ResultType.PASS
            if self.update_action:
                self.update_action()
            return True
        if exc_type is StepEnd:
            self.result = exc_val.result
            if self.result == ResultType.PASS:
                return True
            else:
                return self._continue
        else:
            self.result = ResultType.ERROR
            self.message += str(exc_tb)
            return self._continue

    def __str__(self):
        if self.step_prefix == "COLLECT_RESOURCE" or self.step_prefix == "SETUP" or self.step_prefix == "TEST" or self.step_prefix == "CLEANUP":
            headline = self.step_prefix + "[" + time.strftime(TIME_FORMAT, self.timestamp) + "]"
        else:
            headline = "STEP-" + self.step_prefix + str(self.step_no) + ": " + self.headline + \
                       "[" + time.strftime(TIME_FORMAT, self.timestamp) + "]"
        return headline

    def start(self, headline, message, _continue=False, prefix=None):
        entry = CaseStepEntry(headline=headline, parent=self, message=message, _continue=_continue)
        if prefix is not None:
            entry.step_prefix = prefix
        elif self.step_prefix == "SETUP" or self.step_prefix == "TEST" or self.step_prefix == "CLEANUP" or self.step_prefix == "COLLECT_RESOURCE":
            entry.step_prefix = ""
        else:
            entry.step_prefix = self.step_prefix + str(self.step_no) + "-"

        if any(self.children):
            entry.step_no = self.children[-1].step_no + 1
        entry.update_action = self.update_action
        if self.update_action is not None:
            self.update_action()
        self.children.append(entry)
        return entry

    def get_json(self):
        json_obj = super().get_json()
        if self.step_prefix == "SETUP" or self.step_prefix == "TEST" or self.step_prefix == "CLEANUP":
            json_obj['headline'] = self.step_prefix
        else:
            json_obj['headline'] = "STEP-" + self.step_prefix + str(self.step_no) + self.headline
        return json_obj


class StepReporter:
    """
    测试结果，用单例实现
    """
    instance = None
    path = ""

    json_path = ""
    txt_path = ""

    @classmethod
    def get_instance(cls, logger):
        # cls.path = ("%s/testresult/%s/%s/%s" % (FwConfig.result_path,
        #                                                        RuntimeData.uuid,
        #                                                        FwConfig.branch,
        #                                                        FwConfig.app_num))
        cls.path = "/home/emc/"
        cls.json_path = os.path.join(cls.path, "step_result.json")
        cls.txt_path = os.path.join(cls.path, "step_result.txt")
        if cls.instance is None:
            return StepReporter(logger)
        else:
            return cls.instance

    def __init__(self, logger):
        self.logger = logger
        self.case_node = None
        self.root = NodeEntry(headline="Test Result")

        self.recent_node = self.root

    def update_file(self):
        with open(self.json_path, "w") as jsonfile:
            json.dump(self.root.get_json(), jsonfile, indent=4)
        with open(self.txt_path, "w") as txtfile:
            txtfile.write(self.root.get_friend_print())

    def start_node(self, headline, message):
        ret = NodeEntry(headline, parent=self.root, message=message)
        self.root.children.append(ret)
        return ret

    def print(self):
        print(self.root.get_friend_print())


if __name__ == "__main__":
    logger = logging.getLogger("单元测试")
    rr = StepReporter.get_instance(logger)
    with rr.root.start_node("测试列表") as testlist:
        with testlist.start_case("test_feature_001") as case:
            with case.start(headline="", message="", prefix="SETUP") as step:
                with step.start("设置浏览器", "启动浏览器，选择chrome") as substep:
                    substep.passed("成功设置浏览器")
                with step.start("登录系统", "输入用户名密码") as substep:
                    substep.passed("登录成功")
            with case.start(headline="", message="", prefix="TEST") as step:
                with step.start("测试步骤1", "第一个测试步骤") as substep:
                    with substep.start("一个pass的子步骤", "") as ssubstep:
                        pass
                with step.start("一个异常的步骤", "", _continue=True) as substep:
                    1/0 # 造成异常
                with step.start("继续测试步骤", "") as substep:
                    substep.passed("成功")
            with case.start(headline="", message="", prefix="CLEANUP") as step:
                step.passed("执行清理")



    print(rr.root.get_friend_print())

