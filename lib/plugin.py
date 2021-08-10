# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import sys

from inputstreamhelper import Helper

from tools import Plugin, action, parseQuery, openSettings, getSetting

from invidious import home, styles, sortBy
from invidious.client import client
from invidious.objects.folders import Folders
from invidious.persistence import getFeed, newSearch, searchHistory, Searches
from invidious.utils import newSearchItem, moreItem, settingsItem, playlistsItem


# ------------------------------------------------------------------------------
# InvidiousPlugin
# ------------------------------------------------------------------------------

class InvidiousPlugin(Plugin):

    def __init__(self, *args):
        super(InvidiousPlugin, self).__init__(*args)
        self.__searches__ = Searches()

    # dispatch -----------------------------------------------------------------

    def dispatch(self, **kwargs):
        super(InvidiousPlugin, self).dispatch(**kwargs)
        client.pushQuery(kwargs)

    # helpers ------------------------------------------------------------------

    def getSubfolders(self, type, **kwargs):
        return Folders(
            {"type": type, "style": style, "kwargs": kwargs}
            for style in styles[type]
        )

    def addMore(self, more, **kwargs):
        if more is True:
            kwargs["page"] = int(kwargs.get("page", 1)) + 1
        else:
            kwargs["continuation"] = more
        return self.addItem(
            moreItem(self.url, action=self.action, **kwargs)
        )

    def addNewSearch(self, **kwargs):
        return self.addItem(
            newSearchItem(self.url, action="search", new=True, **kwargs)
        )

    def addPlaylists(self, **kwargs):
        if int(kwargs.get("page", 1)) == 1:
            return self.addItem(
                playlistsItem(self.url, action="playlists", **kwargs)
            )
        return True

    def addSettings(self):
        if getSetting("settings", bool):
            return self.addItem(
                settingsItem(self.url, action="settings")
            )
        return True

    def addDirectory(self, items, *args, **kwargs):
        if super(InvidiousPlugin, self).addDirectory(items, *args):
            more = getattr(items, "more", None)
            if more:
                return self.addMore(more, **kwargs)
            return True
        return False

    def playItem(self, item, manifestType, mimeType=None):
        if not Helper(manifestType).check_inputstream():
            return False
        item.setProperty("inputstreamaddon", "inputstream.adaptive")
        item.setProperty("inputstream.adaptive.manifest_type", manifestType)
        return super(InvidiousPlugin, self).playItem(item, mimeType=mimeType)

    # video --------------------------------------------------------------------

    @action()
    def video(self, **kwargs):
        args = client.video(proxy=getSetting("proxy", bool), **kwargs)
        return self.playItem(*args) if args else False

    # channel ------------------------------------------------------------------

    @action()
    def channel(self, **kwargs):
        if self.addPlaylists(**kwargs):
            return self.addDirectory(client.channel(**kwargs), "video", **kwargs)
        return False

    # playlist -----------------------------------------------------------------

    @action()
    def playlist(self, **kwargs):
        return self.addDirectory(client.playlist(**kwargs), "video", **kwargs)

    # home ---------------------------------------------------------------------

    @action()
    def home(self, **kwargs):
        if self.addDirectory(Folders(home)):
            return self.addSettings()
        return False

    # feed ---------------------------------------------------------------------

    @action(category=30014)
    def feed(self, **kwargs):
        return self.addDirectory(
            client.feed(getFeed(), **kwargs), "video", **kwargs
        )

    # top ----------------------------------------------------------------------

    @action(category=30007)
    def top(self, **kwargs):
        return self.addDirectory(client.top(**kwargs), "video")

    # popular ------------------------------------------------------------------

    @action(category=30008)
    def popular(self, **kwargs):
        return self.addDirectory(client.popular(**kwargs), "video")

    # trending -----------------------------------------------------------------

    @action(category=30009)
    def trending(self, **kwargs):
        if not "type" in kwargs:
            if not self.addItems(self.getSubfolders("trending")):
                return False
        return self.addDirectory(client.trending(**kwargs), "video")

    # playlists ----------------------------------------------------------------

    @action(category=30005)
    def playlists(self, **kwargs):
        return self.addDirectory(
            client.playlists(**kwargs), "playlist", **kwargs
        )

    # autogenerated ------------------------------------------------------------

    @action()
    def autogenerated(self, **kwargs):
        return self.addDirectory(
            client.autogenerated(**kwargs), "playlist", **kwargs
        )

    # search -------------------------------------------------------------------

    def _history(self, **kwargs):
        self.__searches__.clear()
        if self.addNewSearch(**kwargs):
            return self.addDirectory(searchHistory(kwargs["type"]))
        return False

    def _search(self, query, **kwargs):
        self.__searches__.push((query, kwargs))
        return self.addDirectory(
            client.search(query, **kwargs), kwargs["type"],
            query=query, **kwargs
        )

    def _new_search(self, history=False, **kwargs):
        try:
            query, kwargs = self.__searches__.pop()
        except IndexError:
            index = getSetting("sort_by", int)
            try:
                sort_by = sortBy[index]
            except IndexError:
                sort_by = None
            query, kwargs["sort_by"] = newSearch(
                kwargs["type"], sort_by=sort_by, history=history
            )
        if query:
            return self._search(query, **kwargs)
        return False

    @action(category=30002)
    def search(self, **kwargs):
        history = getSetting("search_history", bool)
        if "type" in kwargs:
            query = kwargs.pop("query", "")
            new = kwargs.pop("new", False)
            if query:
                return self._search(query, **kwargs)
            if new:
                return self._new_search(history=history, **kwargs)
            return self._history(**kwargs)
        self.__searches__.clear()
        return self.addDirectory(
            self.getSubfolders("search", new=(not history))
        )

    # settings -----------------------------------------------------------------

    @action(directory=False)
    def settings(self, **kwargs):
        openSettings()
        return True


# __main__ ---------------------------------------------------------------------

def dispatch(url, handle, query, *args):
    InvidiousPlugin(url, int(handle)).dispatch(**parseQuery(query))


if __name__ == "__main__":
    dispatch(*sys.argv)

