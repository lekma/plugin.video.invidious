# -*- coding: utf-8 -*-


__all__ = ["action", "Plugin"]


from functools import wraps

import xbmcplugin

from .addon import maybeLocalize, Logger
from .objects import List


__invalid_action__ = "Invalid action '{}'"


# action -----------------------------------------------------------------------

def action(action=None, category=None, content=None, directory=True):
    def decorator(func):
        func.__action__ = True
        @wraps(func)
        def wrapper(self, **kwargs):
            success = False
            try:
                self.action = action or func.__name__
                self.__category__ = maybeLocalize(category)
                self.__content__ = content
                success = func(self, **kwargs)
            except Exception as error:
                success = False
                raise error
            finally:
                if directory:
                    self.endDirectory(success)
                self.__content__ = None
                self.__category__ = None
                self.action = None
        return wrapper
    return decorator


# ------------------------------------------------------------------------------
# Plugin

class Plugin(object):

    def __init__(self, url, handle):
        self.logger = Logger(component="plugin")
        self.url = url
        self.__handle__ = handle
        self.action = None
        self.__category__ = None
        self.__content__ = None

    # dispatch -----------------------------------------------------------------

    def dispatch(self, **kwargs):
        try:
            action = getattr(self, (name := kwargs.pop("action", "home")))
        except AttributeError:
            raise AttributeError(__invalid_action__.format(name)) from None
        if not callable(action) or not getattr(action, "__action__", False):
            raise Exception(__invalid_action__.format(name))
        return action(**kwargs)

    # utils --------------------------------------------------------------------

    def addItem(self, item):
        if (
            item and
            not xbmcplugin.addDirectoryItem(self.__handle__, *item.asItem())
        ):
            raise
        return True

    def addItems(self, items, *args):
        if isinstance(items, List):
            items = items.getItems(self.url, *args)
        if (
            not xbmcplugin.addDirectoryItems(
                self.__handle__, [item.asItem() for item in items if item]
            )
        ):
            raise
        return True

    def addDirectory(self, items, *args):
        if isinstance(items, List):
            if (category := items.category):
                self.__category__ = (
                    f"{self.__category__} / {maybeLocalize(category)}"
                    if self.__category__ else maybeLocalize(category)
                )
            if (content := items.content):
                self.__content__ = content
        return self.addItems(items, *args)

    def endDirectory(self, success):
        if success:
            if self.__content__:
                xbmcplugin.setContent(self.__handle__, self.__content__)
            if self.__category__:
                xbmcplugin.setPluginCategory(self.__handle__, self.__category__)
        xbmcplugin.endOfDirectory(self.__handle__, success)

    def playItem(self, item, mimeType=None):
        if mimeType:
            item.setMimeType(mimeType)
            item.setContentLookup(False)
        xbmcplugin.setResolvedUrl(self.__handle__, True, item)
        return True

