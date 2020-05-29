# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import pickle

from collections import OrderedDict
from os.path import join, exists

from six import itervalues, iterkeys

from utils import getAddonProfile, selectDialog


# utils ------------------------------------------------------------------------

_feed_path_ = join(getAddonProfile(), "feed.pickle")


def _dumpFeed(feed):
    with open(_feed_path_, "w+") as f:
        pickle.dump(feed, f, -1)


def _loadFeed():
    if exists(_feed_path_):
        with open(_feed_path_, "r") as f:
            return pickle.load(f)
    return OrderedDict()


# exposed ----------------------------------------------------------------------

def addChannelToFeed(authorId, *args):
    feed = _loadFeed()
    feed[authorId] = ", ".join((a.decode("utf-8") for a in args))
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

