# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


__all__ = ["Type", "Object", "List"]


from six import iteritems, with_metaclass, raise_from


# ------------------------------------------------------------------------------
# Type
# ------------------------------------------------------------------------------

def _property(name, func):
    def getter(obj):
        return func(obj.__getattr__(name))
    return property(getter)


class Type(type):

    __attr_error__ = "'{}' object has no attribute '{{}}'"
    __transform__ = {}

    def __new__(cls, name, bases, namespace, **kwargs):
        namespace.setdefault("__slots__", set())
        namespace.setdefault("__attr_error__", cls.__attr_error__.format(name))
        for _name_, _func_ in iteritems(namespace.pop("__transform__", dict())):
            namespace[_name_] = _property(_name_, _func_)
        for _type_, _func_ in iteritems(cls.__transform__):
            for _name_ in namespace.pop(_type_, set()):
                namespace[_name_] = _property(_name_, _func_)
        return type.__new__(cls, name, bases, namespace, **kwargs)


# ------------------------------------------------------------------------------
# Object
# ------------------------------------------------------------------------------

class Object(with_metaclass(Type, object)):

    def __new__(cls, data):
        if isinstance(data, dict):
            if not data:
                return None
            return super(Object, cls).__new__(cls)
        return data

    __slots__ = {"__data__"}

    def __init__(self, data):
        self.__data__ = data

    def __getitem__(self, name):
        return self.__data__[name]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise_from(AttributeError(self.__attr_error__.format(name)), None)

    def get(self, *args):
        return self.__data__.get(*args)

    def getItem(self, *args):
        raise NotImplementedError


# ------------------------------------------------------------------------------
# List
# ------------------------------------------------------------------------------

class List(list):

    __ctor__ = Object

    def __init__(self, items, category=None, content="videos"):
        super(List, self).__init__(self.__ctor__(item) for item in items)
        self.category = category
        self.content = content

    def getItems(self, *args):
        return (item.getItem(*args) for item in self)

