# -*- coding: utf-8 -*-





__all__ = ["Folder", "Folders"]


from tools import ListItem, buildUrl, maybeLocalize, getSetting

from .base import Item, Items

from .. import __schema__


# ------------------------------------------------------------------------------
# Folders
# ------------------------------------------------------------------------------

class Folder(Item):

    @property
    def enabled(self):
        return (
            getSetting(self.type, bool) if self.get("optional", False) else True
        )

    @property
    def style(self):
        return self.get("style", "")

    @property
    def kwargs(self):
        return self.get("kwargs", {})

    def getItem(self, url, **kwargs):
        if self.enabled:
            folder = __schema__[self.type][self.style]
            label = maybeLocalize(folder["label"])
            kwargs = dict(dict(folder.get("kwargs", {}), **self.kwargs), **kwargs)
            return ListItem(
                label,
                buildUrl(url, action=folder.get("action", self.type), **kwargs),
                isFolder=True,
                infos={
                    "video": {
                        "title": label,
                        "plot": maybeLocalize(folder.get("plot", label))
                    }
                },
                **folder.get("art", {})
            )


class Folders(Items):

    __ctor__ = Folder

