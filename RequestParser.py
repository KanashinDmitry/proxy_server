import email
from io import StringIO


class RequestParser:
    @staticmethod
    def parse_request(request_data):
        meta, headers = request_data.decode("utf-8").split('\r\n', 1)

        # construct a message from the request string
        message = email.message_from_file(StringIO(headers))

        # construct a dictionary containing the headers
        headers = dict(message.items())

        url = headers["Host"]
        if ':' in url:
            host, port = url.split(':')
        else:
            host, port = url, 80

        return {"orig_data": request_data, "meta": meta, "host": host, "port": int(port)}
