# -*- coding: utf-8 -*-


from sys import argv
from urllib.parse import urlencode

from inputstreamhelper import Helper

from nuttig import action, getSetting, openSettings, parseQuery, Plugin

from invidious.client import IVClient
from invidious.utils import (
    channelsItem, navigationItem, newQueryItem, settingsItem
)


# ------------------------------------------------------------------------------
# IVPlugin

class IVPlugin(Plugin):

    def __init__(self, *args, **kwargs):
        super(IVPlugin, self).__init__(*args, **kwargs)
        self.__client__ = IVClient(self.logger)

    # helpers ------------------------------------------------------------------

    def addChannels(self):
        return self.addItem(channelsItem(self.url, action="channels"))

    def addNewQuery(self):
        return self.addItem(newQueryItem(self.url, action="search", new=True))

    def addSettings(self):
        if getSetting("home.settings", bool):
            return self.addItem(settingsItem(self.url, action="settings"))
        return True

    def addNavigation(self, target, items, **kwargs):
        if (_kwargs_ := getattr(items, target, None)):
            return self.addItem(
                navigationItem(
                    target,
                    self.url,
                    action=self.__action__,
                    **dict(kwargs, **_kwargs_)
                )
            )
        return True

    def addDirectory(self, items, *args, **kwargs):
        if (
            self.addNavigation("previous", items, **kwargs) and
            super(IVPlugin, self).addDirectory(items, *args) and
            self.addNavigation("next", items, **kwargs)
        ):
            return True
        return False

    # play ---------------------------------------------------------------------

    def playItem(
        self,
        item,
        manifestType,
        mimeType=None,
        language=None,
        headers=None,
        params=None
    ):
        #self.logger.info(
        #    f"playItem(item={item}, manifestType={manifestType}, "
        #    f"mimeType={mimeType}, language={language}, "
        #    f"headers={headers}, params={params})"
        #)
        if item:
            if not Helper(manifestType).check_inputstream():
                return False
            item.setProperty("inputstream", "inputstream.adaptive")
            item.setProperty("inputstream.adaptive.manifest_type", manifestType)
            if language:
                item.setProperty(
                    "inputstream.adaptive.original_audio_language", language
                )
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

    @action()
    def play(self, **kwargs):
        #self.logger.info(f"play(kwargs={kwargs})")
        args, kwargs = self.__client__.video(
            sb=getSetting("features.sponsorblock", bool), **kwargs
        )
        return self.playItem(*args, **kwargs)

    # channel ------------------------------------------------------------------

    @action()
    def channel(self, **kwargs):
        if ("continuation" in kwargs):
            self.__updateListing__ = True
        if (
            (
                (not kwargs.get("continuation")) and
                (tabs := self.__client__.tabs(**kwargs)) and
                (not self.addItems(tabs))
            ) or
            ((items := self.__client__.tab("videos", **kwargs)) is None)
        ):
            return False
        return self.addDirectory(items, **kwargs)

    @action(category=31100)
    def playlists(self, **kwargs):
        if ("continuation" in kwargs):
            self.__updateListing__ = True
        if ((items := self.__client__.playlists(**kwargs)) is not None):
            return self.addDirectory(items, **kwargs)
        return False

    @action(category=31200)
    def streams(self, **kwargs):
        if ("continuation" in kwargs):
            self.__updateListing__ = True
        if ((items := self.__client__.tab("streams", **kwargs)) is not None):
            return self.addDirectory(items, **kwargs)
        return False

    @action(category=31300)
    def shorts(self, **kwargs):
        if ("continuation" in kwargs):
            self.__updateListing__ = True
        if ((items := self.__client__.tab("shorts", **kwargs)) is not None):
            return self.addDirectory(items, **kwargs)
        return False

    # playlist -----------------------------------------------------------------

    @action()
    def playlist(self, **kwargs):
        if ("index" in kwargs):
            self.__updateListing__ = True
        kwargs["index"] = int(kwargs.get("index", 50))
        if ((items := self.__client__.playlist(**kwargs)) is not None):
            return self.addDirectory(items, **kwargs)
        return False

    # home ---------------------------------------------------------------------

    @action(category=30000)
    def home(self, **kwargs):
        if self.addDirectory(self.__client__.home()):
            return self.addSettings()
        return False

    # feed ---------------------------------------------------------------------

    @action(category=30100, cacheToDisc=False)
    def feed(self, **kwargs):
        if ("page" in kwargs):
            self.__updateListing__ = True
        page = kwargs["page"] = int(kwargs.get("page", 1))
        if (
            ((page == 1) and (not self.addChannels())) or
            ((items := self.__client__.feed(**kwargs)) is None)
        ):
            return False
        return self.addDirectory(items, **kwargs)


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
        if self.addNewQuery():
            return self.addDirectory(self.__client__.history())
        return False

    def __search__(self, query):
        if ("page" in query):
            self.__updateListing__ = True
        query["page"] = int(query.get("page", 1))
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
