from abc import ABCMeta, abstractmethod


class IperfPort:
    pass

class TrafficStream:

    def __init__(self, source, destination):
        self.rate = None
        self.frame_size = 1518
        self.vlan = 0
        self.l4stack = None
        self.source = source
        self.destination = destination

class L3Device:

    def __init__(self, ip, mask, gateway, parent):
        self.ip = ip
        self.mask = mask
        self.gateway = gateway
        self.parent = parent


class Endpoint:

    def __init__(self, name, comm):
        self.name = name
        self.comm = comm
        self.devices = list()


class TrafficTester(metaclass=ABCMeta):

    def __init__(self, streams):
        self.traffic_streams = streams
        self.duration = 0
        self.warmup = 5

    @abstractmethod
    def config(self):
        pass

    @abstractmethod
    def test(self):
        pass

    @abstractmethod
    def cleanup(self):
        pass

    @staticmethod
    def create(streams):
        # 具体实例生成的工厂类
        pass


class IperfTrafficTester(TrafficTester):

    def config(self):
        # 实现 iperf的配置方法
        pass


