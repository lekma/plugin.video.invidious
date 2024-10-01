# -*- coding: utf-8 -*-


from functools import wraps

from iapc import Client

from nuttig import addonIsEnabled

from invidious.items import (
    FeedChannels, Folders, Playlists, Queries, Results, Video, Videos
)


# instance ---------------------------------------------------------------------

def instance(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if (
            self.__client__.instance.instance() or
            (
                self.__client__.instance.selectInstance() and
                self.__client__.instance.instance()
            )
        ):
            return func(self, *args, **kwargs)
    return wrapper


# ------------------------------------------------------------------------------
# IVClient

class IVClient(object):

    def __init__(self, logger):
        self.logger = logger.getLogger(f"{logger.component}.client")
        self.__client__ = Client()

    # video --------------------------------------------------------------------

    @instance
    def video(self, sb=False, **kwargs):
        if (video := self.__client__.instance.video(**kwargs)):
            item = Video(video).makeItem(video["url"])
            if (item and sb and addonIsEnabled("service.sponsorblock")):
                item.setProperty("SB:videoID", video["videoId"])
            return (item, video["manifestType"])
        return (None, None)

    # channel ------------------------------------------------------------------

    @instance
    def tabs(self, **kwargs):
        if (tabs := self.__client__.instance.tabs(**kwargs)):
            return Folders(tabs, **kwargs)

    @instance
    def tab(self, key, **kwargs):
        if (videos := self.__client__.instance.tab(key, **kwargs)):
            return Videos(
                videos["items"],
                continuation=videos["continuation"],
                category=videos["channel"]
            )

    @instance
    def playlists(self, **kwargs):
        if (playlists := self.__client__.instance.playlists(**kwargs)):
            return Playlists(
                playlists["items"],
                continuation=playlists["continuation"],
                category=playlists["channel"]
            )

    # playlist -----------------------------------------------------------------

    @instance
    def playlist(self, **kwargs):
        if(playlist := self.__client__.instance.playlist(**kwargs)):
            return Videos(
                playlist["items"], limit=200, category=playlist["title"]
            )

    # home ---------------------------------------------------------------------

    def home(self):
        return Folders(self.__client__.folders())

    # feed ---------------------------------------------------------------------

    @instance
    def feed(self, limit=29, **kwargs):
        return Videos(self.__client__.feed.feed(limit, **kwargs), limit=limit)

    @instance
    def channels(self):
        return FeedChannels(self.__client__.feed.channels())

    # popular ------------------------------------------------------------------

    @instance
    def popular(self, **kwargs):
        if (videos := self.__client__.instance.popular(**kwargs)):
            return Videos(videos, **kwargs)

    # trending -----------------------------------------------------------------

    @instance
    def trending(self, folders=False, **kwargs):
        if folders:
            return Folders(self.__client__.folders("trending"))
        if (videos := self.__client__.instance.trending(**kwargs)):
            return Videos(videos, **kwargs)

    # search -------------------------------------------------------------------

    def query(self):
        return self.__client__.search.query()

    def history(self):
        return Queries(self.__client__.search.history())

    @instance
    def search(self, query):
        return Results(
            self.__client__.search.search(query), limit=20, category=query["q"]
        )
