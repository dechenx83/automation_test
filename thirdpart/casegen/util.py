

def get_parameters(api_obj, method):
    path_param = list()
    query_param = list()
    query_param_option = list()
    for param in api_obj.parameters:
        if param.in_ == "path":
            path_param.append(param.name)
        elif param.in_ == "query":
            if param.required:
                query_param.append(param.name)
            else:
                query_param_option.append(param.name)
    for param in method.parameters:
        if param.in_ == "path":
            path_param.append(param.name)
        elif param.in_ == "query":
            if param.required:
                query_param.append(param.name)
            else:
                query_param_option.append(param.name)
    return path_param, query_param, query_param_option