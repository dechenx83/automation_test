from core.case.base import TestCaseBase
from core.case.decorator import case, data_provider
from core.config.setting import TestSettingBase
from core.resource.pool import ResourcePool
from core.result.reporter import StepResult


@case(priority=2, skip_if_high_priority_failed=True)
class HelloWorldTest2(TestCaseBase):

    def collect_resource(self, pool: ResourcePool):
        self.reporter.add_step_group("Collect Resources")
        self.ap = pool.collect_device("AP", 1)[0]
        self.reporter.end_step_group()

    def setup(self):
        self.reporter.add(StepResult.INFO, self.ap.name)
        self.reporter.add(StepResult.INFO, "This is setup step")

    def test(self, test_data):
        self.reporter.add(StepResult.PASS, "This Passed step")
        self.reporter.add_step_group("Step group1")
        self.reporter.add(StepResult.FAIL, "This is Failed Step")
        self.reporter.end_step_group()

    def cleanup(self):
        self.reporter.add(StepResult.INFO, "This is clean up step")

    class HelloWorldTestSetting(TestSettingBase):
        case_setting1 = "setting1"
        case_setting2 = 20
