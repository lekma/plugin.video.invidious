# -*- coding: utf-8 -*-


__all__ = ["action", "Plugin"]


from functools import wraps

import xbmcplugin

from .addon import maybeLocalize
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
                self.category = maybeLocalize(category)
                self.content = content
                success = func(self, **kwargs)
            except Exception as error:
                success = False
                raise error
            finally:
                if directory:
                    self.endDirectory(success)
                self.content = None
                self.category = None
                self.action = None
        return wrapper
    return decorator


# ------------------------------------------------------------------------------
# Plugin

class Plugin(object):

    def __init__(self, url, handle):
        self.url = url
        self.handle = handle
        self.action = None
        self.category = None
        self.content = None

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
            not xbmcplugin.addDirectoryItem(self.handle, *item.asItem())
        ):
            raise
        return True

    def addItems(self, items, *args):
        if isinstance(items, List):
            items = items.getItems(self.url, *args)
        if (
            not xbmcplugin.addDirectoryItems(
                self.handle, [item.asItem() for item in items if item]
            )
        ):
            raise
        return True

    def addDirectory(self, items, *args):
        if isinstance(items, List):
            if (category := items.category):
                self.category = (
                    f"{self.category} / {maybeLocalize(category)}"
                    if self.category else maybeLocalize(category)
                )
            if (content := items.content):
                self.content = content
        return self.addItems(items, *args)

    def endDirectory(self, success):
        if success:
            if self.content:
                xbmcplugin.setContent(self.handle, self.content)
            if self.category:
                xbmcplugin.setPluginCategory(self.handle, self.category)
        xbmcplugin.endOfDirectory(self.handle, success)

    def playItem(self, item, mimeType=None):
        if mimeType:
            item.setMimeType(mimeType)
            item.setContentLookup(False)
        xbmcplugin.setResolvedUrl(self.handle, True, item)
        return True

