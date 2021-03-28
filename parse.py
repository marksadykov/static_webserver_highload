from config import Config


class Parse:
    def recv_all(self, sock):
        return sock.recv(Config.consts['max_packet']).decode("utf-8")

    def normalize_line_endings(self, s):
        return ''.join((line + '\n') for line in s.splitlines())