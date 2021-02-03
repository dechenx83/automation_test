"""
The Rest Schema Creator to create the schema framework
and API Call Method
"""
import re
from .settings import SETTING
from .openapi import change_to_camel
from .creator import ObjectCreator
from .openapi import SwaggerLoader, ReferenceSchemaDataType, ArraySchemaDataType, \
    ObjectSchemaDataType, get_internal_response_schema_name
from .util import get_parameters
import core.utilities.codedom as codedom

_SCHEMA_BASE = [".schemabase", "SchemaBase"]
_CODE_BASE = "product.restapi.common"


class RestSchemaClassCreator(ObjectCreator):

    def __init__(self, swagger: SwaggerLoader):
        super().__init__(swagger)

    def generate(self):
        super().generate()

        # import
        import_state = codedom.ImportStatement([_SCHEMA_BASE[1], "response_schema"],
                                               from_package=_CODE_BASE + _SCHEMA_BASE[0])
        self.code_statements.append(import_state)

        # class definition
        for file in self.swagger.schema_data.keys():
            for schema, s_value in self.swagger.schema_data[file].schema_mapping.items():
                self.code_statements.append(RestSchemaClassCreator.get_class(schema, s_value))

    @staticmethod
    def get_class(schema, s_value):
        class_def = codedom.ClassDefineStatement(class_name=schema.split("/")[-1], parent=_SCHEMA_BASE[1])
        class_def.doc = codedom.DocStatement([s_value.description])

        # all_fields
        all_field_exp = codedom.ListExpression(
            [codedom.ConstInvokeExpression(field) for field in s_value.properties.keys()])
        req_field_exp = codedom.ListExpression([codedom.ConstInvokeExpression(field) for field in s_value.required])
        class_def.body.append(
            codedom.ExpressionStatement(
                codedom.AssignExpression(codedom.VariableInvokeExpression("_all_fields"), all_field_exp)
            )
        )
        class_def.body.append(
            codedom.ExpressionStatement(
                codedom.AssignExpression(codedom.VariableInvokeExpression("required_fields"), req_field_exp)
            )
        )
        class_def.body.append(codedom.BlankStatement())
        # __init__
        init_method = codedom.MethodDefineStatement("__init__")
        init_method.args.append(codedom.SelfExpression())
        init_method.args.append(codedom.ParameterDefineExpression("raw_json", codedom.NoneExpression()))
        # add object type dict
        init_method.body.append(
            codedom.ExpressionStatement(
                codedom.AssignExpression(
                    codedom.FieldInvokeExpression(
                        codedom.SelfExpression(),
                        codedom.VariableInvokeExpression("_object_fields")
                    ),
                    codedom.InstanceCreationExpression("dict")
                )
            )
        )
        for p, p_value in s_value.properties.items():
            if isinstance(p_value, ReferenceSchemaDataType):
                ref_cls_name = p_value.ref.split("/")[-1]
            else:
                continue
            init_method.body.append(
                codedom.ExpressionStatement(
                    codedom.AssignExpression(
                        codedom.FieldInvokeExpression(
                            codedom.SelfExpression(),
                            codedom.DictInvokeExpression("_object_fields", codedom.ConstInvokeExpression(p))
                        ),
                        codedom.VariableInvokeExpression(ref_cls_name)
                    )
                )
            )
        # add object field list
        for p, p_value in s_value.properties.items():
            init_method.body.append(
                codedom.ExpressionStatement(
                    codedom.AssignExpression(
                        codedom.FieldInvokeExpression(
                            codedom.SelfExpression(),
                            codedom.VariableInvokeExpression(f"_{p}")
                        ),
                        codedom.InstanceCreationExpression("list") if isinstance(p_value, ArraySchemaDataType) else
                        codedom.NoneExpression()
                    )
                )
            )
        # call suport init
        super_init = codedom.MethodInvokeExpression("__init__", codedom.VariableInvokeExpression("raw_json"),
                                                    instance=codedom.MethodInvokeExpression("super"))
        init_method.body.append(codedom.ExpressionStatement(super_init))
        class_def.body.append(init_method)

        # End of Init
        # property
        for p, p_value in s_value.properties.items():
            prop_field = codedom.MethodDefineStatement(p, codedom.SelfExpression())
            prop_field.decorators.append(codedom.VariableInvokeExpression("property"))
            prop_field.body.append(
                codedom.ReturnStatement(
                    codedom.FieldInvokeExpression(
                        codedom.SelfExpression(),
                        codedom.VariableInvokeExpression(f"_{p}")
                    )
                )
            )
            prop_field_set = codedom.MethodDefineStatement(p, codedom.SelfExpression(),
                                                           codedom.ParameterDefineExpression("value"))
            prop_field_set.decorators.append(
                codedom.FieldInvokeExpression(
                    codedom.VariableInvokeExpression(p),
                    codedom.VariableInvokeExpression("setter")
                )
            )
            prop_field_set.body.append(
                codedom.ExpressionStatement(
                    codedom.AssignExpression(
                        codedom.FieldInvokeExpression(
                            codedom.SelfExpression(),
                            codedom.VariableInvokeExpression(f"_{p}")
                        ),
                        codedom.VariableInvokeExpression("value")
                    )
                )
            )
            class_def.body.append(prop_field)
            class_def.body.append(prop_field_set)

        return class_def


