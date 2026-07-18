"""Shared fixtures for property_intake tests: 4 sample documents + fakes.

Not collected by pytest (leading underscore). Provides realistic offline stand-ins
so the whole pipeline can run without a real LLM:

* ``SAMPLE_TEXTS`` — one text body per DocType. Each carries an ASCII token
  ``DOCTYPE_<NAME>`` so a deterministic fake classifier can route it (avoids
  relying on Vietnamese diacritics surviving the PDF font round-trip).
* ``SAMPLE_EXTRACTIONS`` — the structured object each extractor "would" return,
  keyed by extraction schema. Values are grounded in their snippets.
* ``_SchemaRoutedChat`` — a fake chat model returning the right object per schema.
"""

from __future__ import annotations

import fitz  # PyMuPDF

from shb.ai.plugins.property_intake.schema import (
    BienBanBanGiaoExtraction,
    DocType,
    ExtractedField,
    FieldVerification,
    SoHongExtraction,
    ThongBaoThueDatExtraction,
    ToKhaiLPTBExtraction,
    VerificationResult,
)


def _ef(value: str, snippet: str, confidence: float = 0.92) -> ExtractedField:
    return ExtractedField(value=value, snippet=snippet, confidence=confidence)


# --------------------------------------------------------------------------- #
# Sample document texts (ASCII + a routing token, > scan threshold)
# --------------------------------------------------------------------------- #
SAMPLE_TEXTS: dict[DocType, str] = {
    DocType.SO_DO_SO_HONG: (
        "DOCTYPE_SO_DO_SO_HONG GIAY CHUNG NHAN QUYEN SU DUNG DAT "
        "So phat hanh CS 01234567 - Nguoi su dung dat: Nguyen Van A - "
        "Dia chi: 123 Le Loi - Dien tich: 62 m2 - Mat tien 4m sau 15m"
    ),
    DocType.TO_KHAI_LPTB: (
        "DOCTYPE_TO_KHAI_LPTB TO KHAI LE PHI TRUOC BA NHA DAT "
        "Nguoi nop: Nguyen Van A - Dia chi: 123 Le Loi - Dien tich 62 m2 - Nha pho"
    ),
    DocType.BIEN_BAN_BAN_GIAO: (
        "DOCTYPE_BIEN_BAN_BAN_GIAO BIEN BAN BAN GIAO NHA O "
        "Ben nhan: Nguyen Van A - Dia chi 123 Le Loi - Hien trang: da hoan thien"
    ),
    DocType.THONG_BAO_THUE_DAT: (
        "DOCTYPE_THONG_BAO_THUE_DAT THONG BAO NOP THUE SU DUNG DAT "
        "Nguoi nop thue: Nguyen Van A - Dien tich dat: 80 m2 - Muc dich: Dat o do thi"
    ),
}


# --------------------------------------------------------------------------- #
# Sample extractions (what each mocked extractor returns), grounded snippets.
# Designed so cross-document merge yields:
#   - owner_full_name: agreed by all 4 docs -> corroborated, da_xac_thuc
#   - land_area_sqm: GCN/tờ khai = 62 but thông báo thuế = 80 -> mau_thuan (62 wins)
# --------------------------------------------------------------------------- #
SAMPLE_EXTRACTIONS: dict[type, object] = {
    SoHongExtraction: SoHongExtraction(
        owner_full_name=_ef("Nguyễn Văn A", "Người sử dụng đất: Nguyễn Văn A", 0.96),
        certificate_number=_ef("CS 01234567", "Số phát hành: CS 01234567", 0.95),
        address=_ef("123 Lê Lợi", "Địa chỉ: 123 Lê Lợi", 0.9),
        land_area_sqm=_ef("62", "Diện tích: 62 m2", 0.9),
        frontage_m=_ef("4", "Mặt tiền: 4 m", 0.85),
        depth_m=_ef("15", "Chiều sâu: 15 m", 0.85),
        issue_date=_ef("15/03/2020", "Cấp ngày 15/03/2020", 0.9),
    ),
    ToKhaiLPTBExtraction: ToKhaiLPTBExtraction(
        owner_full_name=_ef("Nguyễn Văn A", "Người nộp: Nguyễn Văn A", 0.9),
        address=_ef("123 Lê Lợi", "Địa chỉ: 123 Lê Lợi", 0.88),
        land_area_sqm=_ef("62", "Diện tích 62 m2", 0.88),
        property_type=_ef("Nhà phố", "Loại: Nhà phố", 0.8),
    ),
    BienBanBanGiaoExtraction: BienBanBanGiaoExtraction(
        owner_full_name=_ef("Nguyễn Văn A", "Bên nhận: Nguyễn Văn A", 0.88),
        address=_ef("123 Lê Lợi", "Địa chỉ 123 Lê Lợi", 0.85),
        current_usage_status=_ef("Đã hoàn thiện", "Hiện trạng: Đã hoàn thiện", 0.82),
    ),
    ThongBaoThueDatExtraction: ThongBaoThueDatExtraction(
        owner_full_name=_ef("Nguyễn Văn A", "Người nộp thuế: Nguyễn Văn A", 0.9),
        land_area_sqm=_ef("80", "Diện tích đất: 80 m2", 0.9),  # conflicts with 62
        land_use_purpose=_ef("Đất ở tại đô thị", "Mục đích: Đất ở tại đô thị", 0.88),
    ),
}


