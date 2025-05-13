# -*- coding: utf-8 -*-


from collections import OrderedDict

from nuttig import save, Persistent


# ------------------------------------------------------------------------------
# IVNavigationHistory

class IVNavigationHistory(Persistent, dict):

    def __missing__(self, action):
        self[action] = list()
        return self[action]

    def __push__(self, action, key, value):
        if ((item := {key: value}) in self[action]):
            self[action] = self[action][:self[action].index(item)]
        try:
            return self[action][-1]
        except IndexError:
            return None
        finally:
            self[action].append(item)

    @save
    def index(self, action, index):
        if (index == 50):
            self[action].clear()
        return self.__push__(action, "index", index)

    @save
    def page(self, action, page):
        if (page == 1):
            self[action].clear()
        return self.__push__(action, "page", page)

    @save
    def continuation(self, action, continuation):
        if (not continuation):
            self[action].clear()
        return self.__push__(action, "continuation", continuation)

    @save
    def clear(self):
        super(IVNavigationHistory, self).clear()


# ------------------------------------------------------------------------------
# IVSearchHistory

class IVSearchHistory(Persistent, OrderedDict):

    def __init__(self, *args, **kwargs):
        old = migrate("searchhistory.json")
        super(IVSearchHistory, self).__init__(*args, **kwargs)
        if old:
            for k, v in old.items():
                for q in v.values():
                    if ((qsort := q["sort_by"]) == "upload_date"):
                        qsort = "date"
                    elif (qsort == "view_count"):
                        qsort = "views"
                    self.record(
                        {
                            "q": q["query"],
                            "type": q["type"],
                            "sort": qsort
                        }
                    )

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

    def __init__(self, *args, **kwargs):
        old = migrate("channelfeed.json")
        super(IVFeedChannels, self).__init__(*args, **kwargs)
        if old:
            for k, v in old.items():
                self.add(k, v)

    @save
    def add(self, key, value):
        self[key] = value

    @save
    def remove(self, key):
        del self[key]

    @save
    def clear(self):
        super(IVFeedChannels, self).clear()


# ------------------------------------------------------------------------------

# this should take care of migrating old data
# (I really, REALLY, hope...)

import json
import pathlib
import shutil

from nuttig import getAddonProfile, Logger

def migrate(name):
    old = None
    if (
        ((path := pathlib.Path(getAddonProfile(), name)).exists()) and
        (not (backup := path.with_name(f"{path.name}.bak")).exists())
    ):
        logger = Logger()
        logger.info(f"migrating path: {path}")
        logger.info(f"backup: {backup}")
        try:
            shutil.copyfile(path, backup)
            with open(path, "r") as f:
                old = json.load(f)
        except Exception as err:
            logger.error(f"failed to migrate: {err}")
        else:
            path.unlink()
    return old
