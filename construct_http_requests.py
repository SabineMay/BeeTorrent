HTTP_LINE_END = "\r\n"


def construct_GET_request(host_url, user_agent):
    request = ""

    request_line = "GET / HTTP/1.1" + HTTP_LINE_END
    request += request_line

    host_line = "Host: " + host_url + HTTP_LINE_END
    request += host_line

    user_agent_line = "User-Agent: " + user_agent + HTTP_LINE_END
    request += user_agent_line

    accept_line = "Accept: */*" + HTTP_LINE_END
    request += accept_line

    accept_encoding_line = "Accept-Encoding: identity" + HTTP_LINE_END
    request += accept_encoding line

    connection_line = "Connection: Keep-Alive" + HTTP_LINE_END
    request += connection_line

    request += HTTP_LINE_END

    return request
