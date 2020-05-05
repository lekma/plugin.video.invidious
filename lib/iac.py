# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import uuid
import json

from six import raise_from
from kodi_six import xbmc

from utils import getAddonId, error


def public(func):
    func.__public__ = True
    return func


class JSONRPCError(Exception):

    _err_msg_ = "[{code}] {message}"
    _data_msg_ = "in {method}"
    _stack_msg_ = "(stack: {message} ({name}))"

    def __init__(self, data):
        message = self._err_msg_.format(**data)
        data = data.get("data")
        if data:
            message = " ".join((message, self.data(data)))
        super(JSONRPCError, self).__init__(message)

    def data(self, data):
        message = self._data_msg_.format(**data)
        stack = data.get("stack")
        if stack:
            message = " ".join((message, self.stack(stack)))
        return message

    def stack(self, stack):
        return self._stack_msg_.format(**stack)


class RequestError(RuntimeError):

    _unknown_err_ = "unknown error"

    def __init__(self, data=None):
        message = data["message"] if data else self._unknown_err_
        super(RequestError, self).__init__(message)


def unpack(data):
    data = json.loads(data)
    try:
        return JSONRPCError(data["error"])
    except KeyError:
        try:
            return RequestError(data["exception"])
        except KeyError:
            return data["result"]


# ------------------------------------------------------------------------------
# Monitor
# ------------------------------------------------------------------------------

class Monitor(xbmc.Monitor):

    _request_ = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "JSONRPC.NotifyAll"
    }

    def send(self, sender, message, data):
        params = {
            "message": message,
            "sender": sender,
            "data": data
        }
        return xbmc.executeJSONRPC(
            json.dumps(dict(self._request_, params=params)))


# ------------------------------------------------------------------------------
# Service
# ------------------------------------------------------------------------------

class Service(Monitor):

    _err_msg_ = "[{0.__class__.__name__}: {0}]"

    def __init__(self, sender=None):
        self.sender = sender or getAddonId()
        self._methods_ = {}

    def serve(self):
        for name in dir(self):
            if not name.startswith("_"):
                method = getattr(self, name)
                if callable(method) and getattr(method, "__public__", False):
                    self._methods_[name] = method
        while not self.waitForAbort():
            pass
        self._methods_.clear() # clear circular references

    def execute(self, data):
        try:
            name, args, kwargs = json.loads(data)
            try:
                result = {"result": self._methods_[name](*args, **kwargs)}
            except KeyError:
                raise_from(AttributeError("no method '{0}'".format(name)), None)
        except Exception as err:
            msg = self._err_msg_.format(err)
            error("service: error processing request {}".format(msg))
            result = {"exception": {"message": msg}}
        finally:
            return result

    def onNotification(self, sender, method, data):
        if sender == self.sender:
            message = method.split(".", 1)[1]
            self.send(message, sender, self.execute(data))


# ------------------------------------------------------------------------------
# Client
# ------------------------------------------------------------------------------

class Request(Monitor):

    def __init__(self, sender):
        self.sender = sender
        self.message = uuid.uuid4().hex
        self.result = RequestError()
        self.ready = False

    def execute(self, *data):
        response = unpack(self.send(self.sender, self.message, data))
        if isinstance(response, Exception):
            raise response
        while not self.ready:
            if self.waitForAbort(0.1):
                break
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    def onNotification(self, sender, method, data):
        if sender == self.message:
            message = method.split(".", 1)[1]
            if message == self.sender:
                self.result = unpack(data)
                self.ready = True


class Attribute(object):

    def __init__(self, sender, name):
        self.sender = sender
        self.name = name

    def __getattr__(self, name):
        return Attribute(self.sender, ".".join((self.name, name)))

    def __call__(self, *args, **kwargs):
        return Request(self.sender).execute(self.name, args, kwargs)


class Client(object):

    def __init__(self, sender=None):
        self.sender = sender or getAddonId()

    def __getattr__(self, name):
        return Attribute(self.sender, name)

