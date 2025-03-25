# -*- coding: utf-8 -*-


from iapc import Client
from nuttig import addonIsEnabled, localizedString, okDialog

from invidious.extract import YtDlpVideo


# ------------------------------------------------------------------------------
# YtDlp

class YtDlp(object):

    def __init__(self, logger):
        self.logger = logger.getLogger(component="yt-dlp")

    def __setup__(self):
        pass

    def __stop__(self):
        self.logger.info("stopped")

    # play ---------------------------------------------------------------------

    __service_id__ = "service.yt-dlp"

    def video(self, videoId, **kwargs):
        if addonIsEnabled(self.__service_id__):
            return YtDlpVideo(
                Client(self.__service_id__).video(
                    f"https://www.youtube.com/watch?v={videoId}"
                )
            )
        okDialog(localizedString(90004).format(self.__service_id__))
