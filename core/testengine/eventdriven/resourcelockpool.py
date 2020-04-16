from core.result.logger import logger
from core.utilities.time import get_local_time
from threading import Event, Thread
import time


class ResourceIsLocked(Exception):
    def __init__(self, resource, event, timeout):
        super().__init__(f"Resource {resource} is locked by {event} and not released in {timeout}s")


class InvalidLockOperation(Exception):
    pass


class ResourceLockPool:
    """
    资源锁池
    """
    def __init__(self, log=None):
        self.log = log if log is not None else logger.register("ResourceLockPool", default_level="INFO")
        self.resource = dict()

    def lock(self, resource, event, timeout=60):
        """
        锁定资源
        """
        if resource.name in self.resource:
            lock = self.resource[resource.name]['lock']
            event_name = self.resource[resource.name]['event']
            if not lock.wait(timeout):
                raise ResourceIsLocked(resource.name, event_name, timeout)
        self.log.info(f"Lock {resource.name}: time: {get_local_time()}")
        self.resource[resource.name] = {
            "event": event,
            "date": get_local_time(),
            "lock": Event()
        }

    def release(self, resource, event):
        """
        释放资源
        """
        if resource.name in self.resource:
            if self.resource[resource.name]['event'] == event:
                self.log.info(f"Release lock for {resource.name}")
                self.resource[resource.name]['lock'].set()
                self.resource.pop(resource.name)
            else:
                raise InvalidLockOperation(
                    f"{resource.name} is locked by {self.resource[resource.name]['event']}")
        else:
            raise InvalidLockOperation(f'{resource.name} is not locked')

if __name__ == "__main__":

    class TestResource:
        def __init__(self, name):
            self.name = name


    log = logger.register("testlog")
    pool = ResourceLockPool(log)
    device1 = TestResource('device1')


    def test_method1():
        pool.lock(device1, "event1")
        log.info("method1 start")
        time.sleep(10)
        pool.release(device1, "event1")
        log.info("method1 stop")


    def test_method2():
        pool.lock(device1, "event2")
        log.info("method2 start")
        time.sleep(10)
        pool.release(device1, "event2")
        log.info("method2 stop")



    thread1 = Thread(target=test_method1)
    thread2 = Thread(target=test_method2)

    threads = [thread1, thread2]
    for t in threads:
        t.start()

    for t in threads:
        t.join()


