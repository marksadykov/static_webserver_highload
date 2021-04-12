import re

from config import Config


class ServerProcess:
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
            content_type = request_uri[dotIndex:]

        return content_type, request_uri