# -*- coding: utf-8 -*-


from re import escape, search
from time import time
from urllib.parse import parse_qs, urlparse, urlunparse, urlencode

from yt_dlp.jsinterp import JSInterpreter

from .find import MatchError, __find__

# ------------------------------------------------------------------------------
# Solver

__decipherFuncNamePatterns__ = (
    r'\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
    r'\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
    r'\bm=(?P<sig>[a-zA-Z0-9$]{2,})\(decodeURIComponent\(h\.s\)\)',
    r'\bc&&\(c=(?P<sig>[a-zA-Z0-9$]{2,})\(decodeURIComponent\(c\)\)',
    r'(?:\b|[^a-zA-Z0-9$])(?P<sig>[a-zA-Z0-9$]{2,})\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\);[a-zA-Z0-9$]{2}\.[a-zA-Z0-9$]{2}\(a,\d+\)',
    r'(?:\b|[^a-zA-Z0-9$])(?P<sig>[a-zA-Z0-9$]{2,})\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
    r'(?P<sig>[a-zA-Z0-9$]+)\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
    # Obsolete patterns
    r'(["\'])signature\1\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
    r'\.sig\|\|(?P<sig>[a-zA-Z0-9$]+)\(',
    r'yt\.akamaized\.net/\)\s*\|\|\s*.*?\s*[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*(?:encodeURIComponent\s*\()?\s*(?P<sig>[a-zA-Z0-9$]+)\(',
    r'\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
    r'\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
    r'\bc\s*&&\s*a\.set\([^,]+\s*,\s*\([^)]*\)\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
    r'\bc\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*\([^)]*\)\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
    r'\bc\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*\([^)]*\)\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\('
)

def findDecipherFuncName(js):
    for pattern in __decipherFuncNamePatterns__:
        try:
            return __find__(pattern, js).group('sig')
        except MatchError:
            continue
    raise MatchError('signature function name')


__descrambleFuncNamePatterns__ = (
    #r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&\s*'
    #r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)',
    r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&.*?\|\|\s*([a-z]+)',
    r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)',
)

def findDescrambleFuncName(js):
    for pattern in __descrambleFuncNamePatterns__:
        try:
            match = __find__(pattern, js)
            if match:
                if len(match.groups()) == 1:
                    return match.group(1)
                idx = match.group(2)
                if idx:
                    idx = idx.strip("[]")
                    array = search(
                        r'var {nfunc}\s*=\s*(\[.+?\]);'.format(
                            nfunc=escape(match.group(1))),
                        js
                    )
                    if array:
                        array = array.group(1).strip("[]").split(",")
                        array = [x.strip() for x in array]
                        return array[int(idx)]
        except MatchError:
            continue
    raise MatchError('throttling function name')


class Solver(object):

    def __init__(self, js, expire=3600):
        self.__expire__ = time() + expire
        self.__cache__ = {}
        jsi = JSInterpreter(js)
        self.__jsdecipher__ = jsi.extract_function(findDecipherFuncName(js))
        self.__jsdescramble__ = jsi.extract_function(findDescrambleFuncName(js))

    def __decipher__(self, c):
        url = c['url'][0]
        if 'signature' in url:
            return url
        if 's' not in c:
            if ('&sig=' in url) or ('&lsig=' in url):
                return url
            raise Exception('missing signature')
        return '&'.join(
            (url, '='.join((c['sp'][0], self.__jsdecipher__(c['s']))))
        )

    def __fromCache__(self, key, func, *args):
        if (not (value := self.__cache__.get(key))):
            value = self.__cache__[key] = func(*(args or (key,)))
        return value

    def __descramble__(self, n):
        if (r := self.__jsdescramble__(n)) and r.startswith('enhanced_except_'):
            raise Exception('error while descrambling')
        return [r]

    def extractUrl(self, stream):
        try:
            url = stream['url']
        except KeyError:
            try:
                c = stream['cipher']
            except KeyError:
                c = stream['signatureCipher']
            url = self.__decipher__(parse_qs(c))
        url = urlparse(url)
        q = parse_qs(url.query)
        if (n := q.get('n')):
            q['n'] = self.__fromCache__(n[-1], self.__descramble__, n)
        return urlunparse(url._replace(query=urlencode(q, True)))
