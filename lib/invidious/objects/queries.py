# -*- coding: utf-8 -*-


__all__ = ["Queries"]


from iapc.tools import ListItem, buildUrl

from .base import Item, Items


# ------------------------------------------------------------------------------
# Queries

class Query(Item):

    __menus__ = [
        (30130, "RunScript({addonId},updateSortBy,{type},{query},{sort_by})"),
        (30035, "RunScript({addonId},removeSearchQuery,{type},{query})"),
        (30036, "RunScript({addonId},clearSearchHistory,{type})")
    ]

    def getItem(self, url):
        return ListItem(
            self.query,
            buildUrl(
                url, action="search",
                type=self.type, query=self.query, sort_by=self.sort_by
            ),
            isFolder=True,
            infoLabels={"video": {"title": self.query, "plot": self.query}},
            contextMenus=self.menus(
                type=self.type,
                query=self.query,
                sort_by=self.sort_by
            ),
            poster="DefaultAddonsSearch.png"
        )


class Queries(Items):

    __ctor__ = Query

