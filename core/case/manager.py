"""
Test case manager
Provide the method to scan the test cases.
"""

from importlib import import_module
import os
import json
import ast


def load_cases(package, case_tree):
    """
    Load the test cases by import.
    Should ensure all cases have no gram issue.
    :param package: The case root package name
    :param case_tree: the dict() type to store the test
    :return:
    """
    module = import_module(package)
    if module.__spec__.origin is None:
        return
    # 这个包是一个文件夹，我们才继续查找其所包含的文件
    if os.path.basename(module.__spec__.origin) == "__init__.py":
        case_tree["sub_module"] = list()
        case_tree["cases"] = list()
        module_path = os.path.dirname(module.__spec__.origin)
        for file in os.listdir(module_path):
            if file == "__pycache__":
                continue
            if os.path.isdir(os.path.join(module_path, file)):
                # 如果是一个子文件夹，则代表可能是一个子包，递归查找
                sub_module = dict()
                sub_module["module"] = package + "." + file
                case_tree["sub_module"].append(sub_module)
                load_cases(package + "." + file, sub_module)
            else:
                # 如果是一个py文件，则动态引用，并且查找是否有父类为TestCaseBase的类
                if os.path.splitext(file)[1] == ".py":
                    case_module_name = package + "." + os.path.splitext(file)[0]
                    try:
                        # 测试用例如果有语法错误会导致导入异常，需要catch
                        case_module = import_module(case_module_name)
                    except:
                        continue
                    for k, v in case_module.__dict__.items():
                        if hasattr(v, "__base__") and v.__base__.__name__ == "TestCaseBase":
                            case_info = dict()
                            case_info['name'] = f"{case_module_name}.{v.__name__}"
                            get_case_info(v, case_info)
                            case_tree["cases"].append(case_info)


def get_case_info(case, case_info):
    case_info['priority'] = getattr(case, "priority", 999)
    case_info['test_type'] = getattr(case, "test_type", "")
    case_info['feature_name'] = getattr(case, "feature_name", "")
    case_info['testcase_id'] = getattr(case, "testcase_id", "")
    case_info['pre_tests'] = getattr(case, "pre_tests", [])
    case_info['skip_if_high_priority_failed'] = getattr(case, "skip_if_high_priority_failed", False)
    case_info['doc'] = getattr(case, "__doc__", "")


def load_case_ast(path, case_tree, basepath):
    """
    Load the test cases by AST mode.
    :param path: Absolute test case path
    :param case_tree: case tree dict() object
    :param basepath: The base path of the test case
    :return:
    """
    case_tree["cases"] = list()
    case_tree["sub_modules"] = list()
    for file in os.listdir(path):
        if file == "__pycache__":
            continue
        if os.path.isdir(os.path.join(path, file)):
            sub_module = dict()
            sub_module["name"] = path.replace("/", ".").replace("\\", ".") + "." + file
            sub_module["name"] = sub_module["name"][len(basepath):]
            case_tree["sub_modules"].append(sub_module)
            load_case_ast(os.path.join(path, file), sub_module, basepath)
        elif os.path.splitext(file)[1] == ".py":
            case_file_name = os.path.join(path, file)
            case_moudule_name = os.path.splitext(case_file_name)[0].replace("/", ".").replace("\\", ".")
            case_moudule_name = case_moudule_name[len(basepath):]
            with open(case_file_name) as case_file:
                file_ast = ast.parse(case_file.read())
            if file_ast:
                for astobj in file_ast.body:
                    if isinstance(astobj, ast.ClassDef) and hasattr(astobj, "bases"):
                        for base_cls in astobj.bases:
                            if base_cls.id == "TestCaseBase":
                                case_info = dict()
                                case_info["name"] = case_moudule_name + "." + astobj.name
                                get_ast_case_info(astobj, case_info)
                                case_tree['cases'].append(case_info)


def get_ast_case_info(case, case_info):
    case_info['priority'] = 999
    case_info['test_type'] = ""
    case_info['feature_name'] = ""
    case_info['testcase_id'] = ""
    case_info['pre_tests'] = ""
    case_info['skip_if_high_priority_failed'] = ""
    case_info['doc'] = ""
    for decorator in case.decorator_list:
        if decorator.func.id == "case":
            for keyword in decorator.keywords:
                case_info[keyword.arg] = getattr(keyword.value, keyword.value._fields[0], None)

    if isinstance(case.body[0], ast.Expr):
        case_info['doc'] = getattr(case.body[0].value, case.body[0].value._fields[0] , "")

if __name__ == '__main__':
    cases = dict()
    cases["module"] = "product.testcase"
    load_case_ast("/Users/lilen/PycharmProjects/autoframework/product/testcase",
                  cases, "/Users/lilen/PycharmProjects/autoframework/")
    print(json.dumps(cases, indent=2))

