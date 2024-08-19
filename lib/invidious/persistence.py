# -*- coding: utf-8 -*-


from collections import OrderedDict

from nuttig import save, Persistent


# ------------------------------------------------------------------------------
# IVSearchHistory

class IVSearchHistory(Persistent, OrderedDict):

    @save
    def record(self, query):
        self[(q := query["q"])] = query
        super(IVSearchHistory, self).move_to_end(q)

    @save
    def remove(self, q):
        del self[q]

    @save
    def clear(self):
        super(IVSearchHistory, self).clear()

    @save
    def move_to_end(self, q):
        super(IVSearchHistory, self).move_to_end(q)


# ------------------------------------------------------------------------------
# IVFeedChannels

class IVFeedChannels(Persistent, OrderedDict):

    @save
    def add(self, key, value):
        self[key] = value

    @save
    def remove(self, key):
        del self[key]

    @save
    def clear(self):
        super(IVFeedChannels, self).clear()
