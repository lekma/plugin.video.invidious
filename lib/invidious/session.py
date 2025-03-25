# -*- coding: utf-8 -*-


from concurrent.futures import ThreadPoolExecutor

from requests import HTTPError, RequestException, Session, Timeout

from nuttig import buildUrl, getSetting, localizedString


# ------------------------------------------------------------------------------
# IVSession

class IVSession(Session):

    def __init__(self, logger, headers=None):
        super(IVSession, self).__init__()
        self.logger = logger.getLogger(component="session")
        if headers:
            self.headers.update(headers)
        self.__pool__ = ThreadPoolExecutor()

    def __setup__(self):
        if (timeout := getSetting("session.timeout", float)) > 0.0:
            self.__timeout__ = (((timeout - (timeout % 3)) + 0.05), timeout)
        else:
            self.__timeout__ = None
        self.logger.info(f"{localizedString(41140)}: {self.__timeout__}")

    def __stop__(self):
        self.__pool__.shutdown(cancel_futures=True)
        self.close()
        self.logger.info("stopped")

    # --------------------------------------------------------------------------

    def request(self, method, url, notify=True, **kwargs):
        self.logger.info(
            f"request: {method} {buildUrl(url, **kwargs.get('params', {}))}"
        )
        try:
            return super(IVSession, self).request(
                method, url, timeout=self.__timeout__, **kwargs
            )
        except RequestException as error:
            self.logger.error(error, notify=notify)
            if (not isinstance(error, Timeout)):
                raise error

    # --------------------------------------------------------------------------

    # this is wonky because invidious sometimes includes legitimate results with
    # errors

    def __error__(self, result, notify=True):
        if (isinstance(result, dict) and (error := result.pop("error", None))):
            self.logger.error(error, notify=notify)
            return (True, result or None)
        return (False, result)

    def __get__(self, url, notify=True, **kwargs):
        if ((response := self.get(url, notify=notify, params=kwargs)) is not None):
            notified, result = self.__error__(response.json(), notify=notify)
            try:
                response.raise_for_status()
            except HTTPError as error:
                self.logger.error(error, notify=((not notified) and notify))
            return result

    def __map_get__(self, urls, **kwargs):
        def __pool_get__(url):
            try:
                return self.__get__(url, notify=False, **kwargs)
            except Exception:
                # ignore exceptions ???
                return None
        return self.__pool__.map(__pool_get__, urls)