def all_supported(n: int = 64) -> VerificationResult:
    """Build a verifier verdict that passes every candidate index."""
    return VerificationResult(checks=[FieldVerification(index=i, supported=True) for i in range(n)])


class _FakeStructured:
    def __init__(self, result):
        self._result = result

    async def ainvoke(self, _messages):
        return self._result


class _SchemaRoutedChat:
    """Fake chat returning the object registered for the requested output schema."""

    def __init__(self, by_schema: dict[type, object]):
        self._by_schema = by_schema

    def with_structured_output(self, schema):
        if schema not in self._by_schema:
            raise AssertionError(f"No fake result registered for schema {schema!r}")
        return _FakeStructured(self._by_schema[schema])


def extraction_router() -> _SchemaRoutedChat:
    """Fake chat covering all 4 extractors + the verifier."""
    by_schema = dict(SAMPLE_EXTRACTIONS)
    by_schema[VerificationResult] = all_supported()
    return _SchemaRoutedChat(by_schema)


def classify_by_token(text: str) -> DocType:
    """Deterministic classifier: route by the ASCII DOCTYPE_ token in the text."""
    for doc_type in DocType:
        if f"DOCTYPE_{doc_type.name}" in text:
            return doc_type
    return DocType.KHAC


def text_pdf(text: str) -> bytes:
    """Render text into a minimal one-page PDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


class _FakeFile:
    def __init__(self, name, path, content_type):
        self.original_name = name
        self.stored_path = path
        self.content_type = content_type


class _FakeStorage:
    """In-memory StorageService stand-in (get_file / read_file)."""

    def __init__(self):
        self._files: dict = {}
        self._blobs: dict = {}

    def add(self, file_id, name, content_type, data):
        path = f"/mem/{file_id}"
        self._files[file_id] = _FakeFile(name, path, content_type)
        self._blobs[path] = data

    async def get_file(self, file_id):
        return self._files.get(file_id)

    async def read_file(self, path):
        return self._blobs[path]


def storage_with_all_samples() -> tuple[_FakeStorage, list[str]]:
    """Build a storage holding the 4 sample docs; return (storage, file_ids)."""
    storage = _FakeStorage()
    file_ids: list[str] = []
    naming = {
        DocType.SO_DO_SO_HONG: "so-hong.pdf",
        DocType.TO_KHAI_LPTB: "to-khai-lptb.pdf",
        DocType.BIEN_BAN_BAN_GIAO: "bien-ban-ban-giao.pdf",
        DocType.THONG_BAO_THUE_DAT: "thong-bao-thue-dat.pdf",
    }
    for doc_type, text in SAMPLE_TEXTS.items():
        file_id = doc_type.value  # stable, human-readable file id
        storage.add(file_id, naming[doc_type], "application/pdf", text_pdf(text))
        file_ids.append(file_id)
    return storage, file_ids
