# -*- coding: utf-8 -*-


from sys import argv
from time import time
from urllib.parse import urlencode

from inputstreamhelper import Helper

from nuttig import action, getSetting, openSettings, parseQuery, Plugin

from invidious.client import IVClient
from invidious.utils import channelsItem, moreItem, newQueryItem, settingsItem


# ------------------------------------------------------------------------------
# IVPlugin

class IVPlugin(Plugin):

    def __init__(self, *args, **kwargs):
        super(IVPlugin, self).__init__(*args, **kwargs)
        self.__client__ = IVClient(self.logger)

    # helpers ------------------------------------------------------------------

    def addMore(self, more, count=0, **kwargs):
        if more is True:
            if (index := kwargs.get("index")):
                if count:
                    kwargs["index"] = int(index) + count
                else:
                    del kwargs["index"]
            else:
                kwargs["page"] = int(kwargs.get("page", 1)) + 1
        else:
            kwargs["continuation"] = more
        return self.addItem(
            moreItem(self.url, action=self.action, **kwargs)
        )

    def addDirectory(self, items, *args, **kwargs):
        if super(IVPlugin, self).addDirectory(items, *args):
            if (more := getattr(items, "more", None)):
                return self.addMore(more, count=len(items), **kwargs)
            return True
        return False

    def addSettingsItem(self):
        if getSetting("home.settings", bool):
            return self.addItem(settingsItem(self.url, action="settings"))
        return True

    def addNewQueryItem(self):
        return self.addItem(newQueryItem(self.url, action="search", new=True))

    def addChannelsItem(self):
        return self.addItem(channelsItem(self.url, action="channels"))

    def playItem(
        self, item, manifestType, mimeType=None, headers=None, params=None
    ):
        #self.logger.info(
        #    f"playItem(item={item}, manifestType={manifestType}, "
        #    f"mimeType={mimeType}, headers={headers}, params={params})"
        #)
        if item:
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
            return super(IVPlugin, self).playItem(item, mimeType=mimeType)
        return False

    # play ---------------------------------------------------------------------

    @action()
    def play(self, **kwargs):
        return self.playItem(*self.__client__.video(**kwargs))

    # channel ------------------------------------------------------------------

    @action()
    def channel(self, **kwargs):
        if (
            (
                (not ("continuation" in kwargs)) and
                (tabs := self.__client__.tabs(**kwargs)) and
                (not self.addItems(tabs))
            ) or
            ((items := self.__client__.tab("videos", **kwargs)) is None)
        ):
            return False
        return self.addDirectory(items, **kwargs)

    @action(category=31100)
    def playlists(self, **kwargs):
        if ((items := self.__client__.playlists(**kwargs)) is not None):
            return self.addDirectory(items, **kwargs)
        return False

    @action(category=31200)
    def streams(self, **kwargs):
        if ((items := self.__client__.tab("streams", **kwargs)) is not None):
            return self.addDirectory(items, **kwargs)
        return False

    @action(category=31300)
    def shorts(self, **kwargs):
        if ((items := self.__client__.tab("shorts", **kwargs)) is not None):
            return self.addDirectory(items, **kwargs)
        return False

    # playlist -----------------------------------------------------------------

    @action()
    def playlist(self, index=50, **kwargs):
        if ((items := self.__client__.playlist(index=index, **kwargs)) is not None):
            return self.addDirectory(items, index=index, **kwargs)
        return False

    # home ---------------------------------------------------------------------

    @action(category=30000)
    def home(self, **kwargs):
        if self.addDirectory(self.__client__.home()):
            return self.addSettingsItem()
        return False

    # feed ---------------------------------------------------------------------

    @action(category=30100, cacheToDisc=False)
    def feed(self, **kwargs):
        t = time()
        try:
            if (
                (
                    (int(kwargs.get("page", 1)) == 1) and
                    (not self.addChannelsItem())
                ) or
                ((items := self.__client__.feed(**kwargs)) is None)
            ):
                return False
            return self.addDirectory(items, **kwargs)
        finally:
            self.logger.info(f"feed() took: {time() - t} seconds")


    @action(category=30111)
    def channels(self, **kwargs):
        return self.addDirectory(self.__client__.channels(), **kwargs)

    # popular ------------------------------------------------------------------

    @action(category=30200)
    def popular(self, **kwargs):
        if ((items := self.__client__.popular(**kwargs)) is not None):
            return self.addDirectory(items, **kwargs)
        return False

    # trending -----------------------------------------------------------------

    @action(category=30300)
    def trending(self, **kwargs):
        if (
            (
                (not "type" in kwargs) and
                (not self.addItems(self.__client__.trending(folders=True)))
            ) or
            ((items := self.__client__.trending(**kwargs)) is None)
        ):
            return False
        return self.addDirectory(items, **kwargs)

    # search -------------------------------------------------------------------

    def __query__(self):
        return self.__client__.query()

    def __history__(self):
        if self.addNewQueryItem():
            return self.addDirectory(self.__client__.history())
        return False

    def __search__(self, query):
        if ((results := self.__client__.search(query)) is not None):
            return self.addDirectory(results, **query)
        return False

    @action(category=137)
    def search(self, **kwargs):
        if kwargs:
            if (query := (self.__query__() if "new" in kwargs else kwargs)):
                return self.__search__(query)
            return False
        return self.__history__()

    # settings -----------------------------------------------------------------

    @action(directory=False)
    def settings(self, **kwargs):
        openSettings()
        return True


# __main__ ---------------------------------------------------------------------

def dispatch(url, handle, query, *args):
    IVPlugin(url, int(handle)).dispatch(**parseQuery(query))


if __name__ == "__main__":
    dispatch(*argv)
