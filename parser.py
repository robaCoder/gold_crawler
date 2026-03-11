import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup, Tag

from models import BitcoinPrice, GoldPrice, InterGoldPrice, SilverPrice, SilverPriceRow


class GoldPriceParser:
    """Parses HTML from giavang.org to extract domestic gold price data."""

    SECTION_KEYWORDS = {
        "sjc": "Miếng",
        "ring": "Nhẫn",
    }

    def parse(self, html: str) -> GoldPrice:
        soup = BeautifulSoup(html, "html.parser")

        gold_box = soup.find("div", class_="gold-price-box")
        if gold_box is None:
            raise ValueError("Không tìm thấy gold-price-box trong HTML response")

        sjc_section = self._find_section(gold_box, self.SECTION_KEYWORDS["sjc"])
        ring_section = self._find_section(gold_box, self.SECTION_KEYWORDS["ring"])

        sjc = self._parse_section(sjc_section)
        ring = self._parse_section(ring_section)

        return GoldPrice(
            sjc_buy_price=sjc["buy_price"],
            sjc_buy_change=sjc["buy_change"],
            sjc_sell_price=sjc["sell_price"],
            sjc_sell_change=sjc["sell_change"],
            ring_buy_price=ring["buy_price"],
            ring_buy_change=ring["buy_change"],
            ring_sell_price=ring["sell_price"],
            ring_sell_change=ring["sell_change"],
            updated_at=self._extract_update_time(soup),
            crawled_at=datetime.now(),
        )

    def _find_section(self, container: Tag, keyword: str) -> Optional[Tag]:
        for h2 in container.find_all("h2"):
            link = h2.find("a")
            if link and keyword in link.get_text():
                return h2.find_next_sibling("div", class_="row")
        return None

    def _parse_section(self, section: Optional[Tag]) -> dict:
        empty = {"buy_price": "", "buy_change": "", "sell_price": "", "sell_change": ""}
        if section is None:
            return empty

        cols = section.find_all("div", class_="col-6")
        buy_col = cols[0] if len(cols) > 0 else None
        sell_col = cols[1] if len(cols) > 1 else None

        return {
            "buy_price": self._extract_value(buy_col, "gold-price"),
            "buy_change": self._extract_value(buy_col, "gold-change"),
            "sell_price": self._extract_value(sell_col, "gold-price"),
            "sell_change": self._extract_value(sell_col, "gold-change"),
        }

    def _extract_value(self, col: Optional[Tag], css_class: str) -> str:
        if col is None:
            return ""
        span = col.find("span", class_=css_class)
        if span is None:
            return ""
        return _get_direct_text(span)

    @staticmethod
    def _extract_update_time(soup: BeautifulSoup) -> str:
        h1 = soup.find("h1", class_="box-headline")
        if h1:
            small = h1.find("small")
            if small:
                match = re.search(r"Cập nhật lúc\s+(.+)", small.get_text(strip=True))
                if match:
                    return match.group(1).strip()
        return ""


class InterGoldPriceParser:
    """Parses HTML from giavang.org/the-gioi/ to extract international gold price data."""

    def parse(self, html: str) -> InterGoldPrice:
        soup = BeautifulSoup(html, "html.parser")

        crypto_box = soup.find("div", class_="crypto-price-box")
        if crypto_box is None:
            raise ValueError("Không tìm thấy crypto-price-box trong HTML response")

        price = self._extract_price(crypto_box)
        change, change_percent = self._extract_change(crypto_box)
        price_vn = self._extract_price_vn(soup)
        updated_at = self._extract_update_time(soup)

        return InterGoldPrice(
            price=price,
            change=change,
            change_percent=change_percent,
            price_vn=price_vn,
            updated_at=updated_at,
            crawled_at=datetime.now(),
        )

    @staticmethod
    def _extract_price(crypto_box: Tag) -> str:
        span = crypto_box.find("span", class_="crypto-price")
        if span is None:
            return ""
        return span.get("data-price", span.get_text(strip=True))

    @staticmethod
    def _extract_change(crypto_box: Tag) -> tuple[str, str]:
        span = crypto_box.find("span", class_="crypto-change")
        if span is None:
            return "", ""

        change = _get_direct_text(span)

        change_percent = ""
        small = span.find("small")
        if small:
            text = small.get_text(strip=True)
            match = re.search(r"\(([^)]+)%\)", text)
            if match:
                change_percent = match.group(1)

        return change, change_percent

    @staticmethod
    def _extract_price_vn(soup: BeautifulSoup) -> str:
        box_content = soup.find("div", class_="box-content")
        if box_content is None:
            return ""
        for strong in box_content.find_all("strong"):
            text = strong.get_text(strip=True)
            match = re.search(r"có giá là\s+([\d.,]+)\s*VNĐ", text)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def _extract_update_time(soup: BeautifulSoup) -> str:
        h1 = soup.find("h1", class_="box-headline")
        if h1:
            small = h1.find("small")
            if small:
                match = re.search(r"Cập nhật lúc\s+(.+)", small.get_text(strip=True))
                if match:
                    return match.group(1).strip()
        return ""


