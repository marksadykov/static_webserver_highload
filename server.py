import socket

MAX_PACKET = 32768

def recv_all(sock):
    request = sock.recv(MAX_PACKET).decode("utf-8").split('\n')
    return request[:-2], request[len(request) - 1]

def run():
    r'''Main loop'''

    # Create TCP socket listening on 10000 port for all connections,
    # with connection queue of length 1
    server_sock = socket.socket()
    server_sock.bind(('0.0.0.0', 13006))
    server_sock.listen(1)

    while True:
        # accept connection
        client_sock, client_addr = server_sock.accept()

        # headers and body are divided with \n\n (or \r\n\r\n - that's why we
        # normalize endings). In real application usage, you should handle
        # all variations of line endings not to screw request body

        request_headers, request_body = recv_all(client_sock)

        print('request_headers', request_headers)
        print('request_body', request_body)
        # first line is request headline, and others are headers
        request_headline = request_headers[0]

        print('request_headline', request_headline)
        # headers have their name up to first ': '. In real world uses, they
        # could duplicate, and dict drops duplicates by default, so
        # be aware of this.

        # headline has form of "POST /can/i/haz/requests HTTP/1.0"
        request_method, request_uri, request_proto = request_headline.split(' ', 3)

        response_body = [
            '<html><body><h1>Hello, world!</h1>',
            '<p>This page is in location %(request_uri)r, was requested ' % locals(),
            'using %(request_method)r, and with %(request_proto)r.</p>' % locals(),
            '<p>Request body is %(request_body)r</p>' % locals(),
            '<p>Actual set of headers received:</p>',
            '<ul>',
        ]

        request_headers = request_headers[1:]
        for request_header in request_headers:
            print('request_header', request_header)
            request_header_name, request_header_value = request_header.split(': ', 2)
            response_body.append('<li><b>%r</b> == %r</li>' % (request_header_name, request_header_value))

        response_body.append('</ul></body></html>')

        response_body_raw = ''.join(response_body)

        # Clearly state that connection will be closed after this response,
        # and specify length of response body
        response_headers = {
            'Content-Type': 'text/html; encoding=utf8',
            'Content-Length': len(response_body_raw),
            'Connection': 'close',
        }

        response_headers_raw = ''.join('%s: %s\n' % (k, v) for k, v in response_headers)

        # Reply as HTTP/1.1 server, saying "HTTP OK" (code 200).
        response_proto = 'HTTP/1.1'
        response_status = '200'
        response_status_text = 'OK' # this can be random

        # sending all this stuff
        client_sock.send('%s %s %s' % (response_proto, response_status, \
                                                        response_status_text))
        client_sock.send(response_headers_raw)
        client_sock.send('\n') # to separate headers from body
        client_sock.send(response_body_raw)

        # and closing connection, as we stated before
        client_sock.close()

run()