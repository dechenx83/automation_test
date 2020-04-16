import os
import importlib
import json
from abc import ABCMeta
from functools import wraps, update_wrapper

_DEFAULT_PATH = os.path.join(os.environ['HOME'], "test_config")


class SettingError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SettingBase(metaclass=ABCMeta):
    file_name = None
    setting_path = _DEFAULT_PATH

    @classmethod
    def _get_full_path(cls):
        filename = cls.file_name if cls.file_name else cls.__name__ + ".setting"
        return os.path.join(cls.setting_path, filename)

    @classmethod
    def save(cls):
        if not os.path.exists(cls.setting_path):
            os.makedirs(cls.setting_path)
        with open(cls._get_full_path(), "w") as file:
            obj = dict()
            for key, value in cls.__dict__.items():
                if key.startswith("_") or key == "setting_path"\
                        or key == "file_name":
                    continue
                obj[key] = value
            json.dump(obj, file, indent=4)

    @classmethod
    def load(cls):
        if os.path.exists(cls._get_full_path()):
            with open(cls._get_full_path()) as file:
                obj = json.load(file)
            for key, value in obj.items():
                setattr(cls, key, value)
        else:
            cls.save()


def dynamic_setting(cls):
    @wraps(cls)
    def inner(*args, **kwargs):
        rv = cls(*args, **kwargs)
        for key, value in cls.__dict__.items():
            if hasattr(value, "__base__") and value.__base__.__name__ == "SettingBase":
                setattr(rv, "setting", value)
                if hasattr(rv, "setting_path"):
                    value.setting_path = rv.setting_path
                if hasattr(rv, "setting_file") and rv.setting_file is not None:
                    value.file_name = rv.setting_file
                else:
                    if value.file_name is None:
                        value.file_name = f"{cls.__name__}_{value.__name__}.setting"
                    else:
                        value.file_name = f"{cls.__name__}_{value.file_name}.setting"
                value.load()
        return rv
    return inner


class TestSettingBase(SettingBase):

    def __init__(self, setting_path, file_name):
        self.__class__.file_name = file_name
        self.__class__.setting_path = setting_path


class StaticSettingManager:
    """
    静态配置管理类
    """
    def __init__(self):
        self.settings = dict()
        self._setting_path = _DEFAULT_PATH

    def add_setting(self, setting_name, setting_class):
        if hasattr(setting_class, "__base__"):
            if setting_class.__base__.__name__ != "SettingBase":
                raise SettingError("注册的配置必须是SettingBase的子类")
        else:
            raise SettingError("注册的配置必须是SettingBase的子类")
        self.settings[setting_name] = setting_class
        setting_class.setting_path = self._setting_path

    def setting(self, setting_name, *args, **kwargs):
        """
        配置文件的注册装饰器
        """
        def wrapper(cls):
            self.add_setting(setting_name, cls)
            return cls
        return wrapper

    @property
    def setting_path(self):
        return self._setting_path

    @setting_path.setter
    def setting_path(self, value):
        self._setting_path = value
        for key, setting in self.settings.items():
            setting.setting_path = value

    def sync_path(self):
        """
        同步所有配置的路径
        """
        for key, setting in self.settings.items():
            setting.setting_path = self._setting_path

    def save_all(self):
        """
        保存所有配置
        """
        self.sync_path()
        for key, setting in self.settings.items():
            setting.save()

    def load_all(self):
        """
        读取所有配置
        """
        self.sync_path()
        for key, setting in self.settings.items():
            setting.load()


static_setting = StaticSettingManager()


if __name__ == "__main__":

    @dynamic_setting
    class TestClass:
        def __init__(self, *args, **kwargs):
            self.setting_path = kwargs.get("setting_path", ".")
            self.setting_file = kwargs.get("setting_file", None)

        class MySetting(SettingBase):

            field1 = 1
            field2 = 2

    tc = TestClass(setting_path=".")
