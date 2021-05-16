import os

path = "../httptest/text..txt"
fd = os.open(path, os.O_RDONLY)
n = 50
readBytes = os.read(fd, n).decode("utf-8")

print(readBytes)

os.close(fd)