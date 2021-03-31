import os
from enum import IntEnum
from threading import Event, Lock
from functools import wraps
from core.utilities.time import get_local_time


class StepResult(IntEnum):
    """
    表示节点的状态
    """
    INFO = 1
    PASS = 2
    FAIL = 4
    EXCEPTION = 8
    WARNING = 16
    ERROR = 32


class NodeType(IntEnum):
    """
    表示节点的类型
    """
    Step = 1
    Case = 2
    TestList = 4
    Other = 256


class ResultNode:
    """
    测试结果节点
    """
    def __init__(self, header, status=None, message="", parent=None,
                 node_type=NodeType.Other):
        self.status = StepResult.INFO if status is None else status
        self.header = header
        self.message = message
        self.children = list()
        self.parent = parent
        self.type = node_type
        self.timestamp = get_local_time()
        self.log = None

    def add_child(self, header, status=StepResult.INFO, message="",
                  node_type=NodeType.Other):
        """
        添加新的子节点并返回该节点
        """
        new_node = ResultNode(header, message=message, parent=self,
                              node_type=node_type)
        # 在case或者step类型的节点中，只允许类型是Step
        if self.type in [NodeType.Step, NodeType.Case]:
            new_node.type = NodeType.Step
        self.children.append(new_node)
        new_node.set_status(status)
        return new_node

    def set_status(self, status):
        """
        设置当前节点的状态，并且同时更新父节点的状态
        """
        if self.type == NodeType.Other:
            # 对于类型是非case或者是step的节点，不作状态设置
            return
        if status == StepResult.INFO:
            return
        if self.status in [StepResult.INFO, StepResult.PASS]:
            self.status = status
        self.parent.set_status(status)

    def add(self, status, header, message=""):
        """
        简化的add方法，提供给事件驱动
        """
        self.add_child(header, status, message, NodeType.Step)
        if self.log:
            self.log.info(header)

    def get_test_point_stats(self):
        stats_pass = 0
        stats_fail = 0
        stats_error = 0
        stats_warning = 0
        stats_exception = 0
        for child in self.children:
            child_stats = child.get_test_point_stats()
            stats_pass += child_stats[0]
            stats_fail += child_stats[1]
            stats_error += child_stats[2]
            stats_warning += child_stats[3]
            stats_exception += child_stats[4]
        if not any(self.children):
            if self.status == StepResult.PASS:
                stats_pass = 1
            elif self.status == StepResult.FAIL:
                stats_fail = 1
            elif self.status == StepResult.ERROR:
                stats_error = 1
            elif self.status == StepResult.WARNING:
                stats_warning = 1
            elif self.status == StepResult.EXCEPTION:
                stats_exception = 1
        return stats_pass, stats_fail, stats_error, stats_warning, stats_exception

    def get_test_case_stats(self):
        stats_pass = 0
        stats_fail = 0
        stats_error = 0
        stats_warning = 0
        stats_exception = 0
        if self.type == NodeType.Case:
            if self.status == StepResult.PASS:
                stats_pass = 1
            elif self.status == StepResult.FAIL:
                stats_fail = 1
            elif self.status == StepResult.ERROR:
                stats_error = 1
            elif self.status == StepResult.WARNING:
                stats_warning = 1
            elif self.status == StepResult.EXCEPTION:
                stats_exception = 1
        else:
            for child in self.children:
                child_stats = child.get_test_case_stats()
                stats_pass += child_stats[0]
                stats_fail += child_stats[1]
                stats_error += child_stats[2]
                stats_warning += child_stats[3]
                stats_exception += child_stats[4]
        return stats_pass, stats_fail, stats_error, stats_warning, stats_exception

    @property
    def is_leaf(self):
        return any(self.children)

    def to_dict(self):
        """
        将结果节点输出成字典结构
        """
        rv = dict()
        rv["header"] = self.header
        rv["status"] = self.status.value
        rv["message"] = self.message
        rv["type"] = self.type.value
        rv["children"] = list()
        rv["timestamp"] = self.timestamp
        for child in self.children:
            rv["children"].append(child.to_dict())
        return rv

    def to_text(self, indent=0):
        """
        将结果生成文本类型的结构
        """
        rv = f"{self._get_intent(indent)}[{self.timestamp}]"
        if self.type == NodeType.Case:
            rv += "[TestCase] "
        if self.type == NodeType.TestList:
            rv += "[Test List] "
        rv += self.header
        if self.type in [NodeType.Case, NodeType.Step]:
            rv += self._get_dot_line(rv, 80)
            rv += self.status.name
        rv += os.linesep
        if self.message:
            rv += self._get_intent(indent)
            rv += f"Description:{self.message}{os.linesep}"
        for child in self.children:
            rv += child.to_text(indent+1)
        return rv

    def _get_intent(self, indent):
        return "+" * (indent * 2)

    def _get_dot_line(self, line, line_max):
        if len(line) >= line_max:
            return line
        else:
            return "-" * (line_max - len(line))


