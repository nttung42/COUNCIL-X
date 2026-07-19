"""Generate the DEMO document set for case REQ-2026-2000 (Màn 1 showcase).

Builds 4 realistic-looking Vietnamese property documents as TEXT-LAYER PDFs
(Times New Roman, full diacritics) whose contents match the seeded Màn-1 data of
case REQ-2026-2000 exactly — so the live demo tells ONE coherent story:

    upload → property_intake extracts the same values the rest of the seeded
    case (Màn 2-5) is built on → every downstream number lines up.

Text-layer PDFs also let the bbox locator (plugins/property_intake/locate.py)
find each value's exact position → the document-viewer overlay highlights real
regions. All personal data below is FICTIONAL (demo prop, not a real record).

Run from ai/:  .venv/Scripts/python.exe scripts/make_demo_docs.py
Output:        samples/demo/*.pdf   (samples/ is gitignored; regenerate anytime)
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

OUT_DIR = Path("samples/demo")
FONT = "C:/Windows/Fonts/times.ttf"
FONT_BOLD = "C:/Windows/Fonts/timesbd.ttf"
FONT_ITALIC = "C:/Windows/Fonts/timesi.ttf"

RED = (0.72, 0.05, 0.05)
BLACK = (0, 0, 0)
GRAY = (0.35, 0.35, 0.35)

# ---- Case facts (== seed of REQ-2026-2000; person/phone are fictional) ----- #
OWNER = "TRẦN ANH TUẤN"
OWNER_TITLE = "Ông TRẦN ANH TUẤN"
CCCD = "079085001234"
PHONE = "0903 123 456"
ADDRESS = "64 Võ Thành I, Phường 12, Quận 10, TP. Hồ Chí Minh"
CERT_NO = "CS 47338124"
PLOT_NO = "82"
MAP_SHEET = "BĐ 45"
LAND_AREA = "199,30 m²"
FLOOR_AREA = "245,20 m²"
LAND_PURPOSE = "Đất ở tại nông thôn (ONT)"
USE_TERM = "Lâu dài"
OWNERSHIP = "Sở hữu riêng"
FLOORS = "3 tầng"
STRUCTURE = "Bê tông cốt thép, tường gạch"
BUILD_YEAR = "2011"
FRONTAGE = "4,90 m"
DIRECTION = "Đông Bắc"
ISSUE_DATE = "25/01/2015"
AUTHORITY = "Sở Tài nguyên và Môi trường TP. Hồ Chí Minh"
MORTGAGE = "Chưa thế chấp tại TCTD nào"


class Sheet:
    """One A4 page with simple top-down line layout helpers."""

    def __init__(self, doc: fitz.Document):
        """Create one A4 page and register the Vietnamese font faces."""
        self.page = doc.new_page(width=595, height=842)
        self.page.insert_font(fontname="vn", fontfile=FONT)
        self.page.insert_font(fontname="vnb", fontfile=FONT_BOLD)
        self.page.insert_font(fontname="vni", fontfile=FONT_ITALIC)
        self.y = 56.0

    def center(self, text: str, *, size=12, bold=False, color=BLACK, dy=16):
        """Draw a horizontally centered line."""
        font = fitz.Font(fontfile=FONT_BOLD if bold else FONT)
        w = font.text_length(text, fontsize=size)
        self.page.insert_text(
            ((595 - w) / 2, self.y),
            text,
            fontsize=size,
            fontname="vnb" if bold else "vn",
            color=color,
        )
        self.y += dy

    def line(self, text: str, *, x=64.0, size=11, bold=False, italic=False, color=BLACK, dy=16):
        """Draw one left-aligned text line."""
        fname = "vnb" if bold else ("vni" if italic else "vn")
        self.page.insert_text((x, self.y), text, fontsize=size, fontname=fname, color=color)
        self.y += dy

    def kv(self, label: str, value: str, *, x=64.0, size=11, dy=17):
        """'- Label: value' with the value in bold (extraction target)."""
        font = fitz.Font(fontfile=FONT)
        prefix = f"{label}: "
        self.page.insert_text((x, self.y), prefix, fontsize=size, fontname="vn")
        px = x + font.text_length(prefix, fontsize=size)
        self.page.insert_text((px, self.y), value, fontsize=size, fontname="vnb")
        self.y += dy

    def rule(self, *, dy=14):
        """Draw a thin horizontal separator."""
        self.page.draw_line(
            fitz.Point(64, self.y - 6), fitz.Point(531, self.y - 6), color=GRAY, width=0.6
        )
        self.y += dy

    def gap(self, dy=10):
        """Advance the cursor by ``dy`` points."""
        self.y += dy

    def national_header(self):
        """Draw the national motto header block."""
        self.center("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", size=12, bold=True, dy=15)
        self.center("Độc lập - Tự do - Hạnh phúc", size=11, dy=12)
        self.center("―――――――――――――", size=9, color=GRAY, dy=22)

    def sign_block(self, right_title: str, name: str, note="(Đã ký và đóng dấu)"):
        """Draw a right-side signature block."""
        x = 340.0
        self.page.insert_text((x, self.y), right_title, fontsize=11, fontname="vnb")
        self.y += 15
        self.page.insert_text((x + 8, self.y), note, fontsize=10, fontname="vni", color=GRAY)
        self.y += 44
        self.page.insert_text((x, self.y), name, fontsize=11, fontname="vnb")
        self.y += 16


def make_gcn() -> fitz.Document:
    """01 — Giấy chứng nhận QSDĐ (sổ đỏ), 2 trang."""
    doc = fitz.open()
    s = Sheet(doc)
    s.national_header()
    s.center("GIẤY CHỨNG NHẬN", size=17, bold=True, color=RED, dy=20)
    s.center("QUYỀN SỬ DỤNG ĐẤT, QUYỀN SỞ HỮU NHÀ Ở", size=13, bold=True, color=RED, dy=16)
    s.center("VÀ TÀI SẢN KHÁC GẮN LIỀN VỚI ĐẤT", size=13, bold=True, color=RED, dy=18)
    s.center(f"Số phát hành: {CERT_NO}", size=11.5, bold=True, dy=15)
    s.center("Số vào sổ cấp GCN: CH 04211", size=10.5, color=GRAY, dy=20)
    s.rule()

    s.line("I. NGƯỜI SỬ DỤNG ĐẤT, CHỦ SỞ HỮU NHÀ Ở VÀ TÀI SẢN GẮN LIỀN VỚI ĐẤT", bold=True)
    s.kv("Ông", f"{OWNER}, sinh năm 1985")
    s.kv("CMND/CCCD số", CCCD)
    s.kv("Địa chỉ thường trú", ADDRESS)
    s.kv("Hình thức sở hữu", OWNERSHIP)
    s.gap()

    s.line("II. THỬA ĐẤT", bold=True)
    s.kv("Thửa đất số", PLOT_NO)
    s.kv("Tờ bản đồ số", MAP_SHEET)
    s.kv("Địa chỉ thửa đất", ADDRESS)
    s.kv("Diện tích", f"{LAND_AREA} (Bằng chữ: Một trăm chín mươi chín phẩy ba mét vuông)")
    s.kv("Hình thức sử dụng", "Sử dụng riêng")
    s.kv("Mục đích sử dụng", LAND_PURPOSE)
    s.kv("Thời hạn sử dụng", USE_TERM)
    s.kv("Mặt tiền tiếp giáp", f"{FRONTAGE}, hướng {DIRECTION}")
    s.gap()

    s.line("III. NHÀ Ở", bold=True)
    s.kv("Loại nhà ở", "Nhà ở riêng lẻ (nhà phố trong hẻm)")
    s.kv("Diện tích xây dựng", "81,70 m²")
    s.kv("Diện tích sàn", FLOOR_AREA)
    s.kv("Kết cấu", STRUCTURE)
    s.kv("Số tầng", FLOORS)
    s.kv("Năm hoàn thành xây dựng", BUILD_YEAR)
    s.gap(16)

    s.line(f"TP. Hồ Chí Minh, ngày {ISSUE_DATE}", x=340, italic=True, dy=15)
    s.sign_block("CƠ QUAN CẤP GIẤY", AUTHORITY.replace("TP. Hồ Chí Minh", "").strip())
    s.line(f"Cơ quan cấp: {AUTHORITY}", size=10, color=GRAY)

    # Trang 2 — sơ đồ + ghi chú biến động
    s2 = Sheet(doc)
    s2.center("SƠ ĐỒ THỬA ĐẤT", size=13, bold=True, dy=24)
    s2.page.draw_rect(fitz.Rect(180, 120, 420, 330), color=BLACK, width=1.0)
    s2.page.insert_text((235, 230), f"Thửa {PLOT_NO} — {LAND_AREA}", fontsize=11, fontname="vnb")
    s2.page.insert_text(
        (252, 345), f"Tỷ lệ 1/500 — Tờ {MAP_SHEET}", fontsize=9.5, fontname="vni", color=GRAY
    )
    s2.y = 400
    s2.line("IV. NHỮNG THAY ĐỔI SAU KHI CẤP GIẤY CHỨNG NHẬN", bold=True)
    s2.kv("Tình trạng thế chấp", MORTGAGE)
    s2.line("Không ghi nhận biến động khác.", italic=True, color=GRAY)
    return doc


def make_lptb() -> fitz.Document:
    """02 — Tờ khai lệ phí trước bạ nhà, đất (Mẫu 01/LPTB)."""
    doc = fitz.open()
    s = Sheet(doc)
    s.national_header()
    s.center("TỜ KHAI LỆ PHÍ TRƯỚC BẠ NHÀ, ĐẤT", size=15, bold=True, dy=18)
    s.center("(Mẫu số 01/LPTB — Ban hành kèm Thông tư 80/2021/TT-BTC)", size=9.5, color=GRAY, dy=20)
    s.rule()
    s.line("A. PHẦN NGƯỜI NỘP THUẾ TỰ KHAI", bold=True)
    s.kv("[01] Họ và tên người nộp", OWNER)
    s.kv("[02] Số CCCD", CCCD)
    s.kv("[03] Điện thoại liên hệ", PHONE)
    s.kv("[04] Địa chỉ", ADDRESS)
    s.gap()
    s.line("B. ĐẶC ĐIỂM NHÀ ĐẤT", bold=True)
    s.kv("[05] Loại tài sản", "Nhà phố (nhà trong hẻm)")
    s.kv("[06] Địa chỉ nhà đất", ADDRESS)
    s.kv("[07] Thửa đất số", f"{PLOT_NO} — Tờ bản đồ số {MAP_SHEET}")
    s.kv("[08] GCN số", f"{CERT_NO}, cấp ngày {ISSUE_DATE}")
    s.kv("[09] Diện tích đất", LAND_AREA)
    s.kv("[10] Diện tích sàn nhà", FLOOR_AREA)
    s.kv("[11] Năm xây dựng", BUILD_YEAR)
    s.gap()
    s.line("C. TRỊ GIÁ TÍNH LỆ PHÍ TRƯỚC BẠ", bold=True)
    s.kv("[12] Trị giá nhà, đất tự khai", "8.450.000.000 đồng")
    s.kv("[13] Mức thu lệ phí trước bạ", "0,5%")
    s.kv("[14] Số tiền lệ phí trước bạ", "42.250.000 đồng")
    s.gap(18)
    s.line(
        "Tôi cam đoan số liệu khai trên là đúng và chịu trách nhiệm trước pháp luật.",
        italic=True,
        size=10,
    )
    s.gap(6)
    s.line("TP. Hồ Chí Minh, ngày 03/02/2015", x=340, italic=True, dy=15)
    s.sign_block("NGƯỜI NỘP THUẾ", OWNER, note="(Đã ký)")
    return doc


def make_ban_giao() -> fitz.Document:
    """03 — Biên bản bàn giao nhà và đất."""
    doc = fitz.open()
    s = Sheet(doc)
    s.national_header()
    s.center("BIÊN BẢN BÀN GIAO NHÀ Ở VÀ ĐẤT Ở", size=15, bold=True, dy=20)
    s.line(f"Hôm nay, ngày 10/02/2015, tại {ADDRESS}, chúng tôi gồm:", size=11, dy=18)
    s.line("BÊN GIAO (Bên A):", bold=True)
    s.kv("Ông", "NGUYỄN VĂN HÒA")
    s.kv("CCCD số", "079062004567")
    s.gap(4)
    s.line("BÊN NHẬN (Bên B):", bold=True)
    s.kv("Ông", OWNER)
    s.kv("CCCD số", CCCD)
    s.kv("Điện thoại", PHONE)
    s.kv("Quan hệ với tài sản", "Chủ sở hữu (nhận chuyển nhượng)")
    s.gap()
    s.line("NỘI DUNG BÀN GIAO", bold=True)
    s.kv("Tài sản bàn giao", f"Toàn bộ nhà và đất tại {ADDRESS}")
    s.kv("Loại tài sản", "Nhà phố (nhà trong hẻm)")
    s.kv("Theo GCN số", f"{CERT_NO} (thửa {PLOT_NO}, tờ {MAP_SHEET})")
    s.kv("Diện tích đất", LAND_AREA)
    s.kv("Diện tích sàn xây dựng", FLOOR_AREA)
    s.kv("Số tầng", FLOORS)
    s.kv("Kết cấu công trình", STRUCTURE)
    s.kv("Năm xây dựng", BUILD_YEAR)
    s.kv("Mặt tiền", f"{FRONTAGE} — hướng nhà {DIRECTION}")
    s.kv("Tình trạng sử dụng", "Đang để ở, không tranh chấp, không cho thuê")
    s.gap()
    s.line("Hai bên xác nhận tài sản được bàn giao nguyên trạng, kèm toàn bộ", size=10.5, dy=14)
    s.line(
        "giấy tờ pháp lý liên quan. Biên bản lập thành 02 bản, mỗi bên giữ 01 bản.",
        size=10.5,
        dy=20,
    )
    x_save = s.y
    s.page.insert_text((90, x_save), "ĐẠI DIỆN BÊN GIAO", fontsize=11, fontname="vnb")
    s.page.insert_text((96, x_save + 58), "NGUYỄN VĂN HÒA", fontsize=11, fontname="vnb")
    s.page.insert_text((360, x_save), "ĐẠI DIỆN BÊN NHẬN", fontsize=11, fontname="vnb")
    s.page.insert_text((372, x_save + 58), OWNER, fontsize=11, fontname="vnb")
    return doc


def make_thue_dat() -> fitz.Document:
    """04 — Thông báo nộp thuế sử dụng đất phi nông nghiệp."""
    doc = fitz.open()
    s = Sheet(doc)
    s.line("CỤC THUẾ TP. HỒ CHÍ MINH", bold=True, size=10.5, dy=13)
    s.line("CHI CỤC THUẾ QUẬN 10", bold=True, size=10.5, dy=13)
    s.line("Số: 2618/TB-CCT", size=9.5, color=GRAY, dy=6)
    s.y = 56
    s.center("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", size=11.5, bold=True, dy=14)
    s.center("Độc lập - Tự do - Hạnh phúc", size=10.5, dy=26)
    s.center("THÔNG BÁO NỘP THUẾ SỬ DỤNG ĐẤT PHI NÔNG NGHIỆP", size=13.5, bold=True, dy=16)
    s.center("Kỳ tính thuế: năm 2025", size=10.5, color=GRAY, dy=20)
    s.rule()
    s.kv("Người nộp thuế", OWNER)
    s.kv("Mã số thuế cá nhân", "8412907531")
    s.kv("CCCD số", CCCD)
    s.kv("Địa chỉ nhận thông báo", ADDRESS)
    s.gap()
    s.line("THÔNG TIN THỬA ĐẤT CHỊU THUẾ", bold=True)
    s.kv("Địa chỉ thửa đất", ADDRESS)
    s.kv("Thửa đất số", f"{PLOT_NO} — Tờ bản đồ số {MAP_SHEET}")
    s.kv("Diện tích đất tính thuế", LAND_AREA)
    s.kv("Mục đích sử dụng", LAND_PURPOSE)
    s.kv("GCN số", CERT_NO)
    s.gap()
    s.line("SỐ THUẾ PHẢI NỘP", bold=True)
    s.kv("Giá 1 m² đất tính thuế", "9.800.000 đồng/m²")
    s.kv("Thuế suất", "0,03%")
    s.kv("Số thuế phải nộp năm 2025", "585.941 đồng")
    s.kv("Hạn nộp", "31/10/2025")
    s.gap(18)
    s.line("TP. Hồ Chí Minh, ngày 15/08/2025", x=340, italic=True, dy=15)
    s.sign_block("CHI CỤC TRƯỞNG", "LÊ MINH CHÂU")
    return doc


def main() -> None:
    """Generate all 4 demo PDFs into samples/demo/."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "01_GCN_QSDD_CS47338124.pdf": make_gcn(),
        "02_To_khai_LPTB.pdf": make_lptb(),
        "03_Bien_ban_ban_giao.pdf": make_ban_giao(),
        "04_Thong_bao_thue_dat_2025.pdf": make_thue_dat(),
    }
    for name, doc in outputs.items():
        path = OUT_DIR / name
        doc.save(path)
        print(f"  wrote {path}  ({doc.page_count} trang)")
        doc.close()
    print("Done — bộ hồ sơ demo khớp case REQ-2026-2000 (dữ liệu cá nhân là hư cấu).")


if __name__ == "__main__":
    main()
