import re

from config import Config


class Process:
    def find_all(self, string, target):
        indexes = [i for i in range(len(string)) if string.startswith(target, i)]
        return max(indexes)

    def isDoc(self, content_type):
        if content_type == 'html' or content_type == 'css' or content_type == 'js' or content_type == 'txt':
            return True
        else:
            return False

    def decodeUnicode(self, request_uri):
        result = re.findall(r'%..', request_uri)
        for item in result:
            change = int(('0x' + item[1:]), 16)
            request_uri = request_uri.replace(item, chr(change))

        return request_uri

    def isDir(self, request_uri):

        content_type = ''

        request_uri = self.decodeUnicode(request_uri)

        if request_uri.find('?') != -1:
            findSymbol = request_uri.find('?')
            request_uri = request_uri[:findSymbol]

        if request_uri[-1:] == '/' and request_uri.find('.') != -1:
            content_type = 'html'
            return content_type, request_uri

        if request_uri[-1:] == '/' and request_uri.find('.') == -1:
            request_uri = request_uri[0:-1]

        checkFileOrDir = request_uri.find('.')
        if checkFileOrDir == -1:
            content_type = 'html'
            request_uri += '/index.html'

        else:
            dotIndex = self.find_all(request_uri, '.') + 1
            # _, content_type = request_uri.split('.', 2)
            content_type = request_uri[dotIndex:]

        return content_type, request_uri

    def readFile(self, content_type, request_uri, request_method):

        if request_method == 'POST':
            return '', Config.consts['Bad_Request'], 0, ''

        response_status = Config.consts['OK']
        response_body_raw = ''
        content_length = 0
        response_status_text = Config.consts['OK_status']

        if self.isDoc(content_type):

            f = ''
            try:
                f = open(request_uri[1:], "r")
                response_body_raw = ''.join(f.read())
                content_length = len(response_body_raw)
            except:
                response_status_text = ''
                if (request_uri[-10:] == 'index.html'):
                    response_status = Config.consts['Forbidden']
                else:
                    response_status = Config.consts['Not_Found']
        else:
            if request_uri == '/favicon.ico':
                request_uri = '/httptest' + request_uri
            try:
                f = open(request_uri[1:], "rb")
                response_body_raw = f.read()
            except FileNotFoundError:
                response_status_text = ''
                response_status = Config.consts['Not_Found']

        return response_body_raw, response_status, content_length, response_status_text