def locker(lock):
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                lock.acquire()
                return func(*args, **kwargs)
            finally:
                lock.release()
        return inner
    return outer


class ResultReporter:

    my_lock = Lock()

    def __init__(self, logger):
        self.halt_on_failure = False
        self.halt_on_exception = False
        self.halt_event = Event()
        self.root = ResultNode("Root")
        self.recent_case = None
        self.recent_node = self.root
        self.recent_list = None
        self.logger = logger
        self.case_logger = None

    def search_result(self, case_name):
        """
        搜索给定的测试用例名称的测试结果
        """
        self._search_result(self.root, case_name)

    def _search_result(self, node, case_name):
        if node.type == NodeType.Step:
            return None
        for child in node.children:
            if child.header == case_name:
                return child.status
            else:
                rv = self._search_result(child, case_name)
                if rv:
                    return rv
        else:
            return None

    @locker(my_lock)
    def add_node(self, header, message="", status=StepResult.INFO, node_type=NodeType.Other):
        self.recent_node = self.recent_node.add_child(header=header,
                                                      status=status,
                                                      message=message,
                                                      node_type=node_type)
        self._log_info(f"Result Node {header}, Message: {message}")
        return self.recent_node

    @locker(my_lock)
    def pop(self):
        if self.recent_node.parent:
            self.recent_node = self.recent_node.parent

    @locker(my_lock)
    def add_test(self, case_name):
        self.recent_node = self.recent_node.add_child(header=case_name,
                                                      node_type=NodeType.Case)
        self.recent_case = self.recent_node
        self._log_info(f"[Test Case] {case_name}")

    @locker(my_lock)
    def end_test(self):
        if self.recent_case is None:
            return
        self.recent_node = self.recent_case.parent
        self.recent_case = None

    @locker(my_lock)
    def add_list(self, list_name):
        self.recent_node = self.recent_node.add_child(header=list_name,
                                                      node_type=NodeType.TestList)
        self.recent_list = self.recent_node
        self._log_info(f"[Test list] {list_name}")

    @locker(my_lock)
    def end_list(self):
        if self.recent_list is None:
            return
        self.recent_node = self.recent_list.parent
        self.recent_list = None

    @locker(my_lock)
    def add_step_group(self, group_name):
        self.recent_node = self.recent_node.add_child(header=group_name,
                                                      node_type=NodeType.Step)
        self._log_info(f"[Test Step Group] {group_name}")

    @locker(my_lock)
    def add_event_group(self, group_name):
        rv = self.recent_node.add_child(header=group_name,
                                        node_type=NodeType.Step)
        rv.log = self.case_logger if self.case_logger is not None else self.logger
        self._log_info(f"[Event] {group_name}")
        return rv

    @locker(my_lock)
    def end_step_group(self):
        if self.recent_node.parent:
            self.recent_node = self.recent_node.parent

    def add_precheck_result(self, result, headline):
        pass

    def is_high_priority_passed(self, priority):
        pass

    @locker(my_lock)
    def add(self, status: StepResult, headline, message=""):
        self.recent_node.add_child(header=headline,
                                   message=message,
                                   node_type=NodeType.Step,
                                   status=status)
        self._log_info("Step: " + headline)
        self._log_info("Message" + message)
        self.halt_event.clear()
        if status == StepResult.FAIL and self.halt_on_failure:
            self.halt_event.wait()
        elif status == StepResult.EXCEPTION and self.halt_on_exception:
            self.halt_event.wait()

    def _log_info(self, message):
        if self.case_logger:
            self.case_logger.info(message)
        else:
            self.logger.info(message)

