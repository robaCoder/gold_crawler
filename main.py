import json
import sys
from pathlib import Path

from crawler import BitcoinPriceCrawler, GoldPriceCrawler, InterGoldPriceCrawler, SilverPriceCrawler
from models import BitcoinPrice, GoldPrice, InterGoldPrice, SilverPrice
from renderer import BitcoinPriceRenderer, DomesticGoldRenderer, InterGoldRenderer, SilverPriceRenderer

PROMPT_TEMPLATE = Path(__file__).parent / "default_prompt.txt"
PROMPT_OUTPUT = Path(__file__).parent / "updated_prompt.txt"


def main() -> None:
    domestic_crawler = GoldPriceCrawler()
    inter_crawler = InterGoldPriceCrawler()
    silver_crawler = SilverPriceCrawler()
    bitcoin_crawler = BitcoinPriceCrawler()

    domestic_renderer = DomesticGoldRenderer()
    inter_renderer = InterGoldRenderer()
    silver_renderer = SilverPriceRenderer()
    bitcoin_renderer = BitcoinPriceRenderer()

    # ── Crawl domestic gold ──────────────────────────────────────────────
    print("[1/4] Đang crawl giá vàng trong nước...")
    try:
        domestic = domestic_crawler.crawl()
    except Exception as exc:
        print(f"  [ERROR] {exc}", file=sys.stderr)
        domestic = None

    # ── Crawl international gold ─────────────────────────────────────────
    print("[2/4] Đang crawl giá vàng thế giới...")
    try:
        inter = inter_crawler.crawl()
    except Exception as exc:
        print(f"  [ERROR] {exc}", file=sys.stderr)
        inter = None

    # ── Crawl silver ─────────────────────────────────────────────────────
    print("[3/4] Đang crawl giá bạc thế giới...")
    try:
        silver = silver_crawler.crawl()
    except Exception as exc:
        print(f"  [ERROR] {exc}", file=sys.stderr)
        silver = None

    # ── Crawl bitcoin ────────────────────────────────────────────────────
    print("[4/4] Đang crawl giá Bitcoin...")
    try:
        bitcoin = bitcoin_crawler.crawl()
    except Exception as exc:
        print(f"  [ERROR] {exc}", file=sys.stderr)
        bitcoin = None

    # ── Display results ──────────────────────────────────────────────────
    print()
    for data in (domestic, inter, silver, bitcoin):
        if data:
            print(data)
            print()

    # ── Render images ────────────────────────────────────────────────────
    if domestic:
        path = domestic_renderer.render(domestic)
        print(f"[IMAGE] Giá vàng trong nước -> {path}")

    if inter:
        path = inter_renderer.render(inter)
        print(f"[IMAGE] Giá vàng thế giới   -> {path}")

    if silver:
        path = silver_renderer.render(silver)
        print(f"[IMAGE] Giá bạc thế giới    -> {path}")

    if bitcoin:
        path = bitcoin_renderer.render(bitcoin)
        print(f"[IMAGE] Bitcoin              -> {path}")

    # ── JSON output ──────────────────────────────────────────────────────
    print("\n--- JSON ---")
    result = {}
    if domestic:
        result["domestic"] = domestic.to_dict()
    if inter:
        result["international"] = inter.to_dict()
    if silver:
        result["silver"] = silver.to_dict()
    if bitcoin:
        result["bitcoin"] = bitcoin.to_dict()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    open("result.json", "w", encoding="utf-8").write(json.dumps(result, ensure_ascii=False, indent=2))

    # ── Update prompt ────────────────────────────────────────────────────
    update_prompt(domestic, inter, silver, bitcoin)


def _silver_val(silver: SilverPrice | None, table: str, idx: int, field: str) -> str:
    if silver is None:
        return ""
    rows = silver.usd_rows if table == "usd" else silver.vnd_rows
    if idx >= len(rows):
        return ""
    return getattr(rows[idx], field, "")


