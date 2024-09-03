
HTTP_CODES = {200: 'Ok'}


def unquote(string):
    if not string:
        return ""

    if isinstance(string, str):
        string = string.encode("utf-8")

    bits = string.split(b"%")
    if len(bits) == 1:
        return string.decode("utf-8")

    res = bytearray(bits[0])
    append = res.append
    extend = res.extend

    for item in bits[1:]:
        try:
            append(int(item[:2], 16))
            extend(item[2:])
        except KeyError:
            append(b"%")
            extend(item)

    return bytes(res).decode("utf-8")


def parse_query_bytes(query_string):
    if len(query_string) == 0:
        return {}
    query_params_string = query_string.split(b'&')
    query_params = {}
    for param_string in query_params_string:
        param = param_string.split(b'=')
        key = param[0].decode("utf-8").replace('+', ' ')
        key = unquote(key)
        if len(param) == 1:
            value = b''
        else:
            value = param[1].decode("utf-8").replace('+', ' ')
            value = unquote(value)
        query_params[key] = value
    return query_params


def make_response(html, http_code=200, content_type="text/html"):
    response = "HTTP/1.0 " + str(http_code) + " " + HTTP_CODES.get(http_code) + "\r\n"
    response += "Content type:" + content_type + "\r\n"
    response += "\r\n"
    response += html
    return response
