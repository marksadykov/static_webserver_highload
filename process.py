from config import Config


class Process:
    def isDoc(self, content_type):
        if content_type == 'html' or content_type == 'css' or content_type == 'js' or content_type == 'txt':
            return True
        else:
            return False

    def isDir(self, request_uri):

        content_type = ''

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
            _, content_type = request_uri.split('.', 2)

        return content_type, request_uri

    def readFile(self, content_type, request_uri,):
        response_status = Config.consts['OK']
        response_body_raw = ''
        content_length = 0
        response_status_text = Config.consts['version']

        if self.isDoc(content_type):

            f = ''
            try:
                f = open(request_uri[1:], "r")
                response_body_raw = ''.join(f.read())
                content_length = len(response_body_raw)
            except FileNotFoundError or NotADirectoryError:
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