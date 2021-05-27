import re
import socket
import threading

from config import Config
from utils.normalizeLineEndings import normalizeLineEndings
from utils.findAllOccurrences import findAllOccurrences


class Server:
    def __init__(self):
        # self.cpuCount = os.cpu_count()
        self.cpuCount = 8
        self.numThread = 0
        self.config = Config()
        self.queue = []
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

        self.serverSock.listen(1)
        self.serverSock.setblocking(False)

        print('listen on ' + str(self.config.consts['url']) + ':' + str(self.config.consts['port']))
        print('=============================')

    def polling(self):
        while True:
            if self.numThread < self.cpuCount and (len(self.queue) > 0):
                currentThread = self.queue[0]
                currentThread.start()

            try:
                clientSock, clientAddr = self.serverSock.accept()
                print('Connected to: ' + str(clientAddr[0]) + ':' + str(clientAddr[1]))
                x = threading.Thread(target=self.requestHandler, args=(clientSock,))
                if self.numThread < self.cpuCount:
                    x.start()
                else:
                    self.queue.append(x)

            except:
                pass

    def requestHandler(self, clientSock):
        self.numThread += 1
        request = normalizeLineEndings(self.decodeReceive(clientSock))
        if request == '' or request == '\n' or request.find('\n\n') == -1:
            self.numThread -= 1
            return

        requestHead, _ = request.split('\n\n', 1)
        requestHead = requestHead.splitlines()
        requestHeadline = requestHead[0]
        requestMethod, requestUri, requestProto = requestHeadline.split(' ', 3)
        print('request URL:', requestUri)
        contentType, requestUri = self.isDir(requestUri)
        responseHeaders = self.config.responseHeaders
        self.writeResponse(clientSock, contentType, requestUri, requestMethod, responseHeaders)

        clientSock.close()
        self.numThread -= 1

    def writeHeaders(self, clientSock, responseHeaders, responseBodyRaw, responseProto, responseStatus,
                     responseStatusText):
        responseHeaders['Content-length'] = len(responseBodyRaw)
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

        if self.isDoc(contentType):
            try:
                f = open(requestUri[1:], "r", encoding="latin-1")
                responseBodyRaw = ''.join(f.read())
                f.close()

                self.writeHeaders(clientSock, responseHeaders, responseBodyRaw, responseProto, responseStatus,
                                  responseStatusText)

                if requestMethod != 'HEAD':
                    clientSock.send(responseBodyRaw.encode("latin-1"))

            except:
                responseStatusText = ''
                if requestUri[-10:] == 'index.html':
                    responseStatus = Config.consts['Forbidden']
                else:
                    responseStatus = Config.consts['Not_Found']

                self.writeHeaders(clientSock, responseHeaders, responseBodyRaw, responseProto, responseStatus,
                                  responseStatusText)
        else:
            try:
                f = open(requestUri[1:], "rb")
                responseBodyRaw = f.read()
                f.close()

                self.writeHeaders(clientSock, responseHeaders, responseBodyRaw, responseProto, responseStatus,
                                  responseStatusText)

                if requestMethod != 'HEAD':
                    clientSock.send(responseBodyRaw)

            except:
                responseStatusText = ''
                responseStatus = Config.consts['Not_Found']
                self.writeHeaders(clientSock, responseHeaders, responseBodyRaw, responseProto, responseStatus,
                                  responseStatusText)

    def server(self):
        self.listener()
        self.polling()
