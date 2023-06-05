# -*- coding: utf-8 -*-


from sys import argv
from urllib.parse import urlencode

from inputstreamhelper import Helper

from iapc.tools import Plugin, action, parseQuery, openSettings, getSetting

from invidious import home, styles, sortBy
from invidious.client import client
from invidious.objects import Folders
from invidious.persistence import channel_feed, search_cache, search_history
from invidious.search import newSearch, searchHistory
from invidious.utils import moreItem, newSearchItem, playlistsItem, settingsItem


# ------------------------------------------------------------------------------
# InvidiousPlugin

class InvidiousPlugin(Plugin):

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
            if (more := getattr(items, "more", None)):
                return self.addMore(more, **kwargs)
            return True
        return False

    def playItem(
        self, item, manifestType, mimeType=None, headers=None, params=None
    ):
        if not Helper(manifestType).check_inputstream():
            return False
        item.setProperty("inputstream", "inputstream.adaptive")
        item.setProperty("inputstream.adaptive.manifest_type", manifestType)
        if headers and isinstance(headers, dict):
            item.setProperty(
                "inputstream.adaptive.manifest_headers", urlencode(headers)
            )
        if params and isinstance(params, dict):
            item.setProperty(
                "inputstream.adaptive.manifest_params", urlencode(params)
            )
        return super(InvidiousPlugin, self).playItem(item, mimeType=mimeType)

    # video --------------------------------------------------------------------

    @action()
    def video(self, **kwargs):
        args, kwargs = client.video(proxy=getSetting("proxy", bool), **kwargs)
        return self.playItem(*args, **kwargs) if args else False

    # channel ------------------------------------------------------------------

    @action()
    def channel(self, **kwargs):
        if (not "continuation" in kwargs) and (not self.addPlaylists(**kwargs)):
            return False
        return self.addDirectory(client.channel(**kwargs), "video", **kwargs)

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
            client.feed(list(channel_feed), **kwargs), "video", **kwargs
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

    def __search__(self, query, **kwargs):
        search_cache.push((query, kwargs))
        return self.addDirectory(
            client.search(query, **kwargs), kwargs["type"],
            query=query, **kwargs
        )

    def __new_search__(self, history=False, **kwargs):
        try:
            query, kwargs = search_cache.pop()
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
            return self.__search__(query, **kwargs)
        return False

    def __history__(self, **kwargs):
        search_cache.clear()
        if self.addNewSearch(**kwargs):
            return self.addDirectory(searchHistory(kwargs["type"]))
        return False

    @action(category=30002)
    def search(self, **kwargs):
        history = getSetting("history", bool)
        if "type" in kwargs:
            search_type = kwargs["type"]
            query = kwargs.pop("query", "")
            new = kwargs.pop("new", False)
            if query:
                if history and query in search_history[search_type]:
                    search_history.move_to_end(search_type, query)
                return self.__search__(query, **kwargs)
            if new:
                return self.__new_search__(history=history, **kwargs)
            return self.__history__(**kwargs)
        search_cache.clear()
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
    dispatch(*argv)
