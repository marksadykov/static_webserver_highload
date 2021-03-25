import socket
from io import BytesIO

MAX_PACKET = 32768

mimeTypes = {
    'html': 'text/html',
    'js': 'application/javascript',
    'css': 'text/css',
    'ico': 'image/x-icon',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'svg': 'image/svg+xml',
    'json': 'application/json',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
    'swf': 'application/x-shockwave-flash',
}

def recv_all(sock):
    return sock.recv(MAX_PACKET).decode("utf-8")

def normalize_line_endings(s):
    return ''.join((line + '\n') for line in s.splitlines())

def run():
    server_sock = socket.socket()
    server_sock.bind(('0.0.0.0', 13000))
    server_sock.listen(1)

    while True:
        client_sock, client_addr = server_sock.accept()

        request = normalize_line_endings(recv_all(client_sock))
        request_head, request_body = request.split('\n\n', 1)

        request_head = request_head.splitlines()
        request_headline = request_head[0]
        request_headers = dict(x.split(': ', 1) for x in request_head[1:])

        request_method, request_uri, request_proto = request_headline.split(' ', 3)

        print('request_uri', request_uri)

        content_type = ''
        checkFileOrDir = request_uri.find('.')
        if checkFileOrDir == -1:
            content_type = 'html'
            request_uri += 'index.html'
        else:
            _, content_type = request_uri.split('.', 2)

        content_length = 0
        response_body_raw = ''
        if content_type == 'html' or content_type == 'css' or content_type == 'js':
            f = open(request_uri[1:], "r")
            response_body_raw = ''.join(f.read())
            content_length = len(response_body_raw)
        else:
            f = open(request_uri[1:], "rb")
            response_body_raw = f.read()

        response_headers = {
            'Connection': 'close',
        }

        response_headers['Content-Type'] = mimeTypes[content_type]
        response_headers['Content-Length'] = content_length

        response_headers_raw = ''.join('%s: %s\n' % (k, v) for k, v in response_headers.items())

        response_proto = 'HTTP/1.1'
        response_status = '200'
        response_status_text = 'OK'

        client_sock.send(('%s %s %s' % (response_proto, response_status, response_status_text)).encode())
        client_sock.send('\n'.encode())
        client_sock.send(response_headers_raw.encode())
        client_sock.send('\n'.encode())

        if content_type == 'html' or content_type == 'css' or content_type == 'js':
            client_sock.send(response_body_raw.encode())
        else:
            client_sock.send(response_body_raw)

        client_sock.close()

run()