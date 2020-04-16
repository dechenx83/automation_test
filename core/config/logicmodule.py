import json
from enum import Enum
from abc import ABCMeta, abstractmethod
from core.result.reporter import ResultReporter
from core.resource.pool import ResourcePool
from core.config.setting import static_setting, SettingBase
from threading import Thread
from importlib import import_module
import os


class ModuleType(Enum):
    PRE = 1
    PARALLEL = 2
    POST =3


class ModuleBase(metaclass=ABCMeta):
    """
    逻辑配置模块的基类
    """
    module_type = None
    priority = 99

    def __init__(self, report: ResultReporter, resource: ResourcePool):
        self.reporter = report

        self.resource = resource
        self.thread = None

    @abstractmethod
    def action(self):
        """
        实现该方法来实现模块的逻辑功能
        """
        pass

    def do(self):
        if self.module_type == ModuleType.PARALLEL:
            self.thread = Thread(target=self.action)
            self.thread.start()
        else:
            self.action()

    @abstractmethod
    def stop(self):
        """
        实现该方法来实现模块逻辑功能的终止方法
        """
        pass


@static_setting.setting("LogicModule")
class ModuleSetting(SettingBase):

    module_list_file = "./modules/modulelist.json"
    module_setting_path = "./modules/settings"


class ModuleManager:
    """
    配置模块的管理
    """
    def __init__(self):
        self.modules = dict()

    def load(self):
        """
        从模块列表装载所有模块类
        """
        if not os.path.exists(ModuleSetting.module_list_file):
            # 如果没有找到模块配置文件，则不做任何操作
            return
        with open(ModuleSetting.module_list_file) as file:
            obj = json.load(file)

        for item in obj['modules']:
            try:
                # 配置条目格式：
                # {
                #     "name": "modulename",
                #     "package":"module path",
                #     "setting_file": "setting filename",
                #     "setting_path": "setting path"
                # }
                module_name = item['name']
                module_package = item['package']
                setting_file = item.get("setting_file", None)
                setting_path = item.get('setting_path', ModuleSetting.module_setting_path)
                m = import_module(module_package)
                for element, value in m.__dict__.items():
                    if element == module_name:
                        self.modules[module_name] = {
                            "class": value,
                            "setting_file": setting_file,
                            "setting_path": setting_path
                        }
            except Exception:
                pass

    def add_module(self, module_class, setting_file=None, setting_path=None):
        """
        添加模块
        """
        obj = {
            "class": module_class,
            "setting_file": setting_file,
            "setting_path": setting_path
        }
        self.modules[module_class.__name__] = obj

    def get_module_instances(self, module_type, result_reporter, resources):
        """
        获取模块的实例化列表
        """
        rv = list()
        for mkey, mvalue in self.modules.items():
            print(mvalue['class'].module_type)
            print(module_type)
            if mvalue['class'].module_type.value == module_type.value:
                rv.append(mvalue['class'](result_reporter, resources))
        return rv

    def save(self):
        """
        保存所有模块到模块配置列表
        """
        obj = dict()
        obj['modules'] = list()
        for mkey, mvalue in self.modules.items():
            obj['modules'].append({
                "name": mkey,
                "package": mvalue["class"].__module__,
                "setting_file": mvalue['setting_file'],
                "setting_path": mvalue['setting_path']
            })
        file_dir = os.path.dirname(ModuleSetting.module_list_file)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        with open(ModuleSetting.module_list_file, "w") as file:
            json.dump(obj, file, indent=4)

    def run_module(self, type):
        pass

    def stop_module(self):
        pass


if __name__ == "__main__":
    from product.logicmodules.demo import DemoModule
    mm = ModuleManager()
    mm.load()
    mm.add_module(DemoModule)
    mm.save()
    mm.load()
    post_module = mm.get_module_instances(ModuleType.POST, None, None)
    print(post_module)



