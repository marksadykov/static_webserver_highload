import socket
import logging
import threading
import time

# from _thread import *

from config import Config
from parse import Parse
from process import ServerProcess

def requestProcess(client_sock, parse_current, process_current):
    # time.sleep(5)

    request = parse_current.normalize_line_endings(parse_current.recv_all(client_sock))

    if request == '' or request == '\n' or request.find('\n\n') == -1:
        return

    request_head, request_body = request.split('\n\n', 1)

    request_head = request_head.splitlines()
    request_headline = request_head[0]
    request_headers = dict(x.split(': ', 1) for x in request_head[1:])

    request_method, request_uri, request_proto = request_headline.split(' ', 3)

    # print('request URL:', request_uri)

    content_type, request_uri = process_current.isDir(request_uri)

    response_body_raw, response_status, content_length, response_status_text = process_current.readFile(content_type,
                                                                                                        request_uri,
                                                                                                        request_method)

    response_headers = {
        'Connection': 'close',
        'Server': 'Mark Sadykov',
    }

    try:
        response_headers['Content-Type'] = Config.mimeTypes[content_type]
    except:
        content_type = 'txt'
        response_headers['Content-Type'] = ''

    response_headers['Content-length'] = content_length

    response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

    response_proto = Config.consts['version']

    client_sock.send(('%s %s %s' % (response_proto, response_status, response_status_text)).encode())
    client_sock.send('\r\n'.encode())
    client_sock.send(response_headers_raw.encode())
    client_sock.send('\r\n'.encode())

    if request_method != 'HEAD':
        if process_current.isDoc(content_type):
            # client_sock.send(response_body_raw.encode('latin-1'))
            client_sock.send(response_body_raw.encode())
        else:
            client_sock.send(response_body_raw)

        # client_sock.send('\r\n'.encode())

    client_sock.close()
    print('end')



def server():
    parse_current = Parse()
    process_current = ServerProcess()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind((Config.consts['url'], Config.consts['port']))
    except socket.error as err:
        server_sock.close()
        print(err)

    server_sock.listen(1)
    server_sock.setblocking(False)

    # print('listen on', Config.consts['url'], ':', Config.consts['port'])
    # print('===========================')

    threadCount = 0

    while True:
        try:
            client_sock, client_addr = server_sock.accept()
            x = threading.Thread(target=requestProcess, args=(client_sock, parse_current, process_current))
            x.start()
            print('start', threadCount)
            threadCount += 1
        except:
            pass

        # print('start', threadCount)
        # threadCount += 1
        # print('Connected to: ' + client_addr [0] + ':' + str(client_addr [1]))

        # start_new_thread(requestProcess, (client_sock, parse_current, process_current, threadCount))

        # requestProcess(client_sock, parse_current, process_current)

        # x = threading.Thread(target=requestProcess, args=(client_sock, parse_current, process_current))
        # x.start()

        # x = Process(target=requestProcess, args=(client_sock, parse_current, process_current))
        # x.start()

if __name__ == "__main__":
    server()