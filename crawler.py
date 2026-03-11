from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import requests

from models import BitcoinPrice, GoldPrice, InterGoldPrice, SilverPrice
from parser import BitcoinPriceParser, GoldPriceParser, InterGoldPriceParser, SilverPriceParser


class BaseCrawler(ABC):
    """Abstract base class for all crawlers."""

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers or {}
        self.session = requests.Session()

    def fetch(self) -> str:
        response = self.session.get(self.url, headers=self.headers)
        response.raise_for_status()
        return response.text

    @abstractmethod
    def parse(self, html: str) -> Any:
        ...

    def crawl(self) -> Any:
        html = self.fetch()
        return self.parse(html)


SHARED_HEADERS: Dict[str, str] = {
    "accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;"
        "q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
    ),
}


class GoldPriceCrawler(BaseCrawler):
    """Crawler for domestic gold prices from giavang.org."""

    URL = "https://giavang.org/"

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        super().__init__(self.URL, headers or SHARED_HEADERS)
        self._parser = GoldPriceParser()

    def parse(self, html: str) -> GoldPrice:
        return self._parser.parse(html)


class InterGoldPriceCrawler(BaseCrawler):
    """Crawler for international gold prices from giavang.org/the-gioi/."""

    URL = "https://giavang.org/the-gioi/"

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        h = dict(headers or SHARED_HEADERS)
        h["referer"] = "https://giavang.org/trong-nuoc/"
        h["sec-fetch-site"] = "same-origin"
        super().__init__(self.URL, h)
        self._parser = InterGoldPriceParser()

    def parse(self, html: str) -> InterGoldPrice:
        return self._parser.parse(html)


class SilverPriceCrawler(BaseCrawler):
    """Crawler for silver prices from giabac.net."""

    URL = "https://giabac.net/"

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        h = dict(headers or SHARED_HEADERS)
        h["referer"] = "https://giabac.net/san-pham"
        h["sec-fetch-site"] = "same-origin"
        super().__init__(self.URL, h)
        self._parser = SilverPriceParser()

    def parse(self, html: str) -> SilverPrice:
        return self._parser.parse(html)


class BitcoinPriceCrawler(BaseCrawler):
    """Crawler for Bitcoin prices from webgia.com."""

    URL = "https://webgia.com/tien-ao/bitcoin/"

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        h = dict(headers or SHARED_HEADERS)
        h["referer"] = "https://webgia.com/tien-ao/bitcoin/"
        h["sec-fetch-site"] = "same-origin"
        h["connection"] = "keep-alive"
        super().__init__(self.URL, h)
        self._parser = BitcoinPriceParser()

    def parse(self, html: str) -> BitcoinPrice:
        return self._parser.parse(html)
