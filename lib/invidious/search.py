# -*- coding: utf-8 -*-


from collections import deque, OrderedDict

from iapc import public
from nuttig import (
    containerRefresh, getSetting, inputDialog, localizedString,
    notify, selectDialog, ICONINFO
)

from invidious.persistence import IVSearchHistory
from invidious.utils import confirm


#-------------------------------------------------------------------------------

queryType = OrderedDict(
    (
        (None, 42230),
        ("all", 42211),
        ("video", 42212),
        ("channel", 42213),
        ("playlist", 42214),
        ("movie", 42215),
        ("show", 42216)
    )
)

querySort = OrderedDict(
    (
        (None, 42230),
        ("relevance", 42221),
        ("date", 42222),
        ("views", 42223),
        ("rating", 42224)
    )
)


#-------------------------------------------------------------------------------
# IVSearch

class IVSearch(object):

    def __init__(self, logger, instance):
        self.logger = logger.getLogger(f"{logger.component}.search")
        self.__instance__ = instance
        self.__queries__ = IVSearchHistory()
        self.__cache__ = deque()

    def __q_setup__(self, setting, ordered, label):
        q_setting = list(ordered.keys())[getSetting(*setting)]
        self.logger.info(
            f"{localizedString(label)}: {localizedString(ordered[q_setting])}"
        )
        return q_setting

    def __setup__(self):
        if (
            (not (history := getSetting("search.history", bool))) and
            self.__queries__
        ):
            self.__queries__.clear()
            notify(localizedString(90003), icon=ICONINFO, time=1000)
        self.__history__ = history
        self.logger.info(f"{localizedString(42110)}: {self.__history__}")
        self.__q_type__ = self.__q_setup__(
            ("query.type", int), queryType, 42210
        )
        self.__q_sort__ = self.__q_setup__(
            ("query.sort", int), querySort, 42220
        )

    def __stop__(self):
        self.__instance__ = None
        self.logger.info("stopped")

    # query --------------------------------------------------------------------

    def __q_select__(self, key, ordered, heading):
        keys = [key for key in ordered.keys() if key]
        index = selectDialog(
            [localizedString(ordered[key]) for key in keys],
            heading=heading,
            preselect=keys.index(key)
        )
        return key if index < 0 else keys[index]

    def q_type(self, type="all"):
        return self.__q_select__(type, queryType, 42210)

    def q_sort(self, sort="relevance"):
        return self.__q_select__(sort, querySort, 42220)

    @public
    def query(self, **query):# this is a trick!
        # that method doesn't take keyword arguments
        try:
            query = self.__cache__.pop()
        except IndexError:
            if (q := inputDialog(heading=137)):
                query = {
                    "q": q,
                    "type": self.__q_type__ or self.q_type(),
                    "sort": self.__q_sort__ or self.q_sort(),
                    "page": 1
                }
                if self.__history__:
                    self.__queries__.record(query)
        return query

    # history ------------------------------------------------------------------

    @public
    def history(self):
        self.__cache__.clear()
        return list(reversed(self.__queries__.values()))

    # search -------------------------------------------------------------------

    @public
    def search(self, query):
        self.__cache__.append(query)
        if self.__history__:
            self.__queries__.move_to_end(query["q"])
        return self.__instance__.search(query)

    # --------------------------------------------------------------------------

    @public
    def updateQueryType(self, q):
        _query_ = self.__queries__[q]
        _type_ = _query_["type"]
        if ((type := self.q_type(type=_type_)) != _type_):
            _query_["type"] = type
            self.__queries__.record(_query_)
            containerRefresh()

    @public
    def updateQuerySort(self, q):
        _query_ = self.__queries__[q]
        _sort_ = _query_["sort"]
        if ((sort := self.q_sort(sort=_sort_)) != _sort_):
            _query_["sort"] = sort
            self.__queries__.record(_query_)
            containerRefresh()

    @public
    def removeQuery(self, q):
        self.__queries__.remove(q)
        containerRefresh()

    @public
    def clearHistory(self):
        if confirm():
            self.__queries__.clear()
            containerRefresh()
