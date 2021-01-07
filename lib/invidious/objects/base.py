# -*- coding: utf-8 -*-





__all__ = ["Thumbnails", "Item", "Items"]


from datetime import datetime

from six import with_metaclass

from tools import maybeLocalize, getAddonId
from tools.objects import Type, Object, List


# ------------------------------------------------------------------------------
# Thumbnails
# ------------------------------------------------------------------------------

class Thumbnails(object):

    def __new__(cls, thumbnails):
        if thumbnails:
            return super(Thumbnails, cls).__new__(cls)
        return None


# ------------------------------------------------------------------------------
# ItemType
# ------------------------------------------------------------------------------

def _date(value):
    if isinstance(value, int):
        return datetime.fromtimestamp(value)
    return value


class ItemType(Type):

    __transform__ = {"__date__": _date}


# ------------------------------------------------------------------------------
# Item
# ------------------------------------------------------------------------------

class Item(with_metaclass(ItemType, Object)):

    __menus__ = []

    @classmethod
    def menus(cls, **kwargs):
        return [
            (
                maybeLocalize(label).format(**kwargs),
                action.format(addonId=getAddonId(), **kwargs)
            )
            for label, action in cls.__menus__
        ]

    @property
    def plot(self):
        return self.__plot__.format(self)


# ------------------------------------------------------------------------------
# Items
# ------------------------------------------------------------------------------

class Items(List):

    __ctor__ = Item

    def __init__(self, items, continuation=None, limit=0, **kwargs):
        super(Items, self).__init__(items, **kwargs)
        self.more = continuation or ((len(self) >= limit) if limit else False)
