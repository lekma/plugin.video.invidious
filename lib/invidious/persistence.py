# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


from os.path import join
from collections import OrderedDict, defaultdict, deque

from six import iterkeys, itervalues, iteritems
from six.moves.urllib.parse import unquote_plus, quote_plus

from tools import (
    getAddonId, getAddonProfile, dumpObject, loadObject,
    selectDialog, inputDialog, notify
)

from . import __query_types__
from .objects.queries import Queries
from .utils import containerRefresh, containerUpdate


# feed -------------------------------------------------------------------------

__feed_path__ = join(getAddonProfile(), "feed.pickle")

def _dumpFeed(feed):
    return dumpObject(feed, __feed_path__)

def _loadFeed():
    return loadObject(__feed_path__, default=OrderedDict())


def addChannelToFeed(authorId, author):
    feed = _loadFeed()
    feed[authorId] = unquote_plus(author).decode("utf-8")
    _dumpFeed(feed)

def removeChannelsFromFeed():
    feed = _loadFeed()
    indices = selectDialog(list(itervalues(feed)), heading=30014, multi=True)
    if indices:
        keys = list(iterkeys(feed))
        for index in indices:
            del feed[keys[index]]
        _dumpFeed(feed)

def getFeed():
    return list(iterkeys(_loadFeed()))


# search history ---------------------------------------------------------------

__search_url__ = "plugin://{}/?action=search".format(getAddonId())

__search_history_path__ = join(getAddonProfile(), "search_history.pickle")

def _dumpSearchHistory(search_history):
    return dumpObject(search_history, __search_history_path__)

def _loadSearchHistory():
    return loadObject(__search_history_path__, default=defaultdict(OrderedDict))

def _recordSearchQuery(type, query):
    search_history = _loadSearchHistory()
    search_history[type][quote_plus(query.encode("utf-8"))] = query
    _dumpSearchHistory(search_history)


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

def newSearch(type, history=False):
    query = inputDialog(heading=30002)
    if query and history:
        _recordSearchQuery(type, query)
    return query

def searchHistory(type):
    return Queries(
        type, reversed(list(iteritems(_loadSearchHistory()[type]))),
        category=__query_types__[type]
    )


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
        super(Searches, self).__init__(self.__load__())

    @save
    def clear(self):
        super(Searches, self).clear()

    @save
    def push(self, *args):
        super(Searches, self).append(*args)

    @save
    def pop(self):
        return super(Searches, self).pop()

