# -*- coding: utf-8 -*-


from collections import deque, OrderedDict

from iapc.tools import Persistent, save


# ------------------------------------------------------------------------------
# ChannelFeed

class ChannelFeed(Persistent, OrderedDict):

    @save
    def add(self, key, value):
        self[key] = value

    @save
    def remove(self, *keys):
        for key in keys:
            del self[key]

    @save
    def clear(self):
        super().clear()


channel_feed = ChannelFeed()


# ------------------------------------------------------------------------------
# SearchCache

class SearchCache(Persistent, deque):

    @save
    def clear(self):
        super(SearchCache, self).clear()

    @save
    def push(self, item):
        super(SearchCache, self).append(item)

    @save
    def pop(self):
        return super(SearchCache, self).pop()


search_cache = SearchCache()


# ------------------------------------------------------------------------------
# SearchHistory

class SearchHistory(Persistent, dict):

    def __missing__(self, key):
        self[key] = OrderedDict()
        return self[key]

    @save
    def record(self, type, query, sort_by):
        self[type][query] = {"type": type, "query": query, "sort_by": sort_by}

    @save
    def remove(self, type, query):
        del self[type][query]

    @save
    def clear(self, type=None):
        if type:
            self[type].clear()
        else:
            super(SearchHistory, self).clear()


search_history = SearchHistory()

