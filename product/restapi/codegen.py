
from thirdpart.casegen.schemacreator import RestSchemaClassCreator, ApiCallGenerator
from thirdpart.casegen.openapi import SwaggerLoader

loader = SwaggerLoader()
loader.load(["product.yaml"])
schema_creator = RestSchemaClassCreator(loader)
schema_creator.generate()
caller_creator = ApiCallGenerator(loader, name="Product")
caller_creator.generate()


with open("schemas.py", mode="w") as file:
    for statement in schema_creator.code_statements:
        file.write(statement.to_code())
        file.flush()


with open("caller.py", mode="w") as file:
    for statement in caller_creator.code_statements:
        file.write(statement.to_code())
        file.flush()