class SilverPriceParser:
    """Parses HTML from giabac.net to extract silver price data."""

    def parse(self, html: str) -> SilverPrice:
        soup = BeautifulSoup(html, "html.parser")

        cols = soup.find_all("div", class_="thitruong")
        if len(cols) < 2:
            raise ValueError("Không tìm thấy bảng giá bạc trong HTML response")

        usd_rows = self._parse_table(cols[0])
        vnd_rows = self._parse_table(cols[1])

        return SilverPrice(
            usd_rows=usd_rows,
            vnd_rows=vnd_rows,
            crawled_at=datetime.now(),
        )

    @staticmethod
    def _parse_table(col: Tag) -> list[SilverPriceRow]:
        table = col.find("table")
        if table is None:
            return []
        rows: list[SilverPriceRow] = []
        for tr in table.find_all("tr")[2:]:
            tds = tr.find_all("td")
            if len(tds) >= 3:
                rows.append(SilverPriceRow(
                    unit=tds[0].get_text(strip=True),
                    buy_price=tds[1].get_text(strip=True),
                    sell_price=tds[2].get_text(strip=True),
                ))
        return rows


class BitcoinPriceParser:
    """Parses HTML from webgia.com to extract Bitcoin price data."""

    ROW_KEYS = {
        "Vốn hóa thị trường": "market_cap",
        "Thanh khoản (24h)": "liquidity",
        "Tổng BTC hiện có": "total_supply",
        "Dao động 1 giờ": "change_1h",
        "Dao động 24 giờ": "change_24h",
        "Dao động 7 ngày": "change_7d",
    }

    def parse(self, html: str) -> BitcoinPrice:
        soup = BeautifulSoup(html, "html.parser")

        price = self._extract_price(soup)
        change_percent = self._extract_change_percent(soup)
        price_vn = self._extract_price_vn(soup)
        table_data = self._extract_table(soup)

        return BitcoinPrice(
            price=price,
            change_percent=change_percent,
            price_vn=price_vn,
            market_cap=table_data.get("market_cap", ""),
            liquidity=table_data.get("liquidity", ""),
            total_supply=table_data.get("total_supply", ""),
            change_1h=table_data.get("change_1h", ""),
            change_24h=table_data.get("change_24h", ""),
            change_7d=table_data.get("change_7d", ""),
            crawled_at=datetime.now(),
        )

    @staticmethod
    def _extract_price(soup: BeautifulSoup) -> str:
        span = soup.find("span", id="quote_price")
        if span is None:
            return ""
        return span.get_text(strip=True)

    @staticmethod
    def _extract_change_percent(soup: BeautifulSoup) -> str:
        coin_price = soup.find("div", class_="coin-price")
        if coin_price is None:
            return ""
        spans = coin_price.find_all("span", class_="text-large")
        for span in spans:
            text = span.get_text(strip=True)
            match = re.search(r"\(([^)]+)%\)", text)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def _extract_price_vn(soup: BeautifulSoup) -> str:
        strong = soup.find("strong", class_="text-primary")
        if strong is None:
            return ""
        text = strong.get_text(strip=True)
        match = re.search(r"~([\d.,]+)\s*đồng", text)
        if match:
            return match.group(1)
        return ""

    def _extract_table(self, soup: BeautifulSoup) -> dict:
        result = {}
        table = soup.find("table", id="coin-table")
        if table is None:
            return result
        for tr in table.find_all("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if th is None or td is None:
                continue
            header = th.get_text(strip=True)
            key = self.ROW_KEYS.get(header)
            if key is None:
                continue
            value = td.get_text(strip=True)
            value = re.sub(r"Mua/bán Bitcoin.*", "", value).strip()
            if key == "total_supply":
                value = value.replace("BTC", "").strip()
            elif key in ("change_1h", "change_24h", "change_7d"):
                match = re.search(r"([+-]?\s*[\d.,]+)%", value)
                value = match.group(1).replace(" ", "") if match else value
            result[key] = value
        return result


def _get_direct_text(element: Tag) -> str:
    """Return the first direct text node of an element, ignoring child tags."""
    for child in element.children:
        if isinstance(child, str):
            text = child.strip()
            if text:
                return text
    return ""