def _build_replacements(
    domestic: GoldPrice | None,
    inter: InterGoldPrice | None,
    silver: SilverPrice | None,
    bitcoin: BitcoinPrice | None,
) -> dict[str, str]:
    g = domestic
    i = inter
    b = bitcoin

    return {
        "SJC_BUY_PRICE": g.sjc_buy_price if g else "",
        "SJC_BUY_CHANGE": g.sjc_buy_change if g else "",
        "SJC_SELL_PRICE": g.sjc_sell_price if g else "",
        "SJC_SELL_CHANGE": g.sjc_sell_change if g else "",
        "RING_BUY_PRICE": g.ring_buy_price if g else "",
        "RING_BUY_CHANGE": g.ring_buy_change if g else "",
        "RING_SELL_PRICE": g.ring_sell_price if g else "",
        "RING_SELL_CHANGE": g.ring_sell_change if g else "",
        "INTER_GOLD_PRICE": i.price if i else "",
        "INTER_GOLD_CHANGE_PERCENT": i.change_percent if i else "",
        "INTER_GOLD_CHANGE": i.change if i else "",
        "INTER_GOLD_UPDATED_AT": i.updated_at if i else "",
        "INTER_GOLD_PRICE_VN": i.price_vn if i else "",
        "SILVER_OUNCE_BUY_PRICE": _silver_val(silver, "usd", 0, "buy_price"),
        "SILVER_OUNCE_SELL_PRICE": _silver_val(silver, "usd", 0, "sell_price"),
        "SILVER_GRAM_BUY_PRICE": _silver_val(silver, "usd", 1, "buy_price"),
        "SILVER_GRAM_SELL_PRICE": _silver_val(silver, "usd", 1, "sell_price"),
        "SILVER_LG_BUY_PRICE": _silver_val(silver, "usd", 2, "buy_price"),
        "SILVER_LG_SELL_PRICE": _silver_val(silver, "usd", 2, "sell_price"),
        "SILVER_KG_BUY_PRICE": _silver_val(silver, "usd", 3, "buy_price"),
        "SILVER_KG_SELL_PRICE": _silver_val(silver, "usd", 3, "sell_price"),
        "SILVER_OUNCE_BUY_PRICE_VN": _silver_val(silver, "vnd", 0, "buy_price"),
        "SILVER_OUNCE_SELL_PRICE_VN": _silver_val(silver, "vnd", 0, "sell_price"),
        "SILVER_CHI_BUY_PRICE_VN": _silver_val(silver, "vnd", 1, "buy_price"),
        "SILVER_CHI_SELL_PRICE_VN": _silver_val(silver, "vnd", 1, "sell_price"),
        "SILVER_LG_BUY_PRICE_VN": _silver_val(silver, "vnd", 2, "buy_price"),
        "SILVER_LG_SELL_PRICE_VN": _silver_val(silver, "vnd", 2, "sell_price"),
        "SILVER_KG_BUY_PRICE_VN": _silver_val(silver, "vnd", 3, "buy_price"),
        "SILVER_KG_SELL_PRICE_VN": _silver_val(silver, "vnd", 3, "sell_price"),
        "BITCOIN_PRICE": b.price if b else "",
        "BITCOIN_CHANGE_PERCENT": b.change_percent if b else "",
        "BITCOIN_PRICE_VN": b.price_vn if b else "",
        "BITCOIN_MARKET_CAP": b.market_cap if b else "",
        "BITCOIN_LIQUIDITY": b.liquidity if b else "",
        "BITCOIN_TOTAL_SUPPLY": b.total_supply if b else "",
        "BITCOIN_CHANGE_PERCENT_1H": b.change_1h if b else "",
        "BITCOIN_CHANGE_PERCENT_24H": b.change_24h if b else "",
        "BITCOIN_CHANGE_PERCENT_7D": b.change_7d if b else "",
    }


def update_prompt(
    domestic: GoldPrice | None,
    inter: InterGoldPrice | None,
    silver: SilverPrice | None,
    bitcoin: BitcoinPrice | None,
) -> None:
    if not PROMPT_TEMPLATE.exists():
        print("[PROMPT] default_prompt.txt không tồn tại, bỏ qua.", file=sys.stderr)
        return

    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    replacements = _build_replacements(domestic, inter, silver, bitcoin)

    result = template
    for key, value in replacements.items():
        result = result.replace(f"[[{key}]]", value)

    PROMPT_OUTPUT.write_text(result, encoding="utf-8")
    print(f"[PROMPT] Đã lưu -> {PROMPT_OUTPUT}")


if __name__ == "__main__":
    main()
