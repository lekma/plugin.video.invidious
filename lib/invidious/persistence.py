# -*- coding: utf-8 -*-


from os.path import join
from collections import OrderedDict, defaultdict, deque

from urllib.parse import unquote_plus, quote_plus

from tools import (
    getAddonId, getAddonProfile, dumpObject, loadObject,
    selectDialog, inputDialog, notify, localizedString,
    containerRefresh, containerUpdate
)

from . import __query_types__, __sort_by__
from .objects import Queries


# feed -------------------------------------------------------------------------

__feed_path__ = join(getAddonProfile(), "feed.pickle")

def _dumpFeed(feed):
    return dumpObject(feed, __feed_path__)

def _loadFeed():
    return loadObject(__feed_path__, default=OrderedDict())


def addChannelToFeed(authorId, author):
    feed = _loadFeed()
    feed[authorId] = unquote_plus(author)
    _dumpFeed(feed)

def removeChannelsFromFeed():
    feed = _loadFeed()
    indices = selectDialog(list(feed.values()), heading=30014, multi=True)
    if indices:
        keys = list(feed.keys())
        for index in indices:
            del feed[keys[index]]
        _dumpFeed(feed)

def getFeed():
    return list(_loadFeed().keys())


# search history ---------------------------------------------------------------

__search_url__ = "plugin://{}/?action=search".format(getAddonId())

__search_history_path__ = join(getAddonProfile(), "search_history.pickle")

def _dumpSearchHistory(search_history):
    return dumpObject(search_history, __search_history_path__)

def _loadSearchHistory():
    return loadObject(__search_history_path__, default=defaultdict(OrderedDict))

def _recordSearchQuery(type, query, sort_by):
    search_history = _loadSearchHistory()
    search_history[type][quote_plus(query)] = {
        "query": query, "sort_by": sort_by
    }
    _dumpSearchHistory(search_history)


#def updateSearchHistory():
#    search_history = _loadSearchHistory()
#    for type in search_history:
#        for key, value in search_history[type].items():
#            if not isinstance(value, dict):
#                search_history[type][key] = {
#                    "query": value, "sort_by": "relevance"
#                }
#    _dumpSearchHistory(search_history)

def removeSearchQuery(type, key):
    search_history = _loadSearchHistory()
    del search_history[type][key]
    _dumpSearchHistory(search_history)
    containerRefresh()

def clearSearchHistory(type=None, update=False):
    search_history = _loadSearchHistory()
    if type:
        search_history[type].clear()
    else:
        search_history.clear()
    _dumpSearchHistory(search_history)
    if type:
        containerRefresh()
    else:
        notify(30114, time=2000)
        if update:
            containerUpdate(__search_url__, "replace")
        else:
            containerRefresh()

def getSortBy(sort_by="relevance"):
    keys = list(__sort_by__.keys())
    index = selectDialog(
        [localizedString(value) for value in __sort_by__.values()],
        heading=30130, preselect=keys.index(sort_by)
    )
    if index >= 0:
        sort_by = keys[index]
    return sort_by

def newSearch(type, sort_by=None, history=False):
    query = inputDialog(heading=30002)
    if query:
        if sort_by is None:
            sort_by = getSortBy()
        if history:
            _recordSearchQuery(type, query, sort_by)
    return query, sort_by

def searchHistory(type):
    return Queries(
        type, reversed(list(_loadSearchHistory()[type].items())),
        category=__query_types__[type]
    )

def updateSortBy(type, key, sort_by):
    _tmp = getSortBy(sort_by=sort_by)
    if sort_by != _tmp:
        search_history = _loadSearchHistory()
        search_history[type][key]["sort_by"] = _tmp
        _dumpSearchHistory(search_history)
        containerRefresh()


# searches ---------------------------------------------------------------------

# this object exists to survive kodi being extremely bizarre with interpreter
# invocation (that cost me a lot of time in debugging)

def save(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        finally:
            self.__save__()
    return wrapper

class Searches(deque):

    __path__ = join(getAddonProfile(), "searches.pickle")

    @classmethod
    def __load__(cls):
        return loadObject(cls.__path__, default=list())

    def __save__(self):
        dumpObject(list(self), self.__path__)

    def __init__(self):
        super().__init__(self.__load__())

    @save
    def clear(self):
        super().clear()

    @save
    def push(self, *args):
        super().append(*args)

    @save
    def pop(self):
        return super().pop()

