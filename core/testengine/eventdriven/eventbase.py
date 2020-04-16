"""
事件驱动

事件的类定义
"""

from abc import ABCMeta, abstractmethod
from core.result.logger import logger
from threading import Lock
from enum import Enum


class EventStatus(Enum):
    IDlE = "Idle"
    WAITING = "Waiting"
    RUNNING = "Running"
    SUCCESS = "Success"
    FAIL = "Failure"
    ERROR = "Error"


class EventBase(metaclass=ABCMeta):
    """
    事件的基类
    """
    event_lock = Lock()
    name = ""

    def __init__(self, description="", **kwargs):
        self.description = description
        self.arguments = dict()
        self.job = None
        self.interval = kwargs.get("interval", 0)
        self.result = EventStatus.IDlE
        self.back_ground = False
        self.loop_count = 0
        self.log = kwargs.get("log", logger.register(f"Event_{self.name}"))
        self.need_lock = False
        self.reporter = None

    def run(self):
        if self.need_lock:
            self.lock()
        try:
            if not self.pre_check():
                self.log.error("Pre-check failed")
                self.result = EventStatus.FAIL
                return
            self.action()
        except Exception as ex:
            self.result = EventStatus.ERROR
            self.log.exception(ex)
        finally:
            try:
                self.final()
            except Exception as ex:
                self.log.exception(ex)
            if self.need_lock:
                self.unlock()

    @abstractmethod
    def action(self):
        pass

    def pre_check(self):
        return True

    def final(self):
        pass

    def lock(self):
        self.__class__.event_lock.acquire()

    def unlock(self):
        self.__class__.event_lock.release()
