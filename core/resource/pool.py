"""
资源池对象，包括了资源池、资源以及资源端口的定义，序列化以及反序列化的方法
"""
import json
import os
import time
from abc import ABCMeta, abstractmethod
from core.config.setting import static_setting, SettingBase


# 存放用户注册的配置接口对象类型
_resource_device_mapping = dict()
_resource_port_mapping = dict()


class ResourceError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ResourceNotMeetConstraint(Exception):
    def __init__(self, constraints):
        super().__init__("Resource Not Meet Constraints")
        self.description = ""
        for constraint in constraints:
            self.description += constraint.description + "\n"


def register_resource(category, resource_type, comm_callback):
    """
    注册配置接口实例化的方法或者类。
    """
    if category == "device":
        _resource_device_mapping[resource_type] = comm_callback
    elif category == "port":
        _resource_port_mapping[resource_type] = comm_callback


class ResourceDevice:
    """
    代表所有测试资源设备的配置类，字段动态定义
    """
    def __init__(self, name="", **kwargs):
        self.name = name
        self.type = kwargs.get("type", None)
        self.description = kwargs.get("description", None)
        self.pre_connect = False
        self.ports = dict()
        self._instance = None

    def add_port(self, name, *args, **kwargs):
        if name in self.ports:
            raise ResourceError(f"Port Name {name} already exists")
        self.ports[f"{name}"] = DevicePort(self, name, **kwargs)

    def get_port_count(self, **kwargs):
        return len(self.ports)

    def to_dict(self):
        ret = dict()
        for key, value in self.__dict__.items():
            if key == "__instance":
                continue
            if key == "ports":
                ret[key] = dict()
                for port_name, port in value.items():
                    ret[key][port_name] = port.to_dict()
            else:
                ret[key] = value
        return ret

    def get_comm_instance(self, new=False):
        if self.type not in _resource_device_mapping:
            raise ResourceError(f"type {self.type} is not registered")
        if not new and self._instance:
            return self._instance
        else:
            self._instance = _resource_device_mapping[self.type](self)
        return self._instance

    @staticmethod
    def from_dict(dict_obj):
        ret = ResourceDevice()
        for key, value in dict_obj.items():
            if key == "ports":
                ports = dict()
                for port_name, port in value.items():
                    ports[port_name] = DevicePort.from_dict(port, ret)
                setattr(ret, "ports", ports)
            else:
                setattr(ret, key, value)
        return ret


class DevicePort:
    """
    代表设备的连接端口
    """
    def __init__(self, parent_device=None, name="", **kwargs):
        self.parent = parent_device
        self.type = kwargs.get("type", None)
        self.name = name
        self.description = kwargs.get("description", None)
        self.remote_ports = list()
        self._instance = None

    def get_comm_instance(self, new=False):
        if self.type not in _resource_port_mapping:
            raise ResourceError(f"type {self.type} is not registered")
        if not new and self._instance:
            return self._instance
        else:
            self._instance = _resource_port_mapping[self.type](self)
        return self._instance

    def to_dict(self):
        ret = dict()
        for key, value in self.__dict__.items():
            if key == "__instance":
                continue
            if key == "parent":
                ret[key] = value.name
            elif key == "remote_ports":
                ret[key] = list()
                for remote_port in value:
                    #使用device的名称和port的名称来表示远端的端口
                    #在反序列化的时候可以方便地找到相应的对象实例
                    ret[key].append(
                        {
                            "device": remote_port.parent.name,
                            "port": remote_port.name
                        }
                    )
            else:
                ret[key] = value
        return ret

    @staticmethod
    def from_dict(dict_obj, parent):
        ret = DevicePort(parent)
        for key, value in dict_obj.items():
            if key == "remote_ports" or key == "parent":
                continue
            setattr(ret, key, value)
        return ret


