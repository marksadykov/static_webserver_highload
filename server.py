import socket
import logging
import threading
import time

import os, sys

from config import Config
from parse import Parse
from process import ServerProcess

class Server:
    def __init__(self):
        # self.cpuCount = os.cpu_count()
        self.cpuCount = 8
        self.numThread = 0
        self.parseCurrent = Parse()
        self.processCurrent = ServerProcess()

        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def listener(self):
        try:
            self.serverSock.bind((Config.consts['url'], Config.consts['port']))
        except socket.error as err:
            self.serverSock.close()
            print(err)

        self.serverSock.listen(1)
        self.serverSock.setblocking(False)

        print('listen on ' + str(Config.consts['url']) + ':' + str(Config.consts['port']))
        print('===========================')

    def polling(self):
        queue = []
        while True:
            if self.numThread < self.cpuCount and len(queue) > 0:
                current = queue.pop()
                current.start()
            try:
                clientSock, clientAddr = self.serverSock.accept()
                print('Connected to: ' + str(clientAddr[0]) + ':' + str(clientAddr[1]))
                x = threading.Thread(target=self.requestHandler, args=(clientSock, ))
                if self.numThread < self.cpuCount:
                    self.numThread = self.numThread + 1
                    x.start()
                else:
                    queue.append(x)

            except:
                pass


    def requestHandler(self, clientSock):

        request = self.parseCurrent.normalize_line_endings(self.parseCurrent.recv_all(clientSock))

        if request == '' or request == '\n' or request.find('\n\n') == -1:
            return

        request_head, request_body = request.split('\n\n', 1)

        request_head = request_head.splitlines()
        request_headline = request_head[0]

        request_method, request_uri, request_proto = request_headline.split(' ', 3)

        print('request URL:', request_uri)

        content_type, request_uri = self.processCurrent.isDir(request_uri)

        response_headers = {
            'Connection': 'close',
            'Server': 'Mark Sadykov',
        }

        self.writeResponse(clientSock, content_type, request_uri, request_method, response_headers)

        clientSock.close()
        self.numThread = self.numThread - 1

    def writeHeaders(self, clientSock, response_headers, response_body_raw, response_proto, response_status, response_status_text):
        response_headers['Content-length'] = len(response_body_raw)
        response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())
        clientSock.send(('%s %s %s' % (response_proto, response_status, response_status_text)).encode())
        clientSock.send('\r\n'.encode())
        clientSock.send(response_headers_raw.encode())
        clientSock.send('\r\n'.encode())

    def writeResponse(self, clientSock, content_type, request_uri, request_method, response_headers):

        if request_method == 'POST' or request_uri.find('../') != -1 or request_uri == '/favicon.ico':
            response_proto = Config.consts['version']
            response_status = Config.consts['Bad_Request']
            response_headers['Content-length'] = 0
            response_headers['Content-Type'] = ''
            response_status_text = ''
            response_body_raw = ''

            response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())
            clientSock.send(('%s %s %s' % (response_proto, response_status, response_status_text)).encode())
            clientSock.send('\r\n'.encode())
            clientSock.send(response_headers_raw.encode())
            clientSock.send('\r\n'.encode())
            clientSock.send(response_body_raw.encode())
            return

        response_status = Config.consts['OK']
        response_body_raw = ''
        response_status_text = Config.consts['OK_status']

        try:
            response_headers['Content-Type'] = Config.mimeTypes[content_type]
        except:
            content_type = 'txt'
            response_headers['Content-Type'] = ''

        response_proto = Config.consts['version']


        if self.processCurrent.isDoc(content_type):
            try:
                f = open(request_uri[1:], "r", encoding="latin-1")
                response_body_raw = ''.join(f.read())
                f.close()

                self.writeHeaders(clientSock, response_headers, response_body_raw, response_proto, response_status,
                             response_status_text)

                if request_method != 'HEAD':
                    clientSock.send(response_body_raw.encode("latin-1"))

            except:
                response_status_text = ''
                if request_uri[-10:] == 'index.html':
                    response_status = Config.consts['Forbidden']
                else:
                    response_status = Config.consts['Not_Found']

                self.writeHeaders(clientSock, response_headers, response_body_raw, response_proto, response_status,
                                  response_status_text)
        else:
            try:
                f = open(request_uri[1:], "rb")
                response_body_raw = f.read()
                f.close()

                self.writeHeaders(clientSock, response_headers, response_body_raw, response_proto, response_status,
                                  response_status_text)

                if request_method != 'HEAD':
                    clientSock.send(response_body_raw)

            except:
                response_status_text = ''
                response_status = Config.consts['Not_Found']
                self.writeHeaders(clientSock, response_headers, response_body_raw, response_proto, response_status,
                                  response_status_text)
