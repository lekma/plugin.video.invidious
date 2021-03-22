# -*- coding: utf-8 -*-


__all__ = ["Url", "Thumbnails", "Item", "Items"]


from datetime import datetime
from urllib.parse import quote_plus

from iapc.tools import maybeLocalize, getAddonId
from iapc.tools.objects import Type, Object, List


# ------------------------------------------------------------------------------
# Url

def Url(url):
    return f"https:{url}" if url.startswith("//") else url


# ------------------------------------------------------------------------------
# Thumbnails

class Thumbnails(object):

    def __new__(cls, thumbnails):
        if thumbnails:
            return super().__new__(cls)
        return None


# ------------------------------------------------------------------------------
# Item

def __date__(value):
    if isinstance(value, int):
        return datetime.fromtimestamp(value)
    return value


class ItemType(Type):

    __transform__ = {"__date__": __date__}


class Item(Object, metaclass=ItemType):

    __menus__ = []

    @classmethod
    def menus(cls, **kwargs):
        return [
            (
                maybeLocalize(label).format(**kwargs),
                action.format(
                    addonId=getAddonId(),
                    **{key: quote_plus(value) for key, value in kwargs.items()}
                )
            )
            for label, action in cls.__menus__
        ]

    @property
    def plot(self):
        return self.__plot__.format(self)


# ------------------------------------------------------------------------------
# Items

class Items(List):

    __ctor__ = Item

    def __init__(self, items, continuation=None, limit=0, **kwargs):
        super().__init__(items, **kwargs)
        self.more = continuation or ((len(self) >= limit) if limit else False)

