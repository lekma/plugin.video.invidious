# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


__all__ = ["Queries"]


from tools import ListItem, buildUrl

from .base import Item, Items


# ------------------------------------------------------------------------------
# Queries
# ------------------------------------------------------------------------------

class Query(Item):

    __menus__ = [
        (30130, "RunScript({addonId},updateSortBy,{type},{key},{sort_by})"),
        (30035, "RunScript({addonId},removeSearchQuery,{type},{key})"),
        (30036, "RunScript({addonId},clearSearchHistory,{type})")
    ]

    def getItem(self, url):
        return ListItem(
            self.query,
            buildUrl(
                url, action="search", type=self.type, query=self.query,
                sort_by=self.sort_by
            ),
            isFolder=True,
            infos={"video": {"title": self.query, "plot": self.query}},
            contextMenus=self.menus(
                type=self.type, key=self.key, sort_by=self.sort_by
            ),
            poster="DefaultAddonsSearch.png"
        )


class Queries(Items):

    __ctor__ = Query

    def __init__(self, type, items, **kwargs):
        # this is braindead, but, the base class really expect a dict...
        super(Queries, self).__init__(
            (dict({"type": type, "key": key}, **value) for key, value in items),
            **kwargs
        )

