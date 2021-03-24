import socket

sock = socket.socket()
sock.bind(('', 9092))
sock.listen(5)

while True:
    conn, addr = sock.accept()
    print('connected:', addr)
    data = conn.recv(1024)

    if len(data) > 0:
        request = data.decode("utf-8").split('\n')
        headers = request[:-2]
        mainInformation = headers[0].split(' ')
        method = mainInformation[0]
        path = mainInformation[1]
        print('method:', method, ' path:', path)

    if not data:
        break

    response_body = [
        '<html><body><h1>Hello, world!</h1>',
        '<p>This page is in location %(request_uri)r, was requested ' % locals(),
        'using %(request_method)r, and with %(request_proto)r.</p>' % locals(),
        '<p>Request body is %(request_body)r</p>' % locals(),
        '<p>Actual set of headers received:</p>',
        '<p>hahhahahaha</p',
        '</body></html>',
    ]
    response_body_raw = ''.join(response_body)

    response_headers = {
        'Content-Type': 'text/html; encoding=utf8',
        'Content-Length': len(response_body_raw),
        'Connection': 'close',
    }

    conn.send(resp.encode())
    conn.close()

