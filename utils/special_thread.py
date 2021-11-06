#!/usr/bin/python3

from inspect import isclass

from ctypes import (
	c_long, py_object, pythonapi
)

from threading import (
	Thread, ThreadError, _active
)

def _async_raise(tid, exctype):
	if not isclass(exctype):
		raise TypeError("Only types can be raised (not instances)")

	res = pythonapi.PyThreadState_SetAsyncExc(
		c_long(tid), py_object(exctype)
	)

	if res == 0:
		raise ValueError("invalid thread id")

	elif res != 1:
		pythonapi.PyThreadState_SetAsyncExc(tid, 0)

		raise SystemError("PyThreadState_SetAsyncExc failed")

class magicThread(Thread):
	def _get_my_tid(self):
		if not self.is_alive():
			raise ThreadError("the thread is not active")

		if hasattr(self, "_thread_id"):
			return self._thread_id

		for tid, tobj in _active.items():
			if tobj is self:
				self._thread_id = tid
				return tid

		raise AssertionError("could not determine the thread's id")

	def raise_exc(self, exctype):
		_async_raise(
			self._get_my_tid(), exctype
		)

	def kill(self):
		self.raise_exc(SystemExit)