"""
CODEDOM
"""
import os
from abc import abstractmethod, ABCMeta


class CodeDomError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Expression(metaclass=ABCMeta):
    """
    Expression Base Class
    """
    @abstractmethod
    def to_code(self):
        pass


class VariableInvokeExpression(Expression):
    """
    Variable Invoke Expression
    """
    def __init__(self, var_name):
        self.var_name = var_name

    def to_code(self):
        return self.var_name


class ConstInvokeExpression(Expression):
    """
    Const Invoke
    """
    def __init__(self, const_value):
        self.const_value = const_value

    def to_code(self):
        if isinstance(self.const_value, int) or isinstance(self.const_value, float):
            return str(self.const_value)
        elif self.const_value is None:
            return "None"
        else:
            return f"\"{self.const_value}\""


class NoneExpression(ConstInvokeExpression):
    """
    None Expression
    """
    def __init__(self):
        super().__init__(None)


class TrueExpression(ConstInvokeExpression):
    """
    True Expression
    """
    def __init__(self):
        super().__init__(True)


class FalseExpression(ConstInvokeExpression):
    """
    False Expression
    """
    def __init__(self):
        super().__init__(False)


class AssignExpression(Expression):
    """
    Assign Value
    """
    def __init__(self, left_expression, right_expression):
        if not isinstance(left_expression, Expression):
            raise CodeDomError("left expression should be an expression instance")
        if not isinstance(right_expression, Expression):
            raise CodeDomError("right expression should be an expression instance")
        self.left_expression = left_expression
        self.right_expression = right_expression

    def to_code(self):
        return f"{self.left_expression.to_code()} = {self.right_expression.to_code()}"


class FieldInvokeExpression(Expression):
    """
    Object/Instance Field Invoke Expression
    """
    def __init__(self, instance_expression, field_expression):
        if not isinstance(instance_expression, Expression):
            raise CodeDomError("Instance name should be an expression")
        if not isinstance(field_expression, Expression):
            raise CodeDomError("Field should be an expression")
        self.instance_expression = instance_expression
        self.field_expression = field_expression

    def to_code(self):
        return f"{self.instance_expression.to_code()}.{self.field_expression.to_code()}"


class MethodInvokeExpression(Expression):
    """
    Method invoke Expression
    """
    def __init__(self, method_name, *args, **kwargs):
        for arg in args:
            if not isinstance(arg, Expression):
                raise CodeDomError("Argument should be expression")
        self.method_name = method_name
        self.arg_list = list()
        for arg in args:
            self.arg_list.append(arg)
        self.obj = kwargs.get("instance", None)

    def to_code(self):
        if self.obj:
            return f"{self.obj.to_code()}.{self.method_name}({', '.join([x.to_code() for x in self.arg_list])})"
        else:
            return f"{self.method_name}({', '.join([x.to_code() for x in self.arg_list])})"


class InstanceCreationExpression(Expression):
    """
    Create Instance
    """
    def __init__(self, class_name, *args):
        for arg in args:
            if not isinstance(arg, Expression):
                raise CodeDomError("Argument should be expression")
        self.class_name = class_name
        self.arg_list = args

    def to_code(self):
        return f"{self.class_name}({', '.join([x.to_code() for x in self.arg_list])})"


class DictInvokeExpression(Expression):
    """
    Dict invoke expression
    """
    def __init__(self, dict_name, key_expression):
        self.dict_name = dict_name
        self.key_name = key_expression

    def to_code(self):
        if not isinstance(self.key_name, Expression):
            raise CodeDomError("key should be an expression")
        return f"{self.dict_name}[{self.key_name.to_code()}]"


class ParameterDefineExpression(Expression):
    """
    Parameter definition expression
    """
    def __init__(self, name, default_value=None):
        self.name = name
        self.default_value = default_value
        if default_value is not None and not isinstance(default_value, Expression):
            raise CodeDomError("Parameter default value should be an expression")

    def to_code(self):
        ret = self.name
        if self.default_value is not None:
            return f"{ret}={self.default_value.to_code()}"
        else:
            return ret


class BinaryOperatorExpression(Expression):
    """
    Binary Operator Expression
    """
    def __init__(self, op_expression1, op_expression2, operator):
        if not isinstance(op_expression1, Expression):
            raise CodeDomError("expression1 should be an expression")
        if not isinstance(op_expression2, Expression):
            raise CodeDomError("expression2 should be an expression")
        self.expression1 = op_expression1
        self.expression2 = op_expression2
        self.operator = operator

    def to_code(self):
        return f"{self.expression1.to_code()} {self.operator} {self.expression2.to_code()}"


