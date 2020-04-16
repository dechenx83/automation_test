from thirdpart.commandline.telnet import TelnetClient
from thirdpart.commandline.ssh import SshClient
from core.resource.pool import register_resource, ResourcePool

class UnknownManagementSessionType(Exception):
    pass


def create(resource):
    host = getattr(resource, "host", "")
    ip = getattr(resource, "port", "")
    username = getattr(resource, "username", "")
    password = getattr(resource, "password", "")
    conn_type = getattr(resource, "conn_type", "telnet")
    if conn_type == "telnet":
        return TelnetClient(host, ip, username, password)
    elif conn_type == "ssh":
        return SshClient(host, ip, username, password)
    raise UnknownManagementSessionType()


register_resource("device", "linux_server", create)

pool = ResourcePool()
pool.load("/Users/lilen/PycharmProjects/autoframework/product/resource/test.json", "dechen")
server = pool.collect_device("linux_server", count=1)[0]
client = server.get_comm_instance()
print(client)
client.connect()
print(client.send_and_wait("date\n", "$"))

