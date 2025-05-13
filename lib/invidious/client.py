# -*- coding: utf-8 -*-


from functools import wraps

from iapc import Client

from nuttig import addonIsEnabled

from invidious.items import (
    FeedChannels, Folders, Playlists, Queries, Results, Video, Videos
)
from invidious.persistence import IVNavigationHistory


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
        self.logger = logger.getLogger(component="client")
        self.__client__ = Client()
        self.__history__ = IVNavigationHistory()

    # video --------------------------------------------------------------------

    @instance
    def video(self, sb=False, **kwargs):
        #self.logger.info(f"video(sb={sb}, kwargs={kwargs})")
        if (video := self.__client__.instance.video(**kwargs)):
            item = Video(video).makeItem(video["url"])
            if (item and sb and addonIsEnabled("service.sponsorblock")):
                item.setProperty("SB:videoID", video["videoId"])
            return (
                (item, video["manifestType"]),
                {"mimeType": video["mimeType"], "language": video["language"]}
            )
        return ((None, None), {})

    # channel ------------------------------------------------------------------

    @instance
    def tabs(self, **kwargs):
        if (tabs := self.__client__.instance.tabs(**kwargs)):
            return Folders(tabs, **kwargs)

    @instance
    def tab(self, key, **kwargs):
        items, next, category = self.__client__.instance.tab(key, **kwargs)
        if items is not None:
            previous = self.__history__.continuation(
                key, kwargs.get("continuation")
            )
            return Videos(
                items, next=next, category=category, previous=previous
            )

    @instance
    def playlists(self, **kwargs):
        items, next, category = self.__client__.instance.playlists(**kwargs)
        if items is not None:
            previous = self.__history__.continuation(
                "playlists", kwargs.get("continuation")
            )
            return Playlists(
                items, next=next, category=category, previous=previous
            )

    # playlist -----------------------------------------------------------------

    @instance
    def playlist(self, **kwargs):
        items, next, category = self.__client__.instance.playlist(**kwargs)
        if items is not None:
            previous = self.__history__.index("playlist", kwargs["index"])
            return Videos(
                items, next=next, category=category, previous=previous
            )

    # home ---------------------------------------------------------------------

    def home(self):
        return Folders(self.__client__.folders())

    # feed ---------------------------------------------------------------------

    @instance
    def feed(self, limit=29, **kwargs):
        items, next = self.__client__.feed.feed(limit, **kwargs)
        previous = self.__history__.page("feed", kwargs["page"])
        return Videos(items, next=next, previous=previous)

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
        items, next = self.__client__.search.search(query)
        previous = self.__history__.page("search", query["page"])
        return Results(
            items, next=next, previous=previous, category=query["q"]
        )