class ListExpression(Expression):
    """
    List Expression
    """
    def __init__(self, expression_list):
        self.expression_list = expression_list

    def to_code(self):
        rv_list = ", ".join([exp.to_code() for exp in self.expression_list])
        return f"[{rv_list}]"


class SelfExpression(Expression):
    """
    self
    """
    def to_code(self):
        return "self"

def _get_indent(indent):
    return "    " * indent


class Statement(metaclass=ABCMeta):
    """
    Statement Base
    """

    def to_code(self, indent=0):
        return self._to_code(indent) + "\n"

    @abstractmethod
    def _to_code(self, indent=0):
        pass


class ExpressionStatement(Statement):
    """
    """
    def __init__(self, expression):
        if not isinstance(expression, Expression):
            raise CodeDomError("expression should be an expression")
        self.expression = expression

    def _to_code(self, indent=0):
        return f"{_get_indent(indent)}{self.expression.to_code()}"


class BlankStatement(Statement):

    def _to_code(self, indent=0):
        return ""

class ImportStatement(Statement):
    """
    """
    def __init__(self, packages: list, from_package=None, _as=None):
        self.packages = packages
        self.from_package = from_package
        self.as_ = _as

    def _to_code(self, indent=0):
        ret = f"import {', '.join(self.packages)}"
        if self.from_package:
            ret = f"from {self.from_package} {ret}"
        if self.as_ is not None:
            ret += f" as {self.as_}"
        return f"{_get_indent(indent)}{ret}"


class ReturnStatement(Statement):
    """
    """
    def __init__(self, expression):
        if not isinstance(expression, Expression):
            raise CodeDomError("Return expression should be an expression")
        self.expression = expression

    def _to_code(self, indent=0):
        return f"{_get_indent(indent)}return {self.expression.to_code()}"


class MethodDefineStatement(Statement):
    """
    """
    def __init__(self, method_name, *args):
        self.method_name = method_name
        self.decorators = list()
        self.args = list()
        self.doc = None
        for arg in args:
            self.args.append(arg)
        self.body = list()

    def _to_code(self, indent=0):
        ret = ""
        for decorator in self.decorators:
            ret += f"{_get_indent(indent)}@{decorator.to_code()}\n"
        ret += f"{_get_indent(indent)}def {self.method_name}({', '.join([x.to_code() for x in self.args])}):\n"
        if self.doc is not None:
            ret += self.doc.to_code(indent+1)
        for segment in self.body:
            ret += segment.to_code(indent+1)
        return ret


class ClassDefineStatement(Statement):
    """
    """
    def __init__(self, class_name, parent=None, doc=None):
        self.class_name = class_name
        self.parent = parent
        self.decorators = list()
        self.body = list()
        self.doc = doc

    def _to_code(self, indent=0):
        ret = ""
        for decorator in self.decorators:
            ret += f"{_get_indent(indent)}@{decorator.to_code()}\n"
        ret += f"{_get_indent(indent)}class {self.class_name}"
        if self.parent is not None:
            ret += f"({self.parent})"
        ret += f":\n"
        if self.doc is not None:
            ret += self.doc.to_code(indent+1)
        for segment in self.body:
            ret += segment.to_code(indent+1)
        return ret


class DocStatement(Statement):
    def __init__(self, lines):
        self.lines = lines

    def _to_code(self, indent=0):
        rv = f"{_get_indent(indent)}\"\"\"" + "\n"
        for line in self.lines:
            rv += f"{_get_indent(indent)}{line}\n"
        rv += f"{_get_indent(indent)}\"\"\""
        return rv


class IfStatement(Statement):
    def __init__(self, condition):
        self.condtion = condition
        self.true_statements = list()
        self.false_statements = list()

    def _to_code(self, indent=0):
        rv = f"{_get_indent(indent)}if {self.condtion.to_code()}:\n"
        for statement in self.true_statements:
            rv += statement.to_code(indent+1)
        rv += f"{_get_indent(indent)}else:\n"
        for statement in self.false_statements:
            rv += statement.to_code(indent+1)
        return rv


class PassStatement(Statement):

    def _to_code(self, indent=0):
        return f"{_get_indent(indent)}pass"


if __name__=="__main__":
    mh = MethodDefineStatement("add")
    mh.decorators.append(VariableInvokeExpression("check"))
    mh.args.append(ParameterDefineExpression("a"))
    mh.args.append(ParameterDefineExpression("b"))
    mh.body.append(
        ExpressionStatement(
            AssignExpression(
                VariableInvokeExpression("ret"),
                BinaryOperatorExpression(
                    VariableInvokeExpression("a"),
                    VariableInvokeExpression("b"),
                    "+"))))
    mh.body.append(
        ReturnStatement(
            VariableInvokeExpression("ret")
        )
    )
    print(mh.to_code())
