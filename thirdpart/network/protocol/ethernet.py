from abc import ABCMeta, abstractmethod

class MacAddress:
    """
    MAC 地址定义
    """
    def __init__(self, value):
        self._mac_bytes = None
        self.parse(value)

    def parse(self, value):
        if isinstance(value, bytes):
            self._mac_bytes = value
        if isinstance(value, str):
            self._mac_bytes = bytes.fromhex(value.replace(":", ""))

    def __repr__(self):
        if self._mac_bytes:
            return ":".join(["%02X" % x for x in self._mac_bytes])
        else:
            return ""

    def to_bytes(self):
        return self._mac_bytes


class Ethernet:
    """
    以太网报文
    """
    def __init__(self, value):
        self.da = None
        self.sa = None
        self.protocol = None
        self.payload = None
        self.checksum = None
        self.parse(value)

    def parse(self, value):
        if isinstance(value, str):
            value = bytes.fromhex(value)
        self.da = MacAddress(value[0:6])
        self.sa = MacAddress(value[6:12])
        self.protocol = value[12:14]
        self.payload = value[14: -4]
        self.checksum = value[-4:]

    def to_bytes(self):
        ret = b''
        ret = ret + self.da.to_bytes()
        ret = ret + self.sa.to_bytes()
        ret = ret + self.protocol
        ret = ret + self.payload
        ret = ret + self.checksum
        return ret



class SerializableObject(metaclass=ABCMeta):

    def __init__(self, value):
        self.raw_data = value
        self.parse()

    @abstractmethod
    def parse(self, value):
        pass

    @abstractmethod
    def to_bytes(self):
        pass


class TlvType(SerializableObject):

    def __init__(self, value):
        self.type = None
        self.length = None
        self.body = None
        super().__init__(value)

    def parse(self, value):
        self.type = int.from_bytes(value[0:2], byteorder='big')
        self.length = int.from_bytes(value[2:4], byteorder='big')

    def to_bytes(self):
        rv = b''
        rv += self.type.to_bytes(length=2, byteorder='big')
        rv += self.type.to_bytes(length=2, byteorder='big')
        return rv


class Properties(TlvType):

    def __init__(self, value):
        super().__init__(value)

    def parse(self, value):
        super().parse(value)
        if self.type == 1:
            self.body = value[4: 4 + self.length]
        elif self.type == 10:
            self.body = PropertiesType10(value[4: 4 + self.length])
        else:
            raise Exception(f"Unknown type {self.type}")

    def to_bytes(self):
        rv = super().to_bytes()
        if self.type == 1:
            rv += self.body
        elif self.type == 10:
            rv += self.body.to_bytes()
        else:
            raise Exception(f"Unknown type {self.type}")
        return rv


class PropertiesType10(TlvType):
    def __int__(self, value):
        super().__init__(value)

    def parse(self, value):
        super().parse(value)
        if self.type == 1:
            self.body = int.from_bytes(value[4: 4 + self.length])
        elif self.type == 2:
            self.body = value[4: 4 + self.length].decode()
        else:
            raise Exception(f"Unknown type {self.type}")

    def to_bytes(self):
        rv = super().to_bytes()
        if self.type == 1:
            rv += self.body.to_bytes(length=self.length, byteorder='big')
        elif self.type == 2:
            rv += self.body.encode()
        else:
            raise Exception(f"Unknown type {self.type}")
        return rv



if __name__ == "__main__":
    eth = Ethernet("01005E0000010000000102030800FFFFFFFFFF01020304")
    print(eth.sa)
    print(eth.da)
    print(eth.to_bytes())