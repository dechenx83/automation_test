"""
注册实例化方法，和测试资源模块的耦合点
"""
from thirdpart.commandline.telnet import TelnetClient
from thirdpart.commandline.ssh import SshClient
from core.resource.pool import register_resource, ResourcePool


def create_telnet(resource):
    ip = resource.management.get("ip", "")
    port = resource.management.get("port", 23)
    username = resource.management.get("username", "")
    password = resource.management.get("password", "")

    return TelnetClient(ip, port, username, password)


def create_ssh(resource):
    ip = resource.management.get("ip", "")
    port = resource.management.get("port", 23)
    username = resource.management.get("username", "")
    password = resource.management.get("password", "")

    return SshClient(ip, port, username, password)


register_mapping = (
    ("device", "telnet", create_telnet),
    ("device", "ssh", create_ssh),
)

for mapping in register_mapping:
    register_resource(mapping[0], mapping[1], mapping[2])


rp = ResourcePool()

rp.add_device("TelnetServer1", type="telnet")
setattr(rp.topology["TelnetServer1"], "management", {"ip": "192.168.1.100", "port":23, "username": "admin", "password": "admin"})


telnet_resource = rp.collect_device(device_type="telnet", count=1)[0]
telnet_client = telnet_resource.get_comm_instance()
print(telnet_client.host)
