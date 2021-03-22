# -*- coding: utf-8 -*-


from iapc.tools import (
    selectDialog, inputDialog, notify, localizedString,
    containerRefresh, containerUpdate, getAddonId
)

from . import __sortBy__, queryTypes
from .objects import Queries
from .persistence import search_history


def sortBy(sort_by="relevance"):
    keys = list(__sortBy__.keys())
    index = selectDialog(
        [localizedString(value) for value in __sortBy__.values()],
        heading=30130, preselect=keys.index(sort_by)
    )
    if index >= 0:
        sort_by = keys[index]
    return sort_by


def newSearch(type, sort_by=None, history=False):
    if (query := inputDialog(heading=30002)):
        if sort_by is None:
            sort_by = sortBy()
        if history:
            search_history.record(type, query, sort_by)
    return (query, sort_by)


def searchHistory(type):
    return Queries(
        reversed(search_history[type].values()), category=queryTypes[type]
    )


def removeSearchQuery(type, query):
    search_history.remove(type, query)
    containerRefresh()


__search_url__ = f"plugin://{getAddonId()}/?action=search"

def clearSearchHistory(type=None, update=False):
    search_history.clear(type=type)
    if type:
        containerRefresh()
    else:
        notify(30114, time=2000)
        if update:
            containerUpdate(__search_url__, "replace")
        else:
            containerRefresh()


def updateSortBy(type, query, _sort_by_):
    if ((sort_by := sortBy(sort_by=_sort_by_)) != _sort_by_):
        search_history.record(type, query, sort_by)
        containerRefresh()

