"""
数据暂存
"""


class DataPool:
    def __init__(self):
        self.data = dict()

    def save(self, key, value):
        self.data[key] = value

    def remove(self, key):
        self.data.pop(key)

    def exist(self, key):
        return key in self.data