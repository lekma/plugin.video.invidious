# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import sys

from six import wraps
from kodi_six import xbmcplugin
from inputstreamhelper import Helper

from client import client
from objects import Home, Folders, Folder, _trending_styles_, _search_styles_
from utils import parseQuery, getMoreItem, searchDialog, localizedString, log


def action(category=0):
    def decorator(func):
        func.__action__ = True
        @wraps(func)
        def wrapper(self, **kwargs):
            success = False
            try:
                self.category = category
                self.action = func.__name__
                success = func(self, **kwargs)
            except Exception:
                success = False
                raise
            finally:
                self.endDirectory(success)
                del self.action, self.category
        return wrapper
    return decorator


# ------------------------------------------------------------------------------
# Dispatcher
# ------------------------------------------------------------------------------

class Dispatcher(object):

    def __init__(self, url, handle):
        self.url = url
        self.handle = handle

    # utils --------------------------------------------------------------------

    def addItem(self, item):
        if item and not xbmcplugin.addDirectoryItem(self.handle, *item.asItem()):
            raise
        return True

    def addItems(self, items, *args, **kwargs):
        if not xbmcplugin.addDirectoryItems(
            self.handle, [item.asItem()
                          for item in items.items(self.url, *args) if item]):
            raise
        if items.more:
            continuation = getattr(items, "continuation", None)
            if continuation:
                kwargs["continuation"] = continuation
            else:
                kwargs["page"] = int(kwargs.get("page", 1)) + 1
            self.addItem(getMoreItem(self.url, action=self.action, **kwargs))
        if items.content:
            xbmcplugin.setContent(self.handle, items.content)
        if items.category:
            if self.category:
                self.setCategory(" / ".join((items.category,
                                             localizedString(self.category))))
            else:
                self.setCategory(items.category)
        return True

    def setCategory(self, category):
        xbmcplugin.setPluginCategory(self.handle, category)
        self.category = 0

    def endDirectory(self, success):
        if success and self.category:
            self.setCategory(localizedString(self.category))
        xbmcplugin.endOfDirectory(self.handle, success)

    def getSubfolders(self, _type, styles):
        return ({"type": _type, "style": style} for style in styles)

    # actions ------------------------------------------------------------------

    def play(self, item, manifest, mime=None):
        if not Helper(manifest).check_inputstream():
            return False
        item.setProperty("inputstreamaddon", "inputstream.adaptive")
        item.setProperty("inputstream.adaptive.manifest_type", manifest)
        if mime:
            item.setMimeType(mime)
            item.setContentLookup(False)
        xbmcplugin.setResolvedUrl(self.handle, True, item)
        return True

    @action()
    def video(self, **kwargs):
        args = client.video(**kwargs)
        return self.play(*args) if args else False

    @action()
    def channel(self, **kwargs):
        if int(kwargs.get("page", 1)) == 1:
            self.addItem(Folder({"type": "playlists"}).item(self.url, **kwargs))
        return self.addItems(client.channel(**kwargs), "video", **kwargs)

    @action()
    def playlist(self, **kwargs):
        return self.addItems(client.playlist(**kwargs), "video", **kwargs)

    @action()
    def home(self, **kwargs):
        return self.addItems(Home())

    @action(30005)
    def playlists(self, **kwargs):
        return self.addItems(client.playlists(**kwargs), "playlist", **kwargs)

    @action(30007)
    def top(self, **kwargs):
        return self.addItems(client.top(**kwargs), "video")

    @action(30008)
    def popular(self, **kwargs):
        return self.addItems(client.popular(**kwargs), "video")

    @action(30009)
    def trending(self, **kwargs):
        if not "type" in kwargs:
            self.addItems(
                Folders(self.getSubfolders("trending", _trending_styles_)))
        return self.addItems(client.trending(**kwargs), "video")

    # search -------------------------------------------------------------------

    @action(30002)
    def search(self, **kwargs):
        if not "type" in kwargs:
            client.queries.clear()
            return self.addItems(
                Folders(self.getSubfolders("search", _search_styles_)))
        q = kwargs.pop("q", "")
        if not q:
            try:
                q, kwargs = client.queries.pop()
            except IndexError:
                q = searchDialog()
                if q:
                    client.queries.append((q, kwargs))
        if q:
            return self.addItems(
                client.search(q, **kwargs), kwargs["type"], q=q, **kwargs)
        return False

    # dispatch -----------------------------------------------------------------

    def dispatch(self, **kwargs):
        action = getattr(self, kwargs.pop("action", "home"))
        if not callable(action) or not getattr(action, "__action__", False):
            raise Exception("Invalid action '{}'".format(action.__name__))
        return action(**kwargs)


# __main__ ---------------------------------------------------------------------

def dispatch(url, handle, query, *args):
    Dispatcher(url, int(handle)).dispatch(**parseQuery(query))


if __name__ == "__main__":

    dispatch(*sys.argv)

