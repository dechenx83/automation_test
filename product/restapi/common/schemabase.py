"""
A Schema Type to describe the Swagger OPEN API 3.0 format
"""
from functools import wraps
import os

__allow_type = ['str', 'int', 'float', 'bool', 'dict']


def _is_allow_type(value):
    return type(value).__name__ in __allow_type


def _is_list_type(value):
    return type(value).__name__ in ['list', 'tuple']


class SchemaBase:
    required_fields = list()
    _all_fields = list()

    def __init__(self, raw_json=None):
        self.raw_json = raw_json
        if raw_json is not None:
            self.from_dict(raw_json)

    def to_dict(self):
        rv = dict()
        for key in self.__class__.__dict__:
            if key in self.__class__.__dict__ and isinstance(self.__class__.__dict__[key], property):
                rv[key] = self._value_to_dict(getattr(self, key))
        self.raw_json = rv
        return rv

    def from_dict(self, a_dict):
        self.raw_json = a_dict
        for key, value in a_dict.items():
            setattr(self, key, self._dict_to_value(key, value))

    def _dict_to_value(self, key, dict_value):
        if key in self._object_fields:
            rv = self._object_fields[key]()
            rv.from_dict(dict_value)
            return rv
        if _is_allow_type(dict_value):
            return dict_value
        if _is_list_type(dict_value):
            rv = list()
            for item in dict_value:
                rv.append(self._dict_to_value(key, item))
            return rv

    def _value_to_dict(self, value):
        if _is_allow_type(value):
            return value
        if _is_list_type(value):
            rv = list()
            for item in value:
                rv.append(self._value_to_dict(item))
            return rv
        if isinstance(value, SchemaBase):
            return value.to_dict()

    def __eq__(self, other):
        if not (other.__class__.__name__ == self.__class__.__name__ and \
                other.__class__.__module__ == self.__class__.__module__):
            return False
        for key in self.__class__.__dict__:
            if key in self.__class__.__dict__ and isinstance(self.__class__.__dict__[key], property):
                if getattr(self, key) != getattr(other, key):
                    return False
        return True


def response_schema(code, schema):
    """
    A decorator to describe an API call
    to indicate the all possible reponse of the API
    and the response Schema Type

    This decorator will add the code and schema to a func
    type (Normally the API call method), user can get the
    response Schema type from the property "responses" from
    the func(method)

    eg:
        respnse_schema = getattr(api.v1_serviceability_supportassist_post_201.responses)

    :param code: response code
    :param schema: Schema Type
    """

    def outer(func):
        if not hasattr(func, "responses"):
            setattr(func, "responses", dict())
        if code not in func.responses:
            func.responses[code] = schema

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return outer


def _get_indent(indent):
    return " " * (indent*2)


class GraphqlType:

    def __init__(self, parent=None, name=None, type_=None, array=False):
        self.parent = parent
        self.name = name
        self.type_ = type_
        self.is_array = array

    def to_query(self, indent=0):
        rv = _get_indent(indent) + "{" + os.linesep
        for field, value in self.__dict__.items():
            if field.startswith("_field_") and value is not None:
                rv += _get_indent(indent+1) + value.name + " "
                arg_list = list()
                for arg, arg_val in self.__dict__.items():
                    if arg.startswith("_arg_") and arg_val is not None:
                        arg_list.append(arg_val.to_string())
                if any(arg_list):
                    rv += "(" + ", ".join(arg_list) + ") "
                if not isinstance(value, SimpleTypeField):
                    rv += value.to_query(indent+1).lstrip()
                rv += os.linesep
        rv += _get_indent(indent) + "}"
        return rv

    def to_json(self):
        rv = dict()
        for field, value in self.__dict__.items():
            if field.startswith("_field_") and value is not None:
                field_mock_value = None
                if isinstance(value, SimpleTypeField):
                    if value.type_ == "String":
                        field_mock_value = ""
                    elif value.type_ == "Int":
                        field_mock_value  = 0
                    elif value.type_ == "Bool":
                        field_mock_value  = True
                    else:
                        field_mock_value  = ""
                else:
                    field_mock_value = value.to_json()
                if value.is_array:
                    rv[value.name] = [field_mock_value]
                else:
                    rv[value.name] = field_mock_value
        return rv


class DemoQuery(GraphqlType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_ = "DemoQuery"
        self._field_field1 = None
        self._field_field2 = None
        self._field_field3 = None

    def add_field1(self):
        self._field_field1 = SimpleTypeField(self, name="field1", type_="String", array=False)
        return self

    def add_field2(self):
        self._field_field2 = SimpleTypeField(self, name="field2", type_="String", array=False)
        return self

    def add_field3(self):
        self._field_field3 = DemoField(self, name="field3", array=False)
        return self

    @property
    def field3(self):
        return self._field_field3


class DemoField(GraphqlType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_ = "DemoField"
        self._field_name = None
        self._field_class = None
        self._arg_arg1 = None
        self._arg_arg2 = None

    def add_name(self):
        self._field_name = SimpleTypeField(name="name", type_="String")
        return self

    def add_class(self):
        self._field_class = SimpleTypeField(name="class", type="String")
        return self

    def set_arg1(self, value):
        #self._arg1_field =
        pass


class SimpleTypeField(GraphqlType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_ = "SimpleType"


class ProductInfo(SchemaBase):

    _all_fields = ["product_id", "product_name", "price", "discount", "status"]
    required_fields = ["product_id", "product_name", "price", "status"]

    def __init__(self, raw_json=None):
        self._object_fields = dict()
        self._product_id = None
        self._product_name = None
        self._price = None
        self._discount = None
        self._status = None
        super().__init__(raw_json)

    @property
    def product_id(self):
        return self._product_id

    @product_id.setter
    def product_id(self, value):
        self._product_id = value

    @property
    def product_name(self):
        return self._product_name

    @product_name.setter
    def product_name(self, value):
        self._product_name = value

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        self._price = value

    @property
    def discount(self):
        return self._discount

    @discount.setter
    def discount(self, value):
        self._discount = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value


if __name__=="__main__":
    import json
    product = ProductInfo()
    product.product_id = 1
    product.product_name = "iPhone"
    product.price = 7999
    product.discount = 0.8
    product.status = "ON_SALE"
    print(json.dumps(product.to_dict(), indent=2))