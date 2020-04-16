from core.case.base import TestCaseBase
from core.case.decorator import case, data_provider
from core.resource.pool import ResourcePool
from core.result.reporter import StepResult
import time


@case(priority=10, test_type="Regression")
class DataDrivenTest3(TestCaseBase):
    """
    Data Driven Demo
    """
    def collect_resource(self, pool: ResourcePool):
        pass

    def setup(self):
        pass

    @data_provider()
    def test(self, test_data):
        self.reporter.add(StepResult.INFO, str(test_data["test_value"]))

    def cleanup(self):
        pass

    def get_time(self):
        return time.time()

dd