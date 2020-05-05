# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


_folders_schema_ = {
    "videos": {
        "top": {
            "id": 30007,
            "action": "top"
        },
        "popular": {
            "id": 30008,
            "action": "popular"
        },
        "trending": {
            "id": 30009,
            "action": "trending"
        }
    },
    "channels": {
        "live": {
            "id": 30006,
            "action": "playlists",
            "kwargs": {"authorId": "UC4R8DWoMoI7CAwX8_LjQHig"}
        }
    },
    "playlists": {
        "": {
            "id": 30005
        }
    },
    "trending": {
        "music": {
            "id": 30010,
            "kwargs": {"type": "Music"}
        },
        "gaming": {
            "id": 30011,
            "kwargs": {"type": "Gaming"}
        },
        "news": {
            "id": 30012,
            "kwargs": {"type": "News"}
        },
        "movies": {
            "id": 30013,
            "kwargs": {"type": "Movies"}
        }
    },
    "search": {
        "": {
            "id": 30002
        },
        "videos": {
            "id": 30003,
            "kwargs": {"type": "video"}
        },
        "channels": {
            "id": 30004,
            "kwargs": {"type": "channel"}
        },
        "playlists": {
            "id": 30005,
            "kwargs": {"type": "playlist"}
        }

    }
}


_home_folders_ = (
    {"type": "videos", "style": "top"},
    {"type": "videos", "style": "popular"},
    {"type": "videos", "style": "trending"},
    {"type": "channels", "style": "live"},
    {"type": "search"}
)


_trending_styles_ = ("music", "gaming", "news", "movies")


_search_styles_ = ("videos", "channels", "playlists")

