from time import time
from threading import Thread
# from multiprocessing import Process

# def count(n):
#     while n > 0:
#         n -= 1
#
#     return n
#
# startTime = time()
# n1 = 100000000
# n2 = 100000000
# print(n1)
# print(n2)
# n1 = count(n1)
# n2 = count(n2)
# print(n1)
# print(n2)
# print('\nSequential execution time : %3.2f s.'%(time() - startTime))
#
# startTime = time()
# t1 = Thread(target=count, args=(100000000,))
# t2 = Thread(target=count, args=(100000000,))
# t1.start()
# t2.start()
# t1.join()
# t2.join()
# print('\nThreaded execution time : %3.2f s.'%(time() - startTime))
#
# startTime = time()
# p1 = Process(target=count, args=(1000000000,))
# p2 = Process(target=count, args=(1000000000,))
# p1.start(); p2.start()
# p1.join(); p2.join()
# print('\nMultiprocessed execution time : %3.2f s.'%(time() - startTime))
#
# # import time
# # from threading import Thread
# #

# import os
#
# # Get the number of CPUs
# # in the system using
# # os.cpu_count() method
# cpuCount = os.cpu_count()
#
# # Print the number of
# # CPUs in the system
# print("Number of CPUs in the system:", cpuCount)