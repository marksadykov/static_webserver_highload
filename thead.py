from time import time
from threading import Thread
# from multiprocessing import Process

def count(n):
    while n > 0:
        n -= 1


startTime = time()
count(1000000000)
count(1000000000)
print('\nSequential execution time : %3.2f s.'%(time() - startTime))

startTime = time()
t1 = Thread(target=count, args=(1000000000,))
t2 = Thread(target=count, args=(1000000000,))
t1.start()
t2.start()
t1.join()
t2.join()
print('\nThreaded execution time : %3.2f s.'%(time() - startTime))

# startTime = time()
# p1 = Process(target=count, args=(100000000,))
# p2 = Process(target=count, args=(100000000,))
# p1.start(); p2.start()
# p1.join(); p2.join()
# print('\nMultiprocessed execution time : %3.2f s.'%(time() - startTime))

# import time
# from threading import Thread
#
# COUNT = 50000000
#
# def countdown(n):
#     while n > 0:
#         n -= 1
#
# t1 = Thread(target=countdown, args=(COUNT//2,))
# t2 = Thread(target=countdown, args=(COUNT//2,))
#
# start = time.time()
# t1.start()
# t2.start()
# t1.join()
# t2.join()
# end = time.time()
#
# print('Затраченное время -', end - start)