class ResourcePool:
    """
    资源池类，负责资源的序列化和反序列化以及储存和读取
    """
    def __init__(self):
        self.topology = dict()
        self.reserved = None
        self.information = dict()
        self.file_name = None
        self.owner = None

    def add_device(self, device_name, **kwargs):
        if device_name in self.topology:
            raise ResourceError(f"device {device_name} already exists")
        self.topology[device_name] = ResourceDevice(device_name, **kwargs)

    def reserve(self):
        if self.file_name is None:
            raise ResourceError("load a resource file first")
        self.load(self.file_name, self.owner)
        self.reserved = {"owner": self.owner, "date": time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())}
        self.save(self.file_name)

    def release(self):
        if self.file_name is None:
            raise  ResourceError("load a resource file first")
        self.load(self.file_name)
        self.reserved = None
        self.save(self.file_name)

    def collect_device(self, device_type, count, constraints=list()):
        ret = list()
        for key, value in self.topology.items():
            if value.type == device_type:
                for constraint in constraints:
                    if not constraint.is_meet(value):
                        break
                else:
                    ret.append(value)
            if len(ret) >= count:
                return ret
        else:
            return list()

    def collect_all_device(self, device_type, constraints=list()):
        ret = list()
        for key, value in self.topology.items():
            if value.type == device_type:
                for constraint in constraints:
                    if not constraint.is_meet(value):
                        break
                else:
                    ret.append(value)
        return ret

    def collect_connection_route(self, resource, constraints=list()):
        """
        获取资源连接路由
        """
        # 限制类必须是连接限制ConnectionConstraint
        for constraint in constraints:
            if not isinstance(constraint, ConnectionConstraint):
                raise ResourceError(
                    "collect_connection_route only accept ConnectionConstraints type")
        ret = list()
        for constraint in constraints:
            conns = constraint.get_connection(resource)
            if not any(conns):
                raise ResourceNotMeetConstraint([constraint])
            for conn in conns:
                ret.append(conn)
        return ret

    def load(self, filename, owner):
        # 检查文件是否存在
        if not os.path.exists(filename):
            raise ResourceError(f"Cannot find file {filename}")
        self.file_name = filename

        # 初始化
        self.topology.clear()
        self.reserved = False
        self.information = dict()

        #读取资源配置的json字符串
        with open(filename) as file:
            json_object = json.load(file)

        #判断是否被占用
        if "reserved" in json_object and \
            json_object['reserved'] is not None and \
                json_object['reserved']['owner'] != owner:
            raise ResourceError(f"Resource is reserved by {json_object['reserved']['owner']}")

        self.owner = owner

        if "info" in json_object:
            self.information = json_object['info']
        for key, value in json_object['devices'].items():
            device = ResourceDevice.from_dict(value)
            self.topology[key] = device

        # 映射所有设备的连接关系
        for key, device in json_object['devices'].items():
            for port_name, port in device['ports'].items():
                for remote_port in port['remote_ports']:
                    remote_port_obj = \
                        self.topology[remote_port["device"]].\
                            ports[remote_port["port"]]
                    self.topology[key].ports[port_name].\
                        remote_ports.append(remote_port_obj)

    def save(self, filename):
        """

        """
        with open(filename, mode="w") as file:
            root_object = dict()
            root_object['devices'] = dict()
            root_object['info'] = self.information
            root_object['reserved'] = self.reserved
            for device_key, device in self.topology.items():
                root_object['devices'][device_key] = device.to_dict()
            json.dump(root_object, file, indent=4)


class Constraint(metaclass=ABCMeta):
    """
    资源选择器限制条件的基类
    """
    def __init__(self):
        self.description = None

    @abstractmethod
    def is_meet(self, resource, *args, **kwargs):
        pass


class ConnectionConstraint(Constraint, metaclass=ABCMeta):
    """
    用户限制获取Remote Port的限制条件。
    """
    @abstractmethod
    def get_connection(self, resource, *args, **kwargs):
        pass


@static_setting.setting("ResourceSetting")
class ResourceSetting(SettingBase):
    file_name = "resource_setting.setting"

    resource_path = os.path.join(os.environ['HOME'], "test_resource")
    auto_connect = False


def get_resource_pool(filename, owner):
    ResourceSetting.load()
    full_name = os.path.join(ResourceSetting.resource_path, filename)
    rv = ResourcePool()
    rv.load(full_name, owner)
    return rv


if __name__ == "__main__":




    switch = ResourceDevice(name="switch1")
    switch.add_port("ETH1/1")
    switch.add_port("ETH1/2")

    switch2 = ResourceDevice(name="switch2")
    switch2.add_port("ETH1/1")
    switch2.add_port("ETH1/2")

    switch.ports['ETH1/1'].remote_ports.append(switch2.ports['ETH1/1'])
    switch2.ports['ETH1/1'].remote_ports.append(switch.ports['ETH1/1'])

    rp = ResourcePool()
    rp.topology['switch1'] = switch
    rp.topology['switch2'] = switch2
    #rp.save("test.json")
    rp.load("test.json","michael")
    rp.reserve()
    rp2 = ResourcePool()
    rp2.load("test.json", "jason")
    print("done")

