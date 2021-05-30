class Config:
    consts = {
        'max_packet': 1024,
        'url': '0.0.0.0',
        'port': 3004,

        'OK': '200',
        'Forbidden': '403',
        'Not_Found': '404',
        'Bad_Request': '400',

        'OK_status': 'OK',

        'version': 'HTTP/1.1',
    }

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
        'txt': 'text/plain',
    }

    docTypes = ['html', 'css', 'js', 'txt']

    indexPath = 'html'
    indexFile = '/index.html'

    thread_count = 64
    cpu_limit = 4

    responseHeaders = {
        'Connection': 'close',
        'Server': 'Mark Sadykov',
    }
