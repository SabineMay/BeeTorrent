HTTP_LINE_END = "\r\n"
USER_AGENT = "duTorrent/4.0"

def construct_GET_request(host_domain, host_port, path):
    request = ""

    request_line = "GET " + path + " HTTP/1.1" + HTTP_LINE_END
    request += request_line

    host_line = "Host: " + host_domain + ":" + str(host_port) + HTTP_LINE_END
    request += host_line
    
    connection_line = "Connection: Keep-Alive" + HTTP_LINE_END
    request += connection_line

    user_agent_line = "User-Agent: " + USER_AGENT + HTTP_LINE_END
    request += user_agent_line

    accept_line = "Accept: */*" + HTTP_LINE_END
    request += accept_line

    accept_encoding_line = "Accept-Encoding: identity" + HTTP_LINE_END
    request += accept_encoding_line

    request += HTTP_LINE_END
    print(request)

    return request.encode()

def create_path(base_path, params):
    path = base_path

    first_param = True

    for param in params:
        param_value = params[param]

        if first_param:
            path += "?"
            first_param = False
        else:
            path += "&"
        
        path += param
        path += "="
        path += str(param_value)
    
    return path