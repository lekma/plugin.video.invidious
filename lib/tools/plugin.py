# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


__all__ = ["action", "Plugin"]


from six import wraps, raise_from
from kodi_six import xbmcplugin

from .kodi import maybeLocalize
from .objects import List


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
            except Exception:
                success = False
                raise
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
# ------------------------------------------------------------------------------

class Plugin(object):

    def __init__(self, url, handle):
        self.url = url
        self.handle = handle
        self.action = None
        self.category = None
        self.content = None

    # dispatch -----------------------------------------------------------------

    __invalid_action__ = "Invalid action '{}'"

    def dispatch(self, **kwargs):
        name = kwargs.pop("action", "home")
        try:
            action = getattr(self, name)
        except AttributeError:
            raise_from(AttributeError(self.__invalid_action__.format(name)), None)
        if not callable(action) or not getattr(action, "__action__", False):
            raise Exception(self.__invalid_action__.format(name))
        return action(**kwargs)

    # utils --------------------------------------------------------------------

    def addItem(self, item):
        if item and not xbmcplugin.addDirectoryItem(self.handle, *item.asItem()):
            raise
        return True

    def addItems(self, items, *args):
        if isinstance(items, List):
            items = items.getItems(self.url, *args)
        if not xbmcplugin.addDirectoryItems(
            self.handle, [item.asItem() for item in items if item]
        ):
            raise
        return True

    def addDirectory(self, items, *args):
        if isinstance(items, List):
            category = items.category
            if category:
                self.category = (
                    "{} / {}".format(self.category, maybeLocalize(category))
                    if self.category else maybeLocalize(category)
                )
            content = items.content
            if content:
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

