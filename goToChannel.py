# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import sys

from kodi_six import xbmc

from lib.utils import get_addon_id


_cmd_ = "Container.Update(plugin://{}/?action=channel&authorId={})"


if __name__ == "__main__":
    xbmc.executebuiltin(
        _cmd_.format(get_addon_id(), sys.listitem.getProperty("authorId"))
    )

