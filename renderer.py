from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFont

from models import BitcoinPrice, GoldPrice, InterGoldPrice, SilverPrice

# ── Colour palette ──────────────────────────────────────────────────────────
BG_LIGHT = (255, 255, 255)
CARD_BG = (26, 42, 78)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
GREEN = (101, 188, 0)
RED = (255, 0, 0)
DIVIDER = (50, 65, 105)
TEXT_BLUE = (0, 49, 94)
TEXT_GRAY = (117, 117, 117)
TEXT_BLACK = (0, 0, 0)
TABLE_HEADER_BG = (0, 49, 94)
TABLE_ROW_ALT = (235, 242, 250)
TABLE_BORDER = (180, 195, 215)


# ── Font helpers ────────────────────────────────────────────────────────────
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

_FONT_REGULAR_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = _FONT_CANDIDATES if bold else _FONT_REGULAR_CANDIDATES
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


class BaseRenderer(ABC):
    """Abstract base for rendering gold price data to images."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def render(self, data: Any) -> Path:
        ...

    @staticmethod
    def _draw_rounded_rect(
        draw: ImageDraw.ImageDraw,
        xy: tuple[int, int, int, int],
        radius: int,
        fill: tuple,
    ) -> None:
        draw.rounded_rectangle(xy, radius=radius, fill=fill)

    @staticmethod
    def _change_color(change_text: str) -> tuple:
        text = change_text.strip()
        if text.startswith("-"):
            return RED
        if text.startswith("+") or (text and text[0].isdigit()):
            return GREEN
        return TEXT_GRAY

    @staticmethod
    def _change_arrow(change_text: str) -> str:
        text = change_text.strip()
        if text.startswith("-"):
            return "▼"
        return "▲"

    @staticmethod
    def _compute_col_widths(table_w: int, ratios: tuple) -> list[int]:
        widths = [int(table_w * r) for r in ratios]
        widths[-1] = table_w - sum(widths[:-1])
        return widths

    def _draw_table(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        title: str,
        headers: list[str],
        rows: list[tuple],
        col_widths: list[int],
        fonts: tuple,
        cell_colors: list[tuple] | None = None,
    ) -> int:
        """Draw a styled table. Returns the y position after the table.

        cell_colors: optional per-row list of color tuples matching column count.
                     None entries fall back to TEXT_BLACK.
        """
        font_title, font_header, font_cell = fonts
        table_w = sum(col_widths)
        row_h = 34
        header_h = 36
        title_h = 38
        cell_pad = 10
        start_y = y

        # ── Title bar ───────────────────────────────────────────────────
        draw.rounded_rectangle(
            (x, y, x + table_w, y + title_h),
            radius=8,
            fill=TABLE_HEADER_BG,
            corners=(True, True, False, False),
        )
        title_bbox = draw.textbbox((0, 0), title, font=font_title)
        title_text_w = title_bbox[2] - title_bbox[0]
        draw.text(
            (x + (table_w - title_text_w) // 2, y + (title_h - font_title.size) // 2),
            title,
            font=font_title,
            fill=WHITE,
        )
        y += title_h

        # ── Column headers ──────────────────────────────────────────────
        draw.rectangle((x, y, x + table_w, y + header_h), fill=CARD_BG)
        cx = x
        for i, hdr in enumerate(headers):
            hdr_bbox = draw.textbbox((0, 0), hdr, font=font_header)
            hdr_w = hdr_bbox[2] - hdr_bbox[0]
            if i == 0:
                tx = cx + cell_pad
            else:
                tx = cx + col_widths[i] - hdr_w - cell_pad
            draw.text((tx, y + (header_h - font_header.size) // 2), hdr, font=font_header, fill=WHITE)
            cx += col_widths[i]
        y += header_h

        # ── Data rows ───────────────────────────────────────────────────
        for row_idx, row_data in enumerate(rows):
            bg = TABLE_ROW_ALT if row_idx % 2 == 0 else BG_LIGHT
            is_last = row_idx == len(rows) - 1

            if is_last:
                draw.rounded_rectangle(
                    (x, y, x + table_w, y + row_h),
                    radius=8, fill=bg,
                    corners=(False, False, True, True),
                )
            else:
                draw.rectangle((x, y, x + table_w, y + row_h), fill=bg)

            cx = x
            for i, cell in enumerate(row_data):
                cell_str = str(cell)
                cell_bbox = draw.textbbox((0, 0), cell_str, font=font_cell)
                cell_w = cell_bbox[2] - cell_bbox[0]

                color = TEXT_BLACK
                if cell_colors and row_idx < len(cell_colors) and cell_colors[row_idx] is not None:
                    color = cell_colors[row_idx][i] if i < len(cell_colors[row_idx]) else TEXT_BLACK

                if i == 0:
                    tx = cx + cell_pad
                else:
                    tx = cx + col_widths[i] - cell_w - cell_pad
                draw.text(
                    (tx, y + (row_h - font_cell.size) // 2),
                    cell_str, font=font_cell, fill=color,
                )
                cx += col_widths[i]

            if not is_last:
                draw.line(
                    [(x, y + row_h), (x + table_w, y + row_h)],
                    fill=TABLE_BORDER, width=1,
                )
            y += row_h

        # ── Outer border ────────────────────────────────────────────────
        draw.rounded_rectangle(
            (x, start_y + title_h, x + table_w, y),
            radius=8,
            outline=TABLE_HEADER_BG,
            width=1,
            corners=(False, False, True, True),
        )
        return y


class DomesticGoldRenderer(BaseRenderer):
    """Renders domestic gold price data (SJC Miếng + Nhẫn) to a JPEG image."""

    WIDTH = 820
    HEIGHT = 420
    PADDING = 30

    def render(self, data: GoldPrice) -> Path:
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), BG_LIGHT)
        draw = ImageDraw.Draw(img)

        font_title = _load_font(26, bold=True)
        font_sub = _load_font(14)
        font_label = _load_font(15, bold=True)
        font_price = _load_font(32, bold=True)
        font_change = _load_font(16)
        font_section = _load_font(18, bold=True)
        font_footer = _load_font(12)

        y = self.PADDING
        # LINE DIVIDER
        y += 10

        # ── Title ───────────────────────────────────────────────────────
        draw.text((self.PADDING, y), "GIÁ VÀNG MIẾNG SJC HÔM NAY", font=font_title, fill=TEXT_BLUE)
        y += 36
        draw.text(
            (self.PADDING, y),
            f"Cập nhật lúc {data.updated_at}",
            font=font_sub,
            fill=TEXT_GRAY,
        )

        y += 30
        draw.line([(self.PADDING, y), (self.WIDTH - self.PADDING, y)], fill=DIVIDER, width=1)
        y += 15

        # ── SJC Miếng card ──────────────────────────────────────────────
        y = self._draw_price_card(
            draw, y,
            title="Giá vàng Miếng SJC",
            buy_price=data.sjc_buy_price,
            buy_change=data.sjc_buy_change,
            sell_price=data.sjc_sell_price,
            sell_change=data.sjc_sell_change,
            fonts=(font_section, font_label, font_price, font_change, font_footer),
        )

        draw.line([(self.PADDING, y), (self.WIDTH - self.PADDING, y)], fill=TEXT_GRAY, width=1)
        y += 8

        # ── SJC Nhẫn card ───────────────────────────────────────────────
        y = self._draw_price_card(
            draw, y,
            title="Giá vàng Nhẫn SJC",
            buy_price=data.ring_buy_price,
            buy_change=data.ring_buy_change,
            sell_price=data.ring_sell_price,
            sell_change=data.ring_sell_change,
            fonts=(font_section, font_label, font_price, font_change, font_footer),
        )

        path = self.output_dir / "domestic_gold.jpeg"
        img.save(path, "JPEG", quality=100)
        return path

    def _draw_price_card(
        self,
        draw: ImageDraw.ImageDraw,
        y: int,
        title: str,
        buy_price: str,
        buy_change: str,
        sell_price: str,
        sell_change: str,
        fonts: tuple,
    ) -> int:
        font_section, font_label, font_price, font_change, font_footer = fonts
        card_x = self.PADDING
        card_w = self.WIDTH - 2 * self.PADDING
        card_h = 140
        mid_x = self.PADDING + card_w // 2

        self._draw_rounded_rect(draw, (card_x, y, card_x + card_w, y + card_h), 14, BG_LIGHT)

        # Section title
        draw.text((card_x + 20, y + 12), title, font=font_section, fill=TEXT_BLUE)
        inner_y = y + 45

        # Buy side
        self._draw_price_column(
            draw, card_x + 30, inner_y,
            label="MUA VÀO",
            price=buy_price,
            change=buy_change,
            fonts=(font_label, font_price, font_change, font_footer),
        )

        self._draw_price_column(
            draw, mid_x + 30, inner_y,
            label="BÁN RA",
            price=sell_price,
            change=sell_change,
            fonts=(font_label, font_price, font_change, font_footer),
        )

        return y + card_h

    def _draw_price_column(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        label: str,
        price: str,
        change: str,
        fonts: tuple,
    ) -> None:
        font_label, font_price, font_change, font_footer = fonts

        color = TEXT_GRAY
        if change:
            color = self._change_color(change)

        draw.line([(x - 10, y), (x - 10, y + font_label.size + font_price.size + 20)], fill=color, width=5)

        draw.text((x, y), label, font=font_label, fill=TEXT_GRAY)
        draw.text((x, y + 26), price, font=font_price, fill=TEXT_BLACK)

        unit_text = "x1000đ/lượng"
        draw.text((x + font_price.getbbox(price)[2] + 10, y + 60 - font_footer.size), unit_text, font=font_footer, fill=TEXT_GRAY)


class InterGoldRenderer(BaseRenderer):
    """Renders international gold price data (XAU/USD) to a JPEG image."""

    WIDTH = 820
    HEIGHT = 420
    PADDING = 30

    def render(self, data: InterGoldPrice) -> Path:
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), BG_LIGHT)
        draw = ImageDraw.Draw(img)

        font_title = _load_font(32, bold=True)
        font_sub = _load_font(16)
        font_sub_bold = _load_font(16, bold=True)
        font_price_big = _load_font(48, bold=True)
        font_unit = _load_font(22)
        font_change = _load_font(34)
        font_vn_label = _load_font(16, bold=True)
        font_vn_price = _load_font(24, bold=True)
        font_footer = _load_font(12)

        x = self.PADDING
        y = self.PADDING

        # ── Title ───────────────────────────────────────────────────────
        draw.text((self.PADDING, y), "GIÁ VÀNG THẾ GIỚI — XAU/USD", font=font_title, fill=TEXT_BLUE)
        draw.text((self.PADDING, y + font_title.size + 10), f"Cập nhật lúc {data.updated_at}", font=font_sub, fill=TEXT_GRAY)

        y += font_title.size + 30

        if data.change:
            color = self._change_color(data.change)
            arrow = self._change_arrow(data.change)
            draw.text((x, y), arrow, font=font_title, fill=color)
            draw.text((x + 40, y), f"{data.price}", font=font_change, fill=TEXT_BLACK)
            draw.text((x + 40 * 4.3, y + 12), "USD", font=font_unit, fill=TEXT_GRAY)
            draw.text((x + 40 * 5.7, y), f"{data.change}", font=font_change, fill=color)
            draw.text((x + 40 * 8.3, y + 12), "USD", font=font_unit, fill=TEXT_GRAY)
            draw.text((x + 40 * 9.7, y + 6), f"({data.change_percent}%)", font=_load_font(26), fill=color)

        draw.line([(x, y + font_title.size + 20), (self.WIDTH - self.PADDING, y + font_title.size + 20)], fill=DIVIDER, width=1)
        draw.text((self.PADDING, y + font_title.size + 20 * 2), f"Giá vàng quốc tế (XAU) hôm nay là                 , cập nhật lúc {data.updated_at}", font=font_sub, fill=TEXT_BLACK)
        draw.text((self.PADDING + 245, y + font_title.size + 20 * 2), data.price, font=font_sub_bold, fill=TEXT_BLACK)
        draw.text((self.PADDING, y + font_title.size + 20 * 4), "Giá vàng quốc tế nhìn chung có", font=font_sub, fill=TEXT_BLACK)
        draw.text((self.PADDING + 222, y + font_title.size + 20 * 4), ("giảm" if data.change.startswith("-") else "tăng +") + f" {data.change_percent}% trong 24 giờ qua", font=font_sub_bold, fill=color)
        draw.text((self.PADDING + 222 + 225, y + font_title.size + 20 * 4), ", tương ứng với", font=font_sub, fill=TEXT_BLACK)
        draw.text((self.PADDING + 447 + 110, y + font_title.size + 20 * 4), ("giảm" if data.change.startswith("-") else "tăng +") + f" {data.change} USD/Ounce.", font=font_sub_bold, fill=color)
        draw.text((self.PADDING, y + font_title.size + 20 * 6), "Quy đổi theo tỷ giá Vietcombank thì", font=font_sub, fill=TEXT_BLACK)
        draw.text((self.PADDING + 252, y + font_title.size + 20 * 6), f"1 Ounce = {data.price_vn} VNĐ.", font=font_sub_bold, fill=TEXT_BLACK)
        draw.text((self.PADDING, y + font_title.size + 20 * 8), "Giá vàng thế giới tính theo lượng vàng thì bằng bao nhiêu Việt Nam Đồng?", font=font_sub, fill=TEXT_BLACK)
        draw.text((self.PADDING, y + font_title.size + 20 * 10), "1 Lượng vàng = 1.20565303 Ounce (1 Ounce = 0.829426027 lượng vàng/ cây vàng)", font=font_sub, fill=TEXT_BLACK)
        draw.text((self.PADDING, y + font_title.size + 20 * 12), "Vậy", font=font_sub, fill=TEXT_BLACK)
        draw.text((self.PADDING + 29, y + font_title.size + 20 * 12), f"1 cây vàng theo giá vàng thế giới quy đổi sang tiền Việt Nam Đồng có giá là {data.price_vn} VNĐ.", font=font_sub_bold, fill=TEXT_BLACK)

        path = self.output_dir / "inter_gold.jpeg"
        img.save(path, "JPEG", quality=100)
        return path


class SilverPriceRenderer(BaseRenderer):
    """Renders silver price data as a table in JPEG."""

    WIDTH = 860
    HEIGHT = 340
    PADDING = 30
    TABLE_GAP = 30

    def render(self, data: SilverPrice) -> Path:
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), BG_LIGHT)
        draw = ImageDraw.Draw(img)

        font_title = _load_font(26, bold=True)
        font_sub = _load_font(13)
        font_table_title = _load_font(15, bold=True)
        font_header = _load_font(14, bold=True)
        font_cell = _load_font(14)
        font_footer = _load_font(12)

        y = self.PADDING

        # ── Title ───────────────────────────────────────────────────────
        draw.text((self.PADDING, y), "GIÁ BẠC THẾ GIỚI HÔM NAY", font=font_title, fill=TEXT_BLUE)
        y += 36
        draw.text(
            (self.PADDING, y),
            f"Cập nhật lúc {data.crawled_at:%H:%M:%S %d/%m/%Y}",
            font=font_sub,
            fill=TEXT_GRAY,
        )
        y += 28

        # ── Two tables side by side ─────────────────────────────────────
        usable_w = self.WIDTH - 2 * self.PADDING - self.TABLE_GAP
        table_w = usable_w // 2
        left_x = self.PADDING
        right_x = self.PADDING + table_w + self.TABLE_GAP

        col_widths_usd = self._compute_col_widths(table_w, ratios=(0.30, 0.35, 0.35))
        col_widths_vnd = self._compute_col_widths(table_w, ratios=(0.30, 0.35, 0.35))

        self._draw_table(
            draw, left_x, y,
            title="Giá bạc thế giới (USD)",
            headers=["Đơn vị", "Mua", "Bán"],
            rows=[(r.unit, r.buy_price, r.sell_price) for r in data.usd_rows],
            col_widths=col_widths_usd,
            fonts=(font_table_title, font_header, font_cell),
        )

        self._draw_table(
            draw, right_x, y,
            title="Giá bạc thế giới (VNĐ)",
            headers=["Đơn vị", "Mua", "Bán"],
            rows=[(r.unit, r.buy_price, r.sell_price) for r in data.vnd_rows],
            col_widths=col_widths_vnd,
            fonts=(font_table_title, font_header, font_cell),
        )

        path = self.output_dir / "silver.jpeg"
        img.save(path, "JPEG", quality=100)
        return path


ORANGE = (243, 156, 18)


class BitcoinPriceRenderer(BaseRenderer):
    """Renders Bitcoin price data as a table in JPEG."""

    WIDTH = 620
    HEIGHT = 480
    PADDING = 30

    def render(self, data: BitcoinPrice) -> Path:
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), BG_LIGHT)
        draw = ImageDraw.Draw(img)

        font_title = _load_font(26, bold=True)
        font_price = _load_font(36, bold=True)
        font_pct = _load_font(22)
        font_sub = _load_font(13)
        font_table_title = _load_font(15, bold=True)
        font_header = _load_font(14, bold=True)
        font_cell = _load_font(14)

        y = self.PADDING

        # ── Title ───────────────────────────────────────────────────────
        draw.text((self.PADDING, y), "BITCOIN — BTC/USD", font=font_title, fill=TEXT_BLUE)
        y += 38

        # ── Price + change ──────────────────────────────────────────────
        price_text = f"{data.price}"
        draw.text((self.PADDING, y), price_text, font=font_price, fill=TEXT_BLACK)
        price_bbox = draw.textbbox((self.PADDING, y), price_text, font=font_price)

        if data.change_percent:
            pct_color = self._change_color(data.change_percent)
            pct_text = f"({data.change_percent}%)"
            draw.text((price_bbox[2] + 14, y + 10), pct_text, font=font_pct, fill=pct_color)
        y += 52

        draw.text(
            (self.PADDING, y),
            f"Cập nhật lúc {data.crawled_at:%H:%M:%S %d/%m/%Y}",
            font=font_sub, fill=TEXT_GRAY,
        )
        y += 28

        # ── Detail table ────────────────────────────────────────────────
        table_w = self.WIDTH - 2 * self.PADDING
        col_widths = self._compute_col_widths(table_w, ratios=(0.45, 0.55))

        rows = [
            ("Quy đổi VNĐ", f"~{data.price_vn} đ"),
            ("Vốn hóa thị trường", data.market_cap),
            ("Thanh khoản (24h)", data.liquidity),
            ("Tổng BTC hiện có", f"{data.total_supply} BTC"),
            ("Dao động 1 giờ", f"{data.change_1h}%"),
            ("Dao động 24 giờ", f"{data.change_24h}%"),
            ("Dao động 7 ngày", f"{data.change_7d}%"),
        ]

        def _pct_color(val: str) -> tuple:
            v = val.replace("%", "").strip()
            if v.startswith("-"):
                return RED
            return GREEN

        cell_colors = [
            (TEXT_BLACK, TEXT_BLACK),
            (TEXT_BLACK, TEXT_BLACK),
            (TEXT_BLACK, TEXT_BLACK),
            (TEXT_BLACK, TEXT_BLACK),
            (TEXT_BLACK, _pct_color(data.change_1h)),
            (TEXT_BLACK, _pct_color(data.change_24h)),
            (TEXT_BLACK, _pct_color(data.change_7d)),
        ]

        self._draw_table(
            draw, self.PADDING, y,
            title="Chi tiết Bitcoin",
            headers=["Thông tin", "Giá trị"],
            rows=rows,
            col_widths=col_widths,
            fonts=(font_table_title, font_header, font_cell),
            cell_colors=cell_colors,
        )

        path = self.output_dir / "bitcoin.jpeg"
        img.save(path, "JPEG", quality=100)
        return path
