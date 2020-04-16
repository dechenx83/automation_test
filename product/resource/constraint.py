from core.resource.pool import Constraint, ConnectionConstraint, ResourceDevice, DevicePort, ResourcePool


class PhoneMustBeAndroidConstraint(Constraint):
    """
    判断手机必须是安卓系统，可以附带版本大小判断
    """
    def __init__(self, version_op=None, version=None):
        super().__init__()
        self.version = version
        self.version_op = version_op
        if self.version_op is not None:
            self.description = \
                f"Phone Type must be android and version {self.version_op} {self.version}"
        else:
            self.description = "Phone Type must be android"

    def is_meet(self, resource, *args, **kwargs):

        # 首先判断资源类型是Resource Device，并且type是Android
        if isinstance(resource, ResourceDevice) and \
                resource.type == "Android":
            if self.version_op:
                # 判断资源是否有version字段和值
                device_version = getattr(resource, "version")
                if device_version is None:
                    return False
                if self.version_op == "=":
                    return device_version == self.version
                elif self.version_op == ">":
                    return device_version > self.version
                elif self.version_op == "<":
                    return device_version < self.version
                elif self.version_op == ">=":
                    return device_version >= self.version
                elif self.version_op == "<=":
                    return device_version <= self.version
                elif self.version_op == "!=":
                    return device_version != self.version
                else:
                    return False
            else:
                # 没有版本判断操作符，则资源满足条件
                return True
        # 不满足条件
        return False


class DeviceMustHaveTrafficGeneratorConnected(ConnectionConstraint):
    """
    判断AP必须有测试仪表连接
    """
    def __init__(self, speed_constraint=None, port_count=1):
        super().__init__()
        self.speed = speed_constraint
        self.port_count = port_count
        self.description = \
            f"AP Must have {port_count} Traffic Generator Port(s) Connected"
        if speed_constraint:
            self.description += f", {speed_constraint.description}"

    def is_meet(self, resource, *args, **kwargs):
        return any(self.get_connection(resource))

    def get_connection(self, resource, *args, **kwargs):
        if not isinstance(resource, ResourceDevice):
            return False
        meet_ports = list()
        for port_key, port in resource.ports.items():
            # 假设测试仪表端口连在ETH端口上，跳过非ETH端口的判断
            if port.type != "ETH":
                continue
            #遍历Remote ports
            for remote_port in port.remote_ports:
                if remote_port.parent.type == "TrafficGen":
                    # 如果有速度限制，则调用该限制实例
                    if self.speed:
                        if self.speed.is_meet(remote_port):
                            meet_ports.append(remote_port)
                    else:
                        meet_ports.append(remote_port)
        if len(meet_ports) >= self.port_count:
            return meet_ports[0: self.port_count]
        return list()


class TrafficGeneratorSpeedMustBeGraterThan(Constraint):
    """
    判断测试仪表端口速率必须大于速度
    """
    def __init__(self, speed):
        super().__init__()
        self.speed = speed
        self.description = f"Traffic Generator Port Speed Must Grater Than {speed}M"

    def is_meet(self, resource, *args, **kwargs):
        if not isinstance(resource, DevicePort) or resource.parent.type != "TrafficGen":
            return False
        return getattr(resource, "speed", None) is not None and \
               getattr(resource, "speed") >= self.speed


class ApMustHaveStaConnected(ConnectionConstraint):
    """
    判断AP必须有STA连接
    """
    def __init__(self, sta_constraints=list(), sta_count=1):
        super().__init__()
        # 将constraint分类
        self.sta_constraints = list()
        self.sta_conn_constraints = list()
        for sta_constraint in sta_constraints:
            if isinstance(sta_constraint, ConnectionConstraint):
                self.sta_conn_constraints.append(sta_constraint)
            else:
                self.sta_constraints.append(sta_constraint)
        self.sta_count = sta_count
        self.description = f"AP must have {sta_count} STA connected"
        for sta_constraint in self.sta_constraints:
            self.description += f"\n{sta_constraint.description}"

    def is_meet(self, resource, *args, **kwargs):
        return any(self.get_connection(resource))

    def get_connection(self, resource, *args, **kwargs):
        if not isinstance(resource, ResourceDevice) or resource.type != "AP":
            return False
        for port_key, port in resource.ports.items():
            if port.type != "WIFI":
                continue
            ret = list()
            for remote_port in port.remote_ports:
                if remote_port.parent.type == 'STA':
                    # 用STA Constraint判断远端端口的STA设备是否符合条件
                    meet_all = True
                    for sta_constraint in self.sta_constraints:
                        if not sta_constraint.is_meet(remote_port.parent):
                            meet_all = False
                            break

                    # 如果没有基本的限制条件，不继续测试Connection条件
                    if not meet_all:
                        continue

                    # 对于connection的条件，返回对端的所有端口
                    conn_remote = list()
                    meet_connection = True
                    for sta_conn_constraint in self.sta_conn_constraints:
                        conns = sta_conn_constraint.get_connection(remote_port.parent)
                        # 不满足Connection条件
                        if not any(conns):
                            meet_connection = False
                            break
                        for conn in conns:
                            conn_remote.append(conn)

                    # 没有满足Connection条件，跳过。
                    if not meet_connection:
                        continue

                    ret.append((remote_port, conn_remote))

            if len(ret) >= self.sta_count:
                return ret[0: self.sta_count]
        return list()


