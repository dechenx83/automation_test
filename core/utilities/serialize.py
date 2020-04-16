import importlib
import json
__VAL_TYPE = ['str', 'int', 'float', 'bool']
__LIST_TYPE = ['list', 'set', 'tuple']



class SerializationError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


def serialize_object(obj):
    ret_obj = dict()
    ret_obj["module"] = obj.__class__.__module__
    ret_obj["class_name"] = obj.__class__.__name__
    if ret_obj["class_name"] == 'NoneType':
        # 判断字段值是否是空
        pass
    elif ret_obj["class_name"] in __VAL_TYPE:
        # 判断字段值是否是简单值类型
        ret_obj['value'] = obj
    elif ret_obj["class_name"] in __LIST_TYPE:
        # 判断字段值是否是列表类型
        ret_obj['value'] = list()
        for item in obj:
            ret_obj['value'].append(serialize_object(item))
    elif ret_obj["class_name"] == 'dict':
        # 判断字段值是否是字典类型
        ret_obj['value'] = dict()
        for k, v in obj.items():
            ret_obj['value'][k] = serialize_object(v)
    else:
        # 非语言内定义类型, 遍历所有字段
        ret_obj['value'] = dict()
        for field, value in obj.__dict__.items():
            ret_obj['value'][field] = serialize_object(value)

    return ret_obj


def deserialize_object(json_obj):
    """
    反序列化对象
    """
    #检查被反序列化对象的格式是否正确
    if "class_name" not in json_obj.keys():
        raise SerializationError("no key 'class_name'")
    if json_obj['class_name'] == 'NoneType':
        return None
    if "value" not in json_obj.keys():
        raise  SerializationError("no key 'value'")
    if json_obj['class_name'] in __VAL_TYPE:
        #值类型直接返回value
        return json_obj['value']
    elif json_obj['class_name'] in __LIST_TYPE:
        #如果是列表类型则生成列表，并根据具体的类型返回
        ret = list()
        for item in json_obj['value']:
            ret.append(deserialize_object(item))
        if json_obj['class_name'] == 'set':
            return set(ret)
        elif json_obj['class_name'] == 'tuple':
            return tuple(ret)
        else:
            return ret
    elif json_obj['class_name'] == 'dict':
        #字典类型
        ret = dict()
        for key, value in json_obj['value'].items():
            ret[key] = deserialize_object(value)
        return ret
    else:
        #自定义类型
        module = importlib.import_module(json_obj['module'])
        if not hasattr(module, json_obj['class_name']):
            raise SerializationError("module %s doesn't have type %s" % (json_obj['module'], json_obj['class_name']))
        ret = getattr(module, json_obj['class_name'])()
        for key, value in json_obj['value'].items():
            setattr(ret, key, deserialize_object(value))
        return ret




if __name__=='__main__':
    class TestClass2:
        def __init__(self):
            self.list = list()
            self.list.append("123")
            self.list.append([1,2,3])
            self.list.append({"f1":2, "f2":"123"})

    class TestClass:
        def __init__(self):
            self.field1 = 123
            self.index= TestClass2()
            self.description ="class"

    tc = TestClass()
    s = serialize_object(tc)
    print(json.dumps(s, indent=4))




