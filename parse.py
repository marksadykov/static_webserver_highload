from config import Config


class Parse:
    def __init__(self):
        self.config = Config()

    def recv_all(self, sock):
        print('recv_all', sock)
        buf = sock.recv(self.config.consts['max_packet']).decode("utf-8")
        print('buf', buf)
        return buf

    def normalize_line_endings(self, s):
        return ''.join((line + '\n') for line in s.splitlines())