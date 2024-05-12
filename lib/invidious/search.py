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


def newSearch(search_type, sort_by=None, history=False):
    if (query := inputDialog(heading=30002)):
        if sort_by is None:
            sort_by = sortBy()
        if history:
            search_history.record(search_type, query, sort_by)
    return (query, sort_by)


def searchHistory(search_type):
    return Queries(
        reversed(search_history[search_type].values()), category=queryTypes[search_type]
    )


def removeSearchQuery(search_type, query):
    search_history.remove(search_type, query)
    containerRefresh()


__search_url__ = f"plugin://{getAddonId()}/?action=search"

def clearSearchHistory(search_type=None, update=False):
    search_history.clear(search_type=search_type)
    if search_type:
        containerRefresh()
    else:
        notify(30114, time=2000)
        if update:
            containerUpdate(__search_url__, "replace")
        else:
            containerRefresh()


def updateSortBy(search_type, query, _sort_by_):
    if ((sort_by := sortBy(sort_by=_sort_by_)) != _sort_by_):
        search_history.record(search_type, query, sort_by)
        containerRefresh()
