from core.case.base import TestCaseBase
from core.case.decorator import case, data_provider
from core.resource.pool import ResourcePool
from core.result.reporter import StepResult


@case(priority=1)
class DataDrivenTest(TestCaseBase):

    def collect_resource(self, pool: ResourcePool):
        pass

    def setup(self):
        self.test_data_var["var"] = "Hello"

    @data_provider()
    def test(self, test_data):
        self.reporter.add(StepResult.INFO, str(test_data["test_value"]))
        self.test_data_var["var"] = "World"

    def cleanup(self):
        pass

