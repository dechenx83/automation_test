from abc import ABCMeta, abstractmethod
from core.resource.pool import register_resource

class CommandLine(metaclass=ABCMeta):

    @abstractmethod
    def send(self, string):
        pass

    @abstractmethod
    def send_and_wait(self, string, waitfor, timeout=60, **kwargs):
        pass

    @abstractmethod
    def receive(self):
        pass

    @abstractmethod
    def send_binary(self, binary):
        pass

    @abstractmethod
    def receive_binary(self):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def _login(self):
        pass

