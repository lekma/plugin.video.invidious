# -*- coding: utf-8 -*-


from collections import OrderedDict

from nuttig import save, Persistent


# ------------------------------------------------------------------------------
# IVSearchHistory

class IVSearchHistory(Persistent, OrderedDict):

    def __init__(self, *args, **kwargs):
        old = migrate("searchhistory.json")
        super(IVSearchHistory, self).__init__(*args, **kwargs)
        if old:
            for k, v in old.items():
                for q in v.values():
                    self.record(
                        {
                            "q": q["query"],
                            "type": q["type"],
                            "sort": q["sort_by"],
                            "page": 1
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
