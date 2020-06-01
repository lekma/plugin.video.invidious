# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import pickle

from collections import OrderedDict
from os.path import join, exists

from six import iterkeys, itervalues
from six.moves.urllib.parse import unquote_plus

from utils import getAddonProfile, selectDialog


# utils ------------------------------------------------------------------------

def _dumpObject(obj, path):
    with open(path, "w+") as f:
        pickle.dump(obj, f, -1)

def _loadObject(path, default=None):
    if exists(path):
        with open(path, "r") as f:
            return pickle.load(f)
    return default


# feed -------------------------------------------------------------------------

_feed_path_ = join(getAddonProfile(), "feed.pickle")

def _dumpFeed(feed):
    return _dumpObject(feed, _feed_path_)

def _loadFeed():
    return _loadObject(_feed_path_, default=OrderedDict())


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

