#!/usr/bin/env python
"""
This module provides utilities for wrapping objects in an ansyncronous queueing
system so that all calls to class members return imeediately and the work is
done asynchronously in another thread.
"""
__author__ = "Daniel Casner <www.danielcasner.org>"
version__ = 0.01

import threading, time

class Executor(threading.Thread):
    """A thread which actually executes asynchronously queued method calls on a
    wrapped object."""

    def __init__(self):
        self.queue = []
        self.willBeMore = True
        threading.Thread.__init__(self)

    def queueWork(self, newWork):
        self.queue.append(newWork)

    def run(self):
        while self.willBeMore:
            while len(self.queue):
                self.queue.pop(0).run()
            time.sleep(1)

    def finish(self):
        self.willBeMore = False
        self.join()

class Work(object):
    "Class representation of work to be done by an Executor."
    __slots__ = ['callable', 'args', 'kwargs', 'callback', 'param']

    def __init__(self, ftn, args, kwargs, callback, param):
        "Stores all the information nessisary for AsyncWrap work"
        assert(callable(ftn)) # Error sooner rather than later
        self.callable = ftn
        self.args = args
        self.kwargs = kwargs
        self.callback = callback
        self.param = param

    def run(self):
        retval = self.ftn(*args, **kwargs)
        if callable(self.callback): self.callback(retval, param)

class AsyncWrap(object):
    """A class which wraps another class so all methods are executed
    asynchronously."""
    __slots__ = ['obj', 'exe']

    def __init__(self, obj):
        "Wraps the given object"
        self.obj = obj
        self.exe = Executor()

    def __getattr__(self, name):
        try:
            member = getattr(self.obj, name)
        except:
            raise AttributeError, '%s has no attribute %s' % (type(self.obj), name)
        else:
            if callable(member):
                return self.queueWork(member)
            else:
                return member

    def __setattr__(self, name, value):
        setattr(self.obj, name, value)

    def queueWork(self, ftn):
        def metaFtn(*args, **kwargs):
            callback = None
            param = None
            if kwargs.has_key['callback']:
                callback = kwargs['callback']
                del kwargs['callback']
            if kwargs.has_key['param']:
                param = kwargs['param']
                del kwargs['param']
            self.exe.queueWork(Work(ftn, args, kwargs, callback, param))
        return metaFtn
        
