from .base import CommandLine
import time
import paramiko


class SshClient(CommandLine):
    def __init__(self, host, port, username, password, **kwargs):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh = None
        self.session = None


    def connect(self):
        if self.ssh is None:
            try:
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh.connect(self.host, self.port, self.username, self.password)
                trans = self.ssh.get_transport()
                self.session = trans.open_session()
                self.session.get_pty()
                self.session.invoke_shell()
                if not self._login():
                    self.disconnect()
            except Exception as ex:
                self.ssh = None
                self.session = None


    def disconnect(self):
        if self.ssh:
            try:
                self.ssh.close()
            finally:
                self.ssh = None
                self.session = None

    def send(self, string):
        self.session.send(string.encode())

    def send_and_wait(self, string, waitfor, timeout=60, **kwargs):
        self.send(string)
        return self._wait_for(waitfor, timeout=timeout)

    def receive(self):
        return self.session.recv(256).decode()

    def receive_binary(self):
        return self.session.recv(256)

    def send_binary(self, binary):
        self.session.send(binary.encode())

    def _login(self):
        return self._wait_for("$", timeout=10)

    def _wait_for(self, string, timeout):
        rcv = ""
        recent = time.time()
        while time.time() - recent < timeout:
            rcv += self.session.recv(256).decode()
            if string in rcv:
                return rcv
            else:
                time.sleep(0.1)
        return None
