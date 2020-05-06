# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import uuid
import json

from six import raise_from
from kodi_six import xbmc

from utils import getAddonId, logError


def public(func):
    func.__public__ = True
    return func


# ------------------------------------------------------------------------------
# Monitor
# ------------------------------------------------------------------------------

class JSONRPCError(Exception):

    _error_msg_ = "[{code}] {message}"
    _data_msg_ = "in {method}"
    _stack_msg_ = "(stack: {message} ({name}))"

    def __init__(self, error):
        message = self._error_msg_.format(**error)
        data = error.get("data")
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
        error = json.loads(
            xbmc.executeJSONRPC(
                json.dumps(dict(self._request_, params=params)))).get("error")
        if error:
            raise JSONRPCError(error)


# ------------------------------------------------------------------------------
# Service
# ------------------------------------------------------------------------------

class Service(Monitor):

    _error_msg_ = "[{0.__class__.__name__}: {0}]"

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

    def execute(self, request):
        try:
            name, args, kwargs = json.loads(request)
            try:
                method = self._methods_[name]
            except KeyError:
                raise_from(AttributeError("no method '{0}'".format(name)), None)
            else:
                response = {"result": method(*args, **kwargs)}
        except Exception as error:
            message = self._error_msg_.format(error)
            logError("service: error processing request {}".format(message))
            response = {"error": {"message": message}}
        finally:
            return response

    def onNotification(self, sender, method, request):
        if sender == self.sender:
            message = method.split(".", 1)[1]
            self.send(message, sender, self.execute(request))


# ------------------------------------------------------------------------------
# Client
# ------------------------------------------------------------------------------

class RequestError(Exception):

    _unknown_msg_ = "unknown error"

    def __init__(self, error=None):
        message = error["message"] if error else self._unknown_msg_
        super(RequestError, self).__init__(message)


def unpack(response):
    response = json.loads(response)
    try:
        return response["result"]
    except KeyError:
        return RequestError(response["error"])


class Request(Monitor):

    def __init__(self, sender):
        self.sender = sender
        self.message = uuid.uuid4().hex
        self.response = RequestError()
        self.ready = False

    def execute(self, request):
        self.send(self.sender, self.message, request)
        while not self.ready:
            if self.waitForAbort(0.1):
                break
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

    def onNotification(self, sender, method, response):
        if sender == self.message:
            message = method.split(".", 1)[1]
            if message == self.sender:
                self.response = unpack(response)
                self.ready = True


class Attribute(object):

    def __init__(self, sender, name):
        self.sender = sender
        self.name = name

    def __getattr__(self, name):
        return Attribute(self.sender, ".".join((self.name, name)))

    def __call__(self, *args, **kwargs):
        return Request(self.sender).execute((self.name, args, kwargs))


class Client(object):

    def __init__(self, sender=None):
        self.sender = sender or getAddonId()

    def __getattr__(self, name):
        return Attribute(self.sender, name)

