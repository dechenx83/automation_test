import yaml
from core.utilities.codedom import *

with open("openapi.yaml") as file:
    x=yaml.load(file)


class RestApiCodeGenError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Schema:
    """
    OPEN API Schema 解析/封装代码生成类
    """
    def __init__(self, name, schema_data):
        self.schema_data = schema_data
        self.name = name
        self.code_body = list()

    def gen_dom(self):
        # 类定义
        class_def = ClassDefineStatement(self.name)
        if "properties" not in self.schema_data:
            raise RestApiCodeGenError("properties not in schema definition")

        # 类方法 __init__
        init_def = MethodDefineStatement("__init__", VariableInvokeExpression("self"))

        #定义to_json方法
        to_json_def = MethodDefineStatement("to_json", VariableInvokeExpression("self"))
        to_json_def.body.append(
            ExpressionStatement(
                AssignExpression(
                    VariableInvokeExpression("ret"),
                    MethodInvokeExpression("dict")
                )
            )
        )

        #定义parse方法
        parse_def = MethodDefineStatement("parse", VariableInvokeExpression("json_str"))
        parse_def.decorators.append(
            VariableInvokeExpression("staticmethod")
        )
        parse_def.body.append(
            ExpressionStatement(
                AssignExpression(
                    VariableInvokeExpression("json_obj"),
                    MethodInvokeExpression(
                        "loads", VariableInvokeExpression("json_str"),
                        instance=VariableInvokeExpression("json")
                    )
                )
            )
        )
        parse_def.body.append(
            ExpressionStatement(
                AssignExpression(
                    VariableInvokeExpression("ret"),
                    InstanceCreationExpression(
                        self.name
                    )
                )
            )
        )

        #是否有require的字段
        require_field = self.schema_data.get("required", [])

        # 定义字段和初始化
        for field, value in self.schema_data["properties"].items():
            default_value = NoneExpression()
            if value['type'] == "array":
                default_value = MethodInvokeExpression("list")
            init_def.body.append(
                ExpressionStatement(
                    AssignExpression(
                        FieldInvokeExpression(
                            VariableInvokeExpression("self"),
                            VariableInvokeExpression(field)
                        ),
                        default_value
                    )
                )
            )
            if field in require_field:
                to_json_def.body.append(
                    ExpressionStatement(
                        MethodInvokeExpression(
                            "_check_none_and_raise_exception",
                            FieldInvokeExpression(
                                VariableInvokeExpression("self"),
                                VariableInvokeExpression(field.lower())
                            ),
                            ConstInvokeExpression(f"{field} is required")
                        )
                    )
                )
                parse_def.body.append(
                    ExpressionStatement(
                        MethodInvokeExpression(
                            "_check_key_and_raise_exception",
                            ConstInvokeExpression(field),
                            VariableInvokeExpression("json_obj")
                        )
                    )
                )
            to_json_def.body.append(
                ExpressionStatement(
                    AssignExpression(
                        DictInvokeExpression("ret", ConstInvokeExpression(field)),
                        FieldInvokeExpression(
                            VariableInvokeExpression("self"),
                            VariableInvokeExpression(field.lower())
                        )
                    )
                )
            )
            if field in require_field:
                json_get = MethodInvokeExpression(
                    "get",
                    ConstInvokeExpression(field),
                    instance=VariableInvokeExpression("json"))
            else:
                json_get = MethodInvokeExpression(
                    "get",
                    ConstInvokeExpression(field),
                    NoneExpression(),
                    instance=VariableInvokeExpression("json"))

            parse_def.body.append(
                ExpressionStatement(
                    AssignExpression(
                        FieldInvokeExpression(
                            VariableInvokeExpression("ret"),
                            VariableInvokeExpression(field.lower())
                        ),
                        json_get
                    )
                )
            )
        to_json_def.body.append(
            ReturnStatement(VariableInvokeExpression("ret"))
        )

        parse_def.body.append(
            ReturnStatement(VariableInvokeExpression("ret"))
        )

        class_def.body.append(init_def)
        class_def.body.append(to_json_def)
        class_def.body.append(parse_def)

        self.code_body.append(class_def)


for key, schema in x['components']['schemas'].items():
    s = Schema(key, schema)
    s.gen_dom()
    for c in s.code_body:
        print(c.to_code())