class ApiCallGenerator(ObjectCreator):

    def __init__(self, swagger: SwaggerLoader, *args, **kwargs):
        super().__init__(swagger)
        self.name = kwargs.get("name")

    def generate(self):
        super().generate()
        # Import
        self.code_statements.append(
            codedom.ImportStatement([SETTING["api_base_file"][1]], SETTING["api_base_file"][0])
        )
        self.code_statements.append(
            codedom.ImportStatement(["*"], ".schemas")
        )
        self.code_statements.append(codedom.BlankStatement())
        self.code_statements.append(codedom.BlankStatement())

        # class definition
        class_def = codedom.ClassDefineStatement(f"{change_to_camel(self.name)}RestCall",
                                                 parent=SETTING["api_base_file"][1])

        # init method
        init_method = codedom.MethodDefineStatement("__init__", codedom.SelfExpression(),
                                                    codedom.ParameterDefineExpression("host"),
                                                    codedom.ParameterDefineExpression("port"),
                                                    codedom.ParameterDefineExpression("auth"))

        # get server url
        url = self.swagger.description_data[self.swagger.main_file]['servers'][0]['url']
        protocol = "http"
        if url.lower().startswith("https"):
            protocol = "https"
        base_url = re.findall("http://.+?/(.+)", url)
        if not any(url):
            base_url = re.findall("https://.+?/(.+)", url)
        if not any(url):
            base_url = url
        else:
            base_url = base_url[0]
        init_method.body.append(
            codedom.ExpressionStatement(
                codedom.MethodInvokeExpression(
                    "__init__",
                    codedom.VariableInvokeExpression("host"),
                    codedom.VariableInvokeExpression("port"),
                    codedom.ConstInvokeExpression(base_url),
                    codedom.VariableInvokeExpression("auth"),
                    codedom.ConstInvokeExpression(protocol),
                    instance=codedom.InstanceCreationExpression("super")
                )
            )
        )

        class_def.body.append(init_method)

        # APIs
        for api, api_obj in self.swagger.api_list.items():
            for sub_item in self._gen_api(url, api, api_obj):
                class_def.body.append(sub_item)
        self.code_statements.append(class_def)

    def _gen_api(self, url, api, api_obj):
        rv = list()
        for method in api_obj.methods:
            rv.append(self._get_api_method(url, api, api_obj, method))
        return rv

    def _get_api_method(self, url, api, api_obj, method):
        method_name = api.strip('/').replace('/', '_').replace("-", "_").replace("{", "").replace("}", "")
        method_name += f"_{method.method}"
        path_param, query_param, query_param_option = get_parameters(api_obj, method)

        # define the method
        rv = codedom.MethodDefineStatement(method_name,
                                           codedom.SelfExpression())
        if method.method not in ["get", "delete"]:
            rv.args.append(
                codedom.ParameterDefineExpression("body")
            )
        for param in path_param:
            rv.args.append(
                codedom.ParameterDefineExpression(param)
            )
        for param in query_param:
            rv.args.append(
                codedom.ParameterDefineExpression(param.replace("$", ""))
            )
        for param in query_param_option:
            rv.args.append(
                codedom.ParameterDefineExpression(param.replace("$", ""), codedom.NoneExpression())
            )
        rv.doc = codedom.DocStatement([
            f"Summary: {method.summary}",
            f"Description: {method.description}",
            f"URI: {url + '/' + api.strip('/')}",
            f"METHOD: {method.method}"
        ])

        # response decorator
        for code, response in method.responses.items():
            if response.content is not None and isinstance(response.content, ObjectSchemaDataType):
                schema_name = get_internal_response_schema_name(api, method.method, code)
                response_obj = \
                    self.swagger.schema_data[self.swagger.main_file]. \
                    schema_mapping[f"/components/schemas/{schema_name}"]
            else:
                response_obj = self.swagger.get_response_schema(response)
            if response_obj:
                rv.decorators.append(codedom.MethodInvokeExpression(
                    "response_schema",
                    codedom.ConstInvokeExpression(str(code)),
                    codedom.VariableInvokeExpression(response_obj.name)
                ))

        # end of sign definition

        # body definition
        url_var = codedom.ExpressionStatement(
            codedom.AssignExpression(
                codedom.VariableInvokeExpression("api_path"),
                codedom.ConstInvokeExpression(api.strip('/'))
            )
        )
        rv.body.append(url_var)
        for param in path_param:
            rv.body.append(
                codedom.ExpressionStatement(
                    codedom.AssignExpression(
                        codedom.VariableInvokeExpression("api_path"),
                        codedom.MethodInvokeExpression(
                            "replace",
                            codedom.ConstInvokeExpression(r"{" + param + "}"),
                            codedom.VariableInvokeExpression(param),
                            instance=codedom.VariableInvokeExpression("api_path")
                        )
                    )
                )
            )
        # construct the query param
        if any(query_param) or any(query_param_option):
            rv.body.append(
                codedom.ExpressionStatement(
                    codedom.AssignExpression(
                        codedom.VariableInvokeExpression("query_param_list"),
                        codedom.InstanceCreationExpression("list")
                    )
                )
            )
            for param in query_param + query_param_option:
                rv.body.append(
                    codedom.ExpressionStatement(
                        codedom.MethodInvokeExpression(
                            "append",
                            codedom.BinaryOperatorExpression(
                                codedom.ConstInvokeExpression(param + "="),
                                codedom.VariableInvokeExpression(param.replace("$", "")),
                                "+"
                            ),
                            instance=codedom.VariableInvokeExpression("query_param_list")
                        )
                    )
                )
            rv.body.append(
                codedom.ExpressionStatement(
                    codedom.AssignExpression(
                        codedom.VariableInvokeExpression("api_path"),
                        codedom.BinaryOperatorExpression(
                            codedom.VariableInvokeExpression("api_path"),
                            codedom.ConstInvokeExpression("?"),
                            "+"
                        )
                    )
                )
            )
            rv.body.append(
                codedom.ExpressionStatement(
                    codedom.AssignExpression(
                        codedom.VariableInvokeExpression("api_path"),
                        codedom.BinaryOperatorExpression(
                            codedom.VariableInvokeExpression("api_path"),
                            codedom.MethodInvokeExpression(
                                "join",
                                codedom.VariableInvokeExpression("query_param_list"),
                                instance=codedom.ConstInvokeExpression("&")
                            ),
                            "+"
                        )
                    )
                )
            )

        # api call
        call_method = codedom.MethodInvokeExpression(
            method.method.lower(),
            codedom.VariableInvokeExpression("api_path"),
            instance=codedom.FieldInvokeExpression(
                codedom.SelfExpression(),
                codedom.VariableInvokeExpression("api")
            )
        )
        if method.method not in ['get', 'delete']:
            # check body
            check_state = codedom.IfStatement(
                codedom.MethodInvokeExpression(
                    "isinstance",
                    codedom.VariableInvokeExpression("body"),
                    codedom.VariableInvokeExpression("SchemaBase")
                )
            )
            check_state.true_statements.append(
                codedom.ExpressionStatement(
                    codedom.AssignExpression(
                        codedom.VariableInvokeExpression("call_data"),
                        codedom.MethodInvokeExpression(
                            "to_dict",
                            instance=codedom.VariableInvokeExpression("body")
                        )
                    )
                )
            )
            check_state.false_statements.append(
                codedom.ExpressionStatement(
                    codedom.AssignExpression(
                        codedom.VariableInvokeExpression("call_data"),
                        codedom.VariableInvokeExpression("body")
                    )
                )
            )
            rv.body.append(check_state)
            call_method.arg_list.append(
                codedom.ParameterDefineExpression("data", codedom.VariableInvokeExpression("call_data"))
            )
        rv.body.append(
            codedom.ExpressionStatement(
                codedom.AssignExpression(
                    codedom.VariableInvokeExpression("response"),
                    call_method
                )
            )
        )
        rv.body.append(
            codedom.ReturnStatement(codedom.VariableInvokeExpression("response"))
        )

        return rv
