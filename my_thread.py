import threading,time

class MyThread(threading.Thread):
	__res = None
	__fun = None
	__args = None

	def __init__(self,func,args):
		super(MyThread,self).__init__()
		self.__fun = func
		self.__args = args


	def run(self):
		self.__res = self.__fun(self.__args)


	def get_result(self):
		return self.__res



# threadsPool = []

# for i in range(10):
# 	thread = MyThread(func,args=(i))
# 	thread.start()
# 	threadsPool.append(thread)

# for thread in threadsPool:
# 	thread.join()

# for thread in threadsPool:
# 	print(thread.get_result())