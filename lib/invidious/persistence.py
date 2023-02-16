# -*- coding: utf-8 -*-


from collections import OrderedDict

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
    def update(self, others):
        super(ChannelFeed, self).update(others)

    @save
    def clear(self):
        super(ChannelFeed, self).clear()


channel_feed = ChannelFeed()


# ------------------------------------------------------------------------------
# SearchCache

class SearchCache(Persistent, list):

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


# ------------------------------------------------------------------------------

# this should take care of migrating
# from the old pickle format to the new json format
# (I really, REALLY, hope...)

import os
import pathlib
import pickle
import shutil

from iapc.tools import getAddonProfile, Logger

logger = Logger()
for root, dirs, filenames in os.walk(getAddonProfile()):
    for filename in filenames:
        if (path := pathlib.Path(root, filename)).suffix == ".pickle":
            logger.info(f"migrating path: {path}")
            try:
                if (
                    not (backup := path.with_name(f"{path.name}.bak")).exists()
                ):
                    logger.info(f"backup: {backup}")
                    shutil.copyfile(path, backup)
                with open(path, "rb") as f:
                    pickle.load(f).__save__()
            except Exception as err:
                logger.error(f"failed to migrate pickle file: {err}")
            else:
                path.unlink()

