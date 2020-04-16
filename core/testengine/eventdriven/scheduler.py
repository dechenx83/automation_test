from apscheduler.schedulers.background import BlockingScheduler, BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED
from core.result.reporter import ResultReporter
from core.result.logger import logger
from core.config.setting import static_setting
import core.testengine.caserunner
import importlib
import os
import datetime
import uuid


class EventScheduler:
    def __init__(self, reporter: ResultReporter):
        self.reporter = reporter
        self.scheduler = BlockingScheduler()
        self.events = list()
        log_path = static_setting.settings["CaseRunner"].log_path
        log_file = os.path.join(log_path, "event_scheduler_log.log")
        self.log = logger.register("EventScheduler", filename=log_file, for_test=True)
        self.scheduler.add_listener(self._event_listen, EVENT_JOB_EXECUTED)

    def add_event(self, event, package, args, is_background, need_lock,
                  start_time, interval=5, loop_count=1, description=""):
        m = importlib.import_module(package)
        event_cls = getattr(m, event)
        new_event = event_cls(description, log=self.log)
        new_event.need_lock = need_lock
        new_event.back_ground = is_background
        new_event.arguments = args
        new_event.interval = interval
        new_event.loop_count = loop_count
        # 生成一个STEP 的节点给Event操作
        new_event.reporter = self.reporter.add_event_group(f"Event: {event}")

        if is_background:
            new_event.job = self.scheduler.add_job(new_event.run, "interval",
                                                   seconds=interval,
                                                   start_date=start_time,
                                                   id=f"{event}{uuid.uuid4()}"
                                                   )
        else:
            new_event.job = self.scheduler.add_job(new_event.run, "date",
                                                   run_date=start_time,
                                                   id=f"{event}{uuid.uuid4()}"
                                                   )
        self.events.append(new_event)

    def remove_event(self, event_id):
        job = self.scheduler.get_job(event_id)
        if job:
            event_to_remove = None
            for event in self.events:
                if event.job == job:
                    event_to_remove = event
                    self.scheduler.remove_job(event_id)
                    break
            if event_to_remove:
                self.events.remove(event_to_remove)

    def start(self):
        self.scheduler.start()

    def _event_listen(self, job):
        for event in self.events:
            if event.job.id == job.job_id:
                if event.back_ground:
                    return
                else:
                    if event.loop_count == 1:
                        return
                    delta = datetime.timedelta(seconds=event.interval)
                    next_date = job.scheduled_run_time + delta
                    event.job = self.scheduler.add_job(event.run, "date",
                                                       run_date=next_date,
                                                       id=f"{event.name}{uuid.uuid4()}")
                    event.loop_count -= 1
                    return


if __name__=="__main__":
    report = ResultReporter(logger.register("TestLog"))
    scheduler = EventScheduler(report)
    scheduler.add_event("DemoEvent1", "product.event.demo_event",
                        args=None, is_background=False, need_lock=False,
                        loop_count=2, interval=5,
                        start_time="2020-3-18 00:48:59", description="a test")
    scheduler.start()

    input("wait")