from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class GoldPrice:
    sjc_buy_price: str = ""
    sjc_buy_change: str = ""
    sjc_sell_price: str = ""
    sjc_sell_change: str = ""
    ring_buy_price: str = ""
    ring_buy_change: str = ""
    ring_sell_price: str = ""
    ring_sell_change: str = ""
    updated_at: str = ""
    crawled_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["crawled_at"] = self.crawled_at.isoformat()
        return data

    def _parse_number(self, value: str) -> Optional[float]:
        if not value:
            return None
        cleaned = value.replace(",", "").replace(".", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    @property
    def sjc_buy_price_num(self) -> Optional[float]:
        return self._parse_number(self.sjc_buy_price)

    @property
    def sjc_sell_price_num(self) -> Optional[float]:
        return self._parse_number(self.sjc_sell_price)

    @property
    def ring_buy_price_num(self) -> Optional[float]:
        return self._parse_number(self.ring_buy_price)

    @property
    def ring_sell_price_num(self) -> Optional[float]:
        return self._parse_number(self.ring_sell_price)

    def __str__(self) -> str:
        lines = [
            f"=== Giá Vàng Trong Nước ({self.updated_at}) ===",
            f"  [SJC Miếng]  Mua: {self.sjc_buy_price}  ({self.sjc_buy_change})"
            f"  |  Bán: {self.sjc_sell_price}  ({self.sjc_sell_change})",
            f"  [SJC Nhẫn]   Mua: {self.ring_buy_price}  ({self.ring_buy_change})"
            f"  |  Bán: {self.ring_sell_price}  ({self.ring_sell_change})",
            f"  Crawled at: {self.crawled_at:%Y-%m-%d %H:%M:%S}",
        ]
        return "\n".join(lines)


@dataclass
class InterGoldPrice:
    price: str = ""
    change: str = ""
    change_percent: str = ""
    price_vn: str = ""
    updated_at: str = ""
    crawled_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["crawled_at"] = self.crawled_at.isoformat()
        return data

    @property
    def is_negative(self) -> bool:
        return self.change.strip().startswith("-")

    def __str__(self) -> str:
        sign = "" if self.is_negative else "+"
        lines = [
            f"=== Giá Vàng Thế Giới ({self.updated_at}) ===",
            f"  Giá: {self.price} USD",
            f"  Thay đổi: {sign}{self.change} USD ({sign}{self.change_percent}%)",
            f"  Quy đổi: {self.price_vn} VNĐ/lượng",
            f"  Crawled at: {self.crawled_at:%Y-%m-%d %H:%M:%S}",
        ]
        return "\n".join(lines)


@dataclass
class SilverPriceRow:
    unit: str = ""
    buy_price: str = ""
    sell_price: str = ""


@dataclass
class SilverPrice:
    usd_rows: List[SilverPriceRow] = field(default_factory=list)
    vnd_rows: List[SilverPriceRow] = field(default_factory=list)
    crawled_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "usd": [asdict(r) for r in self.usd_rows],
            "vnd": [asdict(r) for r in self.vnd_rows],
            "crawled_at": self.crawled_at.isoformat(),
        }

    def __str__(self) -> str:
        lines = ["=== Giá Bạc Thế Giới ==="]
        lines.append("  [USD]")
        for r in self.usd_rows:
            lines.append(f"    {r.unit:<10} Mua: {r.buy_price:<12} Bán: {r.sell_price}")
        lines.append("  [VND]")
        for r in self.vnd_rows:
            lines.append(f"    {r.unit:<10} Mua: {r.buy_price:<16} Bán: {r.sell_price}")
        lines.append(f"  Crawled at: {self.crawled_at:%Y-%m-%d %H:%M:%S}")
        return "\n".join(lines)


@dataclass
class BitcoinPrice:
    price: str = ""
    change_percent: str = ""
    price_vn: str = ""
    market_cap: str = ""
    liquidity: str = ""
    total_supply: str = ""
    change_1h: str = ""
    change_24h: str = ""
    change_7d: str = ""
    crawled_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["crawled_at"] = self.crawled_at.isoformat()
        return data

    def __str__(self) -> str:
        lines = [
            f"=== Bitcoin - BTC/USD ===",
            f"  Giá: ${self.price}  ({self.change_percent}%)",
            f"  Quy đổi VNĐ: {self.price_vn}",
            f"  Vốn hóa: ${self.market_cap}",
            f"  Thanh khoản 24h: ${self.liquidity}",
            f"  Tổng BTC: {self.total_supply}",
            f"  Dao động 1h: {self.change_1h}%  |  24h: {self.change_24h}%  |  7d: {self.change_7d}%",
            f"  Crawled at: {self.crawled_at:%Y-%m-%d %H:%M:%S}",
        ]
        return "\n".join(lines)
