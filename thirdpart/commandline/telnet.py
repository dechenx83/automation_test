from .base import CommandLine
from telnetlib import Telnet


class TelnetClient(CommandLine):
    def __init__(self, host, port, username, password, **kwargs):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.username_prompt = kwargs.get("user_prompt", "as:")
        self.password_prompt = kwargs.get("pwd_prompt", "assword:")
        self.telnet = None

    def connect(self):
        if self.telnet:
            return
        self.telnet = Telnet()

        self.telnet.open(self.host, self.port)
        if not self._login():
            self.disconnect()

    def disconnect(self):
        if self.telnet:
            try:
                self.telnet.close()
            finally:
                self.telnet = None

    def send(self, string):
        self.telnet.write(string.encode())

    def send_and_wait(self, string, waitfor, timeout=60, **kwargs):
        self.telnet.write(string.encode())
        return self.telnet.read_until(waitfor.encode(), timeout=timeout).decode()

    def receive(self):
        return self.telnet.read_eager().decode()

    def receive_binary(self):
        return self.telnet.read_eager()

    def send_binary(self, binary):
        self.telnet.write(binary)

    def _login(self):
        ret_data = self.telnet.read_until(
            self.username_prompt.encode(), timeout=10)
        if not ret_data:
            return False
        self.telnet.write(f"{self.username}\n".encode())
        ret_data = self.telnet.read_until(
            self.password_prompt.encode(), timeout=10)
        if not ret_data:
            return False
        self.telnet.write(f"{self.password}\n".encode())
        ret_data = self.telnet.read_until("$".encode())
        if ret_data:
            return True
        else:
            return False