if __name__ == "__main__":
    ap1 = ResourceDevice(name="ap1", type="AP")
    ap1.add_port("ETH1/1", type="ETH")
    ap1.add_port("ETH1/2", type="ETH")
    ap1.add_port("WIFI", type="WIFI")

    sta1 = ResourceDevice(name="sta1", type="STA")
    sta1.add_port("WIFI", type="WIFI")
    sta1.add_port("ETH1/1", type="ETH")
    sta1.add_port("ETH1/2", type="ETH")

    sta2 = ResourceDevice(name="sta2", type="STA")
    sta2.add_port("WIFI", type="WIFI")
    sta2.add_port("ETH1/1", type="ETH")
    sta2.add_port("ETH1/2", type="ETH")

    sta3 = ResourceDevice(name="sta3", type="STA")
    sta3.add_port("WIFI", type="WIFI")
    sta3.add_port("ETH1/1", type="ETH")
    sta3.add_port("ETH1/2", type="ETH")

    traffic_gen = ResourceDevice(name="trafficGen", type="TrafficGen")
    traffic_gen.add_port("PORT1/1/1", type="ETH")
    setattr(traffic_gen.ports['PORT1/1/1'], "speed", 1000)
    traffic_gen.add_port("PORT1/1/2", type="ETH")
    setattr(traffic_gen.ports['PORT1/1/2'], "speed", 1000)
    traffic_gen.add_port("PORT1/1/3", type="ETH")
    setattr(traffic_gen.ports['PORT1/1/3'], "speed", 1000)
    traffic_gen.add_port("PORT1/1/4", type="ETH")
    setattr(traffic_gen.ports['PORT1/1/4'], "speed", 1000)


    # AP和Traffic Generator之间的连接
    ap1.ports['ETH1/1'].remote_ports.append(traffic_gen.ports['PORT1/1/1'])
    traffic_gen.ports['PORT1/1/1'].remote_ports.append(ap1.ports['ETH1/1'])

    #建立ap和STA之间的连接
    ap1.ports['WIFI'].remote_ports.append(sta1.ports['WIFI'])
    sta1.ports['WIFI'].remote_ports.append(ap1.ports['WIFI'])

    ap1.ports['WIFI'].remote_ports.append(sta2.ports['WIFI'])
    sta2.ports['WIFI'].remote_ports.append(ap1.ports['WIFI'])

    ap1.ports['WIFI'].remote_ports.append(sta3.ports['WIFI'])
    sta3.ports['WIFI'].remote_ports.append(ap1.ports['WIFI'])

    #建立 STA 和 Traffic Generator之间的连接
    sta1.ports['ETH1/1'].remote_ports.append(traffic_gen.ports['PORT1/1/2'])
    traffic_gen.ports['PORT1/1/2'].remote_ports.append(sta1.ports['ETH1/1'])

    sta2.ports['ETH1/1'].remote_ports.append(traffic_gen.ports['PORT1/1/3'])
    traffic_gen.ports['PORT1/1/3'].remote_ports.append(sta2.ports['ETH1/1'])

    sta3.ports['ETH1/1'].remote_ports.append(traffic_gen.ports['PORT1/1/4'])
    traffic_gen.ports['PORT1/1/4'].remote_ports.append(sta3.ports['ETH1/1'])


    rp = ResourcePool()
    rp.topology['ap1'] = ap1
    rp.topology['sta1'] = sta1
    rp.topology['sta2'] = sta2
    rp.topology['sta3'] = sta3
    rp.topology['trafficGen'] = traffic_gen
    rp.save("test.json")

    # AP必须有STA的连接
    constraint1 = ApMustHaveStaConnected()

    # AP必须至少有3个STA连接
    constraint2 = ApMustHaveStaConnected(sta_count=3)

    # AP必须至少有4个STA连接
    constraint3 = ApMustHaveStaConnected(sta_count=4)



    # 设备必须有10000M速率的测试仪表端口连接
    constraint5 = DeviceMustHaveTrafficGeneratorConnected(
        speed_constraint=TrafficGeneratorSpeedMustBeGraterThan(10000))



    # 设备必须有1000M速率的测试仪表端口连接
    constraint4 = DeviceMustHaveTrafficGeneratorConnected(
        speed_constraint=TrafficGeneratorSpeedMustBeGraterThan(1000))
    # AP必须有至少3个STA连接，并且STA必须有1000M以上速率的测试仪表连接
    constraint6 = ApMustHaveStaConnected(sta_constraints=[constraint4], sta_count=3)

    ap = rp.collect_device(
        "AP",
        1,
        constraints=[
            constraint4,
            constraint6
        ]
    )

    traffic_gen = rp.collect_connection_route(ap1, [constraint4])

    sta_connection = rp.collect_connection_route(ap1, [constraint6])

    for port in traffic_gen:
        print(port.parent.name)

    for connection in sta_connection:
        print(connection[0].parent.name)
        for traffic_port in connection[1]:
            print(f"    {traffic_port.name}")


    class SshServer:
        def __init__(self, ip, port, username, password):
            pass


    resource = ResourcePool()
    resource.load("test.json")
    ssh_device = resource.collect_device(device_type="ssh_server")[0]
    ssh_comm = SshServer(
        ssh_device.management["ip"],
        ssh_device.management["port"],
        ssh_device.management["username"],
        ssh_device.management["password"]
    )



