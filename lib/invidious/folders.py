# -*- coding: utf-8 -*-


from nuttig import localizedString


# folders ----------------------------------------------------------------------

__folders__ = {
    "folders": {
        "feed": {
            "title": 30100,
            "setting": "home.feed",
            "art": "icons/settings/network.png"
        },
        "popular": {
            "title": 30200,
            "setting": "home.popular",
            "art": "DefaultMusicTop100.png"
        },
        "trending": {
            "title": 30300,
            "setting": "home.trending",
            "art": "DefaultFavourites.png",
            "folders": {
                "music": {
                    "action": "trending",
                    "title": 30310,
                    "art": "DefaultAddonMusic.png",
                    "properties": {"SpecialSort": "top"},
                    "kwargs": {
                        "type": "music",
                        "category": localizedString(30310)
                    }
                },
                "gaming": {
                    "action": "trending",
                    "title": 30320,
                    "art": "DefaultAddonGame.png",
                    "properties": {"SpecialSort": "top"},
                    "kwargs": {
                        "type": "gaming",
                        "category": localizedString(30320)
                    }
                },
                "movies": {
                    "action": "trending",
                    "title": 30330,
                    "art": "DefaultMovies.png",
                    "properties": {"SpecialSort": "top"},
                    "kwargs": {
                        "type": "movies",
                        "category": localizedString(30330)
                    }
                }
            }
        },
        "search": {
            "title": 137,
            "art": "DefaultAddonsSearch.png"
        }
    }
}


class Folder(dict):

    def __init__(self, action, folder):
        return super(Folder, self).__init__(
            title=folder["title"],
            action=folder.get("action", action),
            setting=folder.get("setting"),
            art=dict.fromkeys(("poster", "icon"), folder.get("art")),
            properties=folder.get("properties"),
            kwargs=folder.get("kwargs", {})
        )

def getFolders(*paths):
    folders = __folders__["folders"]
    for path in paths:
        folders = folders.get(path, {}).get("folders", {})
    return [Folder(*item) for item in folders.items()]
