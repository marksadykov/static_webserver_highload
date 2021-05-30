import re
import socket
import threading
import os
from multiprocessing import Process

from config import Config
from utils.normalizeLineEndings import normalizeLineEndings
from utils.findAllOccurrences import findAllOccurrences


class Server:
    def __init__(self):
        self.config = Config()
        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def decodeReceive(self, socket):
        return socket.recv(self.config.consts['max_packet']).decode("utf-8")

    def isDoc(self, contentType):
        if contentType in self.config.docTypes:
            return True

        return False

    def decodeUnicode(self, request_uri):
        result = re.findall(r'%..', request_uri)
        for item in result:
            change = int(('0x' + item[1:]), 16)
            request_uri = request_uri.replace(item, chr(change))

        return request_uri

    def normalizePath(self, requestUri):
        if requestUri.find('?') != -1:
            findSymbol = requestUri.find('?')
            return requestUri[:findSymbol]

        return requestUri

    def isDir(self, requestUri):
        requestUri = self.decodeUnicode(requestUri)
        requestUri = self.normalizePath(requestUri)

        if requestUri[-1:] == '/' and requestUri.find('.') != -1:
            contentType = self.config.indexPath
            return contentType, requestUri

        if requestUri[-1:] == '/' and requestUri.find('.') == -1:
            requestUri = requestUri[0:-1]

        checkFileOrDir = requestUri.find('.')
        if checkFileOrDir == -1:
            contentType = self.config.indexPath
            requestUri += self.config.indexFile

        else:
            dotIndex = findAllOccurrences(requestUri, '.') + 1
            contentType = requestUri[dotIndex:]

        return contentType, requestUri

    def listener(self):
        try:
            self.serverSock.bind((self.config.consts['url'], self.config.consts['port']))
        except socket.error as err:
            self.serverSock.close()
            print(err)

        self.serverSock.listen(8)

        print('listen on ' + str(self.config.consts['url']) + ':' + str(self.config.consts['port']))
        print('=============================')

    def start(self, serverSock, config, initThreads, runWorker, requestHandler):
        process_pool = []

        for index in range(config.cpu_limit):
            process = Process(target=initThreads, args=(serverSock, config, runWorker, requestHandler))
            process.start()
            process_pool.append(process)

        try:
            for process in process_pool:
                process.join()

        except KeyboardInterrupt:
            for process in process_pool:
                process.terminate()

    def initThreads(self, serverSock, config, runWorker, requestHandler):
        thread_pool = []

        for index in range(config.thread_count):
            thread = threading.Thread(target=runWorker, args=(serverSock, config, requestHandler))
            thread.start()

        for thread in thread_pool:
            thread.join()

    def runWorker(self, serverSock, config, requestHandler):
        while True:
            conn, addr = serverSock.accept()
            try:
                requestHandler(conn, config)
            except Exception as e:
                print('exception socket', e)
            finally:
                conn.close()

    def requestHandler(self, clientSock, config):
        request = normalizeLineEndings(self.decodeReceive(clientSock))
        if request == '' or request == '\n' or request.find('\n\n') == -1:
            return

        requestHead, _ = request.split('\n\n', 1)
        requestHead = requestHead.splitlines()
        requestHeadline = requestHead[0]
        requestMethod, requestUri, requestProto = requestHeadline.split(' ', 3)
        print('request URL:', requestUri)
        contentType, requestUri = self.isDir(requestUri)
        responseHeaders = config.responseHeaders
        self.writeResponse(clientSock, contentType, requestUri, requestMethod, responseHeaders)

    def writeHeaders(self, clientSock, responseHeaders, responseBodyRaw, responseProto, responseStatus,
                     responseStatusText):
        responseHeaders['Content-length'] = responseBodyRaw
        responseHeadersRaw = ''.join('%s: %s\r\n' % (k, v) for k, v in responseHeaders.items())
        clientSock.send(('%s %s %s' % (responseProto, responseStatus, responseStatusText)).encode())
        clientSock.send('\r\n'.encode())
        clientSock.send(responseHeadersRaw.encode())
        clientSock.send('\r\n'.encode())

    def writeResponse(self, clientSock, contentType, requestUri, requestMethod, responseHeaders):

        if requestMethod == 'POST' or requestUri.find('../') != -1 or requestUri == '/favicon.ico':
            responseProto = Config.consts['version']
            responseStatus = Config.consts['Bad_Request']
            responseHeaders['Content-length'] = 0
            responseHeaders['Content-Type'] = ''
            responseStatusText = ''
            responseBodyRaw = ''

            responseHeadersRaw = ''.join('%s: %s\r\n' % (k, v) for k, v in responseHeaders.items())
            clientSock.send(('%s %s %s' % (responseProto, responseStatus, responseStatusText)).encode())
            clientSock.send('\r\n'.encode())
            clientSock.send(responseHeadersRaw.encode())
            clientSock.send('\r\n'.encode())
            clientSock.send(responseBodyRaw.encode())
            return

        responseStatus = Config.consts['OK']
        responseBodyRaw = ''
        responseStatusText = Config.consts['OK_status']

        try:
            responseHeaders['Content-Type'] = Config.mimeTypes[contentType]
        except:
            contentType = 'txt'
            responseHeaders['Content-Type'] = ''

        responseProto = Config.consts['version']

        try:
            self.writeHeaders(clientSock, responseHeaders, os.path.getsize(requestUri[1:]), responseProto,
                              responseStatus,
                              responseStatusText)

            if requestMethod == 'HEAD':
                return

            with open(requestUri[1:], 'rb') as file:
                clientSock.sendfile(file)



        except:
            responseStatusText = ''
            if requestUri[-10:] == 'index.html':
                responseStatus = Config.consts['Forbidden']
            else:
                responseStatus = Config.consts['Not_Found']

            self.writeHeaders(clientSock, responseHeaders, responseBodyRaw, responseProto, responseStatus,
                              responseStatusText)

    def server(self):
        self.listener()
        self.start(self.serverSock, self.config, self.initThreads, self.runWorker, self.requestHandler)
