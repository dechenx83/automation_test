
from core.testengine.eventdriven.eventbase import EventBase, EventStatus
from core.result.reporter import StepResult


class DemoEvent1(EventBase):

    name = "DemoEvent1"

    def action(self):
        self.reporter.add(StepResult.INFO, "This is a Demo Event")
        self.result = EventStatus.SUCCESS


class DemoEvent2(EventBase):

    name = "DemoEvent2"

    def action(self):
        self.reporter.add(StepResult.INFO, "This is a Demo Event")
        self.result = EventStatus.SUCCESS


