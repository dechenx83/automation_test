
from core.config.logicmodule import ModuleBase, ModuleType
from core.config.setting import dynamic_setting, SettingBase
from core.resource.pool import ResourcePool
from core.result.reporter import ResultReporter, StepResult


@dynamic_setting
class DemoModule(ModuleBase):
    """
    示例模块，会在测试用例执行前输出一个INFO信息
    """
    module_type = ModuleType.POST
    priority = 0

    def __init__(self, report: ResultReporter, resource: ResourcePool, **kwargs):
        super().__init__(report, resource)
        self.setting_path = kwargs.get("setting_path", ".")
        self.setting_file = kwargs.get("setting_file", None)

    def action(self):
        self.reporter.add(StepResult.INFO, "This is a demo module")
        self.reporter.add(StepResult.INFO, f"setting value: {self.setting.setting_value} ")

    def stop(self):
        pass

    class ModuleSetting(SettingBase):

        setting_value = "a value"