if __name__ == "__main__":
    import logging
    rr = ResultReporter(logging)
    # 添加一个测试列表节点
    rr.add_list("Test List 1")

    # 添加一个测试用例节点
    rr.add_test("Test Case 1")

    # 添加一个SETUP步骤节点
    rr.add_step_group("SETUP")
    # 添加一些步骤
    rr.add(StepResult.PASS, "Do Something Setup", "I'm doing something")
    rr.end_step_group()

    # 添加一个测试步骤节点
    rr.add_step_group("TEST")

    rr.add_step_group("Login to website")
    rr.add(StepResult.PASS, "Input Username", "Username is admin")
    rr.add(StepResult.PASS, "Input Password", "Password is admin")
    rr.add(StepResult.FAIL, "Login", "Login is failed")
    rr.end_step_group()

    # 这里我们少了一个end_group, 但是end_test会把我们带回正确的位置。
    rr.end_test()

    # 第二个测试用例
    rr.add_test("Test Case 2")
    rr.add_step_group("SETUP")
    rr.add(StepResult.PASS, "Do Something Setup", "I'm doing something")
    rr.end_step_group()

    rr.add_step_group("TEST")
    rr.add_step_group("Login to website")
    rr.add(StepResult.PASS, "Input Username", "Username is admin")
    rr.add(StepResult.PASS, "Input Password", "Password is admin")
    rr.end_step_group()
    rr.end_test()
    rr.add_list("Sub Test List")
    rr.add_test("Test Case 3")
    rr.add_step_group("SETUP")
    rr.add(StepResult.PASS, "Do Something Setup", "I'm doing something")
    rr.end_step_group()

    rr.add_step_group("TEST")
    rr.add_step_group("Login to website")
    rr.add(StepResult.PASS, "Input Username", "Username is admin")
    rr.add(StepResult.PASS, "Input Password", "Password is admin")
    rr.end_step_group()
    rr.end_test()
    rr.end_list()

    rr.add_test("Test Case 4")
    rr.add_step_group("SETUP")
    rr.add(StepResult.PASS, "Do Something Setup", "I'm doing something")
    rr.end_step_group()

    rr.add_step_group("TEST")
    rr.add_step_group("Login to website")
    rr.add(StepResult.PASS, "Input Username", "Username is admin")
    rr.add(StepResult.PASS, "Input Password", "Password is admin")
    rr.end_step_group()
    rr.end_test()

    rr.end_list()

    print(rr.root.to_text())
    tp_stats = rr.root.get_test_point_stats()
    print(f"PASS: {tp_stats[0]}, FAIL: {tp_stats[1]}")
    print(f"ERROR: {tp_stats[2]}, WARNING: {tp_stats[3]}, EXCEPTION: {tp_stats[4]}")
    tc_stats = rr.root.get_test_case_stats()
    print(f"PASS: {tc_stats[0]}, FAIL: {tc_stats[1]}")
    print(f"ERROR: {tc_stats[2]}, WARNING: {tc_stats[3]}, EXCEPTION: {tc_stats[4]}")

    # import json
    # print(json.dumps(rr.root.to_dict(), indent=4))
