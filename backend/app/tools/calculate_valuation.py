"""calculate_valuation — Valuation Engine của PAA (SHB_ThamDinhBDS_DesignDoc_2.md §4.2).

Định giá bất động sản bằng cách BLEND 3 phương pháp thẩm định giá phổ biến trong
nghiệp vụ ngân hàng, mỗi phương pháp có trọng số, trả về ``ValuationResult`` đúng
schema ``specs/001-property-appraisal-agent/data-model.md §6``:

1. So sánh trực tiếp (Sales Comparison) — trọng số chính.
2. Hồi quy hedonic (ML-assisted, MVP dùng heuristic — xem docstring hàm).
3. Chi phí xây dựng (Cost Approach) — bổ trợ.

--------------------------------------------------------------------------------
HỢP ĐỒNG INPUT/OUTPUT (để Orchestrator wiring — Nguyên tắc IV)
--------------------------------------------------------------------------------
Hàm này KHÔNG tự gọi lookup tool. Orchestrator/Valuation Agent truyền vào:

- ``subject_property`` : dict theo ``data-model.md §1`` (``PropertyAppraisalRequest
  .subject_property``). Bắt buộc ``area_m2`` (> 0) và ``property_type``. Các field
  ``frontage_m``, ``alley_width_m``, ``floors`` là tuỳ chọn (lấy từ hồ sơ tài sản
  của thẩm định viên) — nếu thiếu, các điều chỉnh tương ứng bị bỏ qua (neutral).

- ``comparables`` : list ``ComparableTransaction`` (``data-model.md §2``) — chính là
  ``market_price_lookup(...)["data"]["comparables"]``. Mỗi phần tử ĐÃ được
  ``market_price_lookup`` quy đổi giá theo thời gian và có thêm field
  ``adjusted_price_per_m2`` / ``adjusted_price_total`` / ``time_adjustment_factor``.
  Nếu field ``adjusted_price_per_m2`` không có, engine fallback sang
  ``price_per_m2`` (và tự quy đổi nếu ``price_index`` được truyền).

- ``price_index`` : ``PriceIndexSeries`` (``data-model.md §3``, tuỳ chọn) — chỉ dùng
  khi comparables CHƯA được quy đổi sẵn. Không truyền vẫn chạy được.

- ``current_period`` : str, vd ``"2026-Q2"`` (tuỳ chọn) — kỳ quy đổi hiện tại; nếu
  thiếu, lấy kỳ mới nhất trong ``price_index`` hoặc từ chính comparables.

- ``amenities`` : list ``{type, name, distance_m}`` (tuỳ chọn) — từ
  ``neighborhood_amenity_lookup(...)["data"]["amenities"]``; là feature của mô hình
  hedonic. Thiếu -> hedonic dùng premium trung tính.

Trả về ``dict`` khớp ``ValuationResult`` (data-model.md §6). Dùng ``dict`` thuần
(không phụ thuộc pydantic) để orchestrator serialize JSON trực tiếp.

TypedDict bên dưới CHỈ để type-hint/IDE; runtime nhận ``dict`` thường cũng chạy.
"""

from __future__ import annotations

import re
import statistics
from typing import List, Optional, Sequence, TypedDict

# --------------------------------------------------------------------------- #
# Type hints tham chiếu data-model.md (không định nghĩa lại toàn bộ entity khác)
# --------------------------------------------------------------------------- #


class SubjectProperty(TypedDict, total=False):
    address: str
    lat: float
    long: float
    area_m2: float                 # bắt buộc, > 0
    property_type: str             # nha_pho | dat_nen | chung_cu | bds_thuong_mai
    legal_status_claimed: str      # so_hong | so_do | giay_tay | khac
    frontage_m: float              # tuỳ chọn
    alley_width_m: Optional[float]  # tuỳ chọn; None = mặt tiền đường lớn
    floors: int                    # tuỳ chọn


class ComparableTransaction(TypedDict, total=False):
    transaction_id: str
    area_m2: float
    frontage_m: float
    alley_width_m: Optional[float]
    floors: int
    legal_status: str
    transaction_type: str          # sold | listed
    price_total: int
    price_per_m2: int
    adjusted_price_per_m2: int      # do market_price_lookup thêm (đã quy đổi thời gian)
    adjusted_price_total: int
    transaction_date: str
    transaction_period: str         # YYYY-Qn
    distance_from_subject_km: float
    confidence: float


class ValueRange(TypedDict):
    low: int
    high: int


class MethodologyBreakdown(TypedDict):
    comparable_approach: int
    hedonic_model: int
    cost_approach: int


class ValuationResult(TypedDict):
    estimated_value: int
    value_range: ValueRange
    value_per_m2: int
    confidence_score: float
    methodology_breakdown: MethodologyBreakdown
    comparables_used: int
    time_adjustment_index_period: Optional[str]
    adjustment_notes: List[str]


# --------------------------------------------------------------------------- #
# Hệ số điều chỉnh tham chiếu (design doc §4.2 + ví dụ mục 4.2).
# Các con số là heuristic hợp lý cho MVP hackathon — ghi rõ nguồn gốc để
# thẩm định viên hiệu chỉnh (explainability, Nguyên tắc II).
# --------------------------------------------------------------------------- #

# Trọng số blend mặc định 3 phương pháp.
DEFAULT_BLEND_WEIGHTS = {"comparable": 0.50, "hedonic": 0.30, "cost": 0.20}
# Khi ít comparable (<3), so sánh trực tiếp kém tin cậy -> dồn trọng số sang cost.
LOW_DATA_BLEND_WEIGHTS = {"comparable": 0.30, "hedonic": 0.30, "cost": 0.40}
LOW_DATA_COMPARABLE_THRESHOLD = 3

# Điều chỉnh diện tích (economies of scale): căn nhỏ hơn -> giá/m² cao hơn.
AREA_ELASTICITY = 0.10          # 10% chênh diện tích -> ~1% chênh giá/m²
AREA_ADJ_CAP = 0.10             # cap ±10%

# Điều chỉnh tiếp cận (hẻm/mặt tiền). Tham chiếu ví dụ design doc:
# "trừ 4% do hẻm 2.5m" (so với hẻm chuẩn 4.0m: (4.0-2.5)*0.025 ≈ 3.75% ~ 4%).
ALLEY_REF_M = 4.0
ALLEY_PENALTY_PER_M = 0.025     # 2.5%/m hẹp hơn hẻm chuẩn
MAIN_ROAD_PREMIUM = 0.06        # mặt tiền đường lớn (alley_width None): +6%
ACCESS_ADJ_CAP = 0.12

# Điều chỉnh pháp lý: quy giá comparable về mặt bằng pháp lý của subject.
# so_hong là chuẩn tham chiếu (1.0); giấy tờ yếu hơn giao dịch ở giá thấp hơn.
LEGAL_VALUE_FACTOR = {
    "so_hong": 1.00,
    "so_do": 0.93,
    "giay_tay": 0.85,
    "khac": 0.88,
}

# Tin rao bán (listed) là GIÁ CHÀO, thường cao hơn giá chốt thực -> haircut + giảm trọng số.
LISTED_HAIRCUT = 0.95
LISTED_WEIGHT_FACTOR = 0.5

# Thận trọng tài sản bảo đảm: comparable cao hơn trung vị khu vực > 12% bị giảm
# trọng số còn 35% (giá thu hồi thực tế thường thấp hơn giá đỉnh/căn đặc biệt).
HIGH_SIDE_TOL = 0.12
HIGH_SIDE_WEIGHT_FACTOR = 0.35

# Cost approach: đơn giá xây dựng (VND/m² sàn) + tỷ trọng đất theo loại tài sản.
CONSTRUCTION_UNIT_COST = {
    "nha_pho": 10_000_000,
    "dat_nen": 0,               # đất nền: gần như không có giá trị công trình
    "chung_cu": 12_000_000,
    "bds_thuong_mai": 12_000_000,
}
LAND_FRACTION = {               # phần giá trị đất trong giá comparable/m²
    "nha_pho": 0.68,
    "dat_nen": 0.95,
    "chung_cu": 0.15,           # chung cư: giá gần như toàn phần công trình/căn
    "bds_thuong_mai": 0.55,
}
DEFAULT_FLOORS = {"nha_pho": 3, "dat_nen": 0, "chung_cu": 1, "bds_thuong_mai": 3}
DEPRECIATION_FACTOR = 0.85      # hệ số còn lại (tuổi công trình không rõ -> mặc định)

# Confidence & value_range.
CONF_BASE = 0.30
CONF_PER_COMP = 0.08
CONF_MAX = 0.95
CONF_ZERO_COMP_CAP = 0.35       # comparables_used == 0 -> confidence < 0.4 (SC-005)
CONF_FLOOR = 0.20
METHOD_DISPERSION_TOL = 0.15    # lệch giữa 3 phương pháp > 15% -> giảm confidence
COMP_CV_TOL = 0.08              # biến thiên giá comparable > 8% -> giảm confidence dần
SPREAD_BASE = 0.05
SPREAD_CONF_COEF = 0.15

NO_COMPARABLE_NOTE = (
    "Không đủ dữ liệu so sánh, cần thẩm định viên bổ sung — định giá dựa chủ yếu "
    "vào phương pháp chi phí, độ tin cậy thấp."
)


# --------------------------------------------------------------------------- #
# Hàm chính
# --------------------------------------------------------------------------- #
def calculate_valuation(
    subject_property: SubjectProperty,
    comparables: Optional[Sequence[ComparableTransaction]] = None,
    price_index: Optional[dict] = None,
    current_period: Optional[str] = None,
    amenities: Optional[Sequence[dict]] = None,
) -> ValuationResult:
    """Định giá 1 tài sản bằng blend 3 phương pháp; trả ``ValuationResult`` (§6).

    Xem docstring module cho hợp đồng input/output đầy đủ. Không raise khi thiếu
    dữ liệu: giảm/dồn trọng số phương pháp thiếu và ghi chú vào ``adjustment_notes``
    (Error Handling trong agent spec).
    """
    comparables = list(comparables or [])
    notes: List[str] = []

    area = _pos_float(subject_property.get("area_m2"))
    prop_type = subject_property.get("property_type") or "nha_pho"
    if area is None:
        # Không có diện tích -> không thể quy ra tổng giá trị. Trả kết quả rỗng an toàn.
        notes.append("Thiếu area_m2 hợp lệ của tài sản — không thể định giá, cần bổ sung.")
        return _empty_result(notes)

    period = current_period or _resolve_period(comparables, price_index)

    # --- 1. Chuẩn hoá từng comparable về "giá/m² tương đương subject" ---------
    adj_records = []
    for c in comparables:
        rec = _normalize_comparable(c, subject_property, prop_type, price_index, period, notes)
        if rec is not None:
            adj_records.append(rec)

    comparables_used = len(adj_records)

    # --- 2. Ba phương pháp ---------------------------------------------------
    comparable_ppm2 = _comparable_approach(adj_records)
    equal_median_ppm2 = (
        statistics.median([r["adj_ppm2"] for r in adj_records]) if adj_records else None
    )
    hedonic_ppm2 = _hedonic_approach(equal_median_ppm2, subject_property, amenities, notes)
    cost_value = _cost_approach(
        comparable_ppm2 or equal_median_ppm2, subject_property, prop_type, area, notes
    )

    comparable_value = int(round(comparable_ppm2 * area)) if comparable_ppm2 else None
    hedonic_value = int(round(hedonic_ppm2 * area)) if hedonic_ppm2 else None

    # --- 3. Blend ------------------------------------------------------------
    estimated_value, weights_used = _blend(
        comparable_value, hedonic_value, cost_value, comparables_used, notes
    )
    if estimated_value is None:
        notes.append("Không có phương pháp nào đủ dữ liệu để định giá — cần thẩm định viên xử lý thủ công.")
        return _empty_result(notes)

    value_per_m2 = int(round(estimated_value / area))

    # --- 4. Confidence & value_range ----------------------------------------
    method_values = [v for v in (comparable_value, hedonic_value, cost_value) if v]
    comp_cv = _coefficient_of_variation([r["adj_ppm2"] for r in adj_records])
    confidence = _confidence_score(comparables_used, estimated_value, method_values, comp_cv, notes)
    low, high = _value_range(estimated_value, confidence)

    if period:
        notes.insert(0, f"Giá comparable quy đổi theo chỉ số khu vực về kỳ {period}.")

    return {
        "estimated_value": int(estimated_value),
        "value_range": {"low": int(low), "high": int(high)},
        "value_per_m2": value_per_m2,
        "confidence_score": round(confidence, 3),
        "methodology_breakdown": {
            "comparable_approach": int(comparable_value) if comparable_value else 0,
            "hedonic_model": int(hedonic_value) if hedonic_value else 0,
            "cost_approach": int(cost_value) if cost_value else 0,
        },
        "comparables_used": comparables_used,
        "time_adjustment_index_period": period,
        "adjustment_notes": notes,
    }


# --------------------------------------------------------------------------- #
# 1. So sánh trực tiếp
# --------------------------------------------------------------------------- #
def _normalize_comparable(
    c: dict,
    subject: dict,
    prop_type: str,
    price_index: Optional[dict],
    period: Optional[str],
    notes: List[str],
) -> Optional[dict]:
    """Quy 1 comparable về giá/m² tương đương đặc điểm subject + trọng số.

    Trả ``{"adj_ppm2", "weight", "listed"}`` hoặc ``None`` nếu comparable không
    dùng được (thiếu giá / khác loại tài sản).
    """
    if prop_type and c.get("property_type") and c.get("property_type") != prop_type:
        return None

    # (a) giá/m² gốc: ưu tiên giá đã quy đổi thời gian từ market_price_lookup.
    ppm2 = c.get("adjusted_price_per_m2") or c.get("price_per_m2")
    if not ppm2 and c.get("price_total") and c.get("area_m2"):
        ppm2 = c["price_total"] / c["area_m2"]
    ppm2 = _pos_float(ppm2)
    if ppm2 is None:
        return None

    # (b) nếu comparable CHƯA quy đổi thời gian mà ta có price_index -> tự quy đổi.
    if "adjusted_price_per_m2" not in c and price_index and period:
        factor = _time_factor(price_index, c.get("transaction_period")
                              or _period_from_date(c.get("transaction_date")), period)
        if factor:
            ppm2 *= factor

    adj = float(ppm2)

    # (c) điều chỉnh diện tích (economies of scale).
    c_area = _pos_float(c.get("area_m2"))
    s_area = _pos_float(subject.get("area_m2"))
    if c_area and s_area:
        area_adj = _clamp(AREA_ELASTICITY * (c_area - s_area) / s_area, -AREA_ADJ_CAP, AREA_ADJ_CAP)
        adj *= (1 + area_adj)

    # (d) điều chỉnh tiếp cận (hẻm/mặt tiền) — chỉ khi biết tình trạng của subject.
    if "alley_width_m" in subject:
        subj_prem = _access_premium(subject.get("alley_width_m"))
        comp_prem = _access_premium(c.get("alley_width_m"))
        access_adj = _clamp(subj_prem - comp_prem, -ACCESS_ADJ_CAP, ACCESS_ADJ_CAP)
        adj *= (1 + access_adj)

    # (e) điều chỉnh pháp lý: quy về mặt bằng pháp lý subject (mặc định so_hong).
    subj_legal = subject.get("legal_status_claimed", "so_hong")
    comp_legal = c.get("legal_status", subj_legal)
    sf = LEGAL_VALUE_FACTOR.get(subj_legal, 1.0)
    cf = LEGAL_VALUE_FACTOR.get(comp_legal, 1.0)
    if cf:
        adj *= (sf / cf)

    # (f) tin rao bán: haircut.
    listed = c.get("transaction_type") == "listed"
    if listed:
        adj *= LISTED_HAIRCUT

    # trọng số: giao dịch gần hơn & confidence cao hơn ảnh hưởng nhiều hơn.
    dist = _pos_float(c.get("distance_from_subject_km"))
    conf = c.get("confidence")
    conf = float(conf) if isinstance(conf, (int, float)) else 0.7
    weight = conf / ((dist if dist is not None else 1.0) + 0.3)
    if listed:
        weight *= LISTED_WEIGHT_FACTOR

    return {"adj_ppm2": adj, "weight": weight, "listed": listed}


def _comparable_approach(records: List[dict]) -> Optional[float]:
    """Giá/m² so sánh = **trung vị có trọng số** (weighted median) của giá đã điều chỉnh.

    Dùng trung vị (thay vì trung bình) để bền vững với các comparable ngoại lai —
    dữ liệu BĐS thực tế phân tán mạnh (nhà cùng khu chênh 30-40%). Trọng số =
    confidence / (khoảng_cách + 0.3), ưu tiên giao dịch gần & tin cậy hơn.

    THẬN TRỌNG TÀI SẢN BẢO ĐẢM (conservative collateral): các giao dịch có giá
    vượt xa trung vị khu vực (căn góc, cải tạo đặc biệt, giá chào cao) ít đại diện
    cho giá thu hồi thực tế -> giảm mạnh trọng số (bất đối xứng, thiên về giá trị
    thanh lý an toàn cho ngân hàng). Đây là posture định giá thận trọng chuẩn mực,
    không phải loại bỏ dữ liệu.
    """
    if not records:
        return None
    values = [r["adj_ppm2"] for r in records]
    med = statistics.median(values)
    weights = []
    for r in records:
        w = r["weight"]
        if r["adj_ppm2"] > med * (1 + HIGH_SIDE_TOL):
            w *= HIGH_SIDE_WEIGHT_FACTOR
        weights.append(w)
    return _weighted_median(values, weights)


# --------------------------------------------------------------------------- #
# 2. Hedonic (heuristic MVP)
# --------------------------------------------------------------------------- #
def _hedonic_approach(
    base_ppm2: Optional[float],
    subject: dict,
    amenities: Optional[Sequence[dict]],
    notes: List[str],
) -> Optional[float]:
    """Xấp xỉ hedonic cho MVP (KHÔNG train ML thật — hackathon).

    Design doc §4.2 mô tả mô hình hồi quy trên feature {vị trí, diện tích, mặt
    tiền, tuổi nhà, mật độ tiện ích, stigma}. Ở đây dùng heuristic:

        hedonic_ppm2 = base_ppm2 × (1 + feature_premium)

    với ``base_ppm2`` = trung vị (không trọng số) của các comparable đã điều chỉnh
    (ước lượng trung tâm bền vững, làm mượt/kiểm chứng chéo phương pháp so sánh),
    ``feature_premium`` = tổng điều chỉnh nhỏ theo tiện ích + khả năng tiếp cận của
    subject. Đây là proxy minh bạch thay cho hệ số hồi quy — thẩm định viên có thể
    thay bằng model thật sau (adapter pattern, Nguyên tắc VI).
    """
    if not base_ppm2:
        return None

    premium = 0.0
    reasons = []

    # (a) tiện ích lân cận (từ neighborhood_amenity_lookup).
    if amenities:
        near = [a for a in amenities if _pos_float(a.get("distance_m")) is not None
                and a["distance_m"] <= 500]
        premium += min(0.05, 0.012 * len(near))
        if any(a.get("type") == "school" and a.get("distance_m", 9999) <= 500 for a in amenities):
            premium += 0.02
            reasons.append("cộng ~3% do gần trường học")
        if near:
            reasons.append(f"cộng ~{min(5, len(near))}% do {len(near)} tiện ích trong 500m")

    # (b) khả năng tiếp cận của subject.
    if "alley_width_m" in subject:
        acc = _access_premium(subject.get("alley_width_m"))
        premium += acc
        if acc < 0:
            reasons.append(f"trừ ~{abs(round(acc * 100))}% do hẻm hẹp {subject.get('alley_width_m')}m")
        elif acc > 0:
            reasons.append("cộng ~6% do mặt tiền đường lớn")

    premium = _clamp(premium, -0.08, 0.08)
    if reasons:
        notes.append("Hedonic: " + "; ".join(reasons) + " (heuristic thay ML).")
    return base_ppm2 * (1 + premium)


# --------------------------------------------------------------------------- #
# 3. Chi phí xây dựng
# --------------------------------------------------------------------------- #
def _cost_approach(
    base_ppm2: Optional[float],
    subject: dict,
    prop_type: str,
    area: float,
    notes: List[str],
) -> Optional[int]:
    """Giá trị đất (theo so sánh) + giá trị công trình còn lại (design doc §4.2).

        cost = land_ppm2 × diện_tích + đơn_giá_xây × diện_tích_sàn × khấu_hao

    ``land_ppm2`` = ``base_ppm2 × LAND_FRACTION[loại]`` (tách phần đất khỏi giá
    comparable đã gồm cả công trình). Thiếu ``base_ppm2`` (không có comparable) ->
    chỉ còn phần công trình, cost approach kém tin cậy; vẫn trả để blend dựa vào.
    """
    unit_cost = CONSTRUCTION_UNIT_COST.get(prop_type, CONSTRUCTION_UNIT_COST["nha_pho"])
    land_fraction = LAND_FRACTION.get(prop_type, LAND_FRACTION["nha_pho"])
    floors = subject.get("floors")
    if not isinstance(floors, int) or floors < 0:
        floors = DEFAULT_FLOORS.get(prop_type, 1)

    land_value = 0.0
    if base_ppm2:
        land_value = base_ppm2 * land_fraction * area
    else:
        notes.append("Cost approach: thiếu comparable để ước lượng giá đất — chỉ tính phần công trình.")

    floor_area = area * max(1, floors) if unit_cost else 0
    construction_value = unit_cost * floor_area * DEPRECIATION_FACTOR

    total = land_value + construction_value
    if total <= 0:
        return None
    notes.append(
        f"Cost approach: đất ~{_billions(land_value)} tỷ + xây dựng "
        f"{floors} tầng ×{unit_cost // 1_000_000}tr/m² ×{DEPRECIATION_FACTOR} khấu hao "
        f"~{_billions(construction_value)} tỷ."
    )
    return int(round(total))


# --------------------------------------------------------------------------- #
# Blend + confidence + range
# --------------------------------------------------------------------------- #
def _blend(
    comparable_value: Optional[int],
    hedonic_value: Optional[int],
    cost_value: Optional[int],
    comparables_used: int,
    notes: List[str],
) -> tuple:
    """Blend 3 phương pháp theo trọng số; bỏ qua & tái chuẩn hoá phương pháp thiếu."""
    base = (
        LOW_DATA_BLEND_WEIGHTS
        if comparables_used < LOW_DATA_COMPARABLE_THRESHOLD
        else DEFAULT_BLEND_WEIGHTS
    )
    if comparables_used < LOW_DATA_COMPARABLE_THRESHOLD:
        notes.append(
            f"Chỉ có {comparables_used} comparable (<{LOW_DATA_COMPARABLE_THRESHOLD}) — "
            "giảm trọng số so sánh trực tiếp, tăng trọng số chi phí."
        )

    parts = {
        "comparable": comparable_value,
        "hedonic": hedonic_value,
        "cost": cost_value,
    }
    active = {k: v for k, v in parts.items() if v}
    if not active:
        return None, {}

    total_w = sum(base[k] for k in active)
    weights = {k: base[k] / total_w for k in active}
    est = sum(active[k] * weights[k] for k in active)

    missing = [k for k, v in parts.items() if not v]
    if missing:
        notes.append("Thiếu dữ liệu cho phương pháp: " + ", ".join(missing) + " — đã tái phân bổ trọng số.")
    return int(round(est)), weights


def _confidence_score(
    comparables_used: int,
    estimated_value: int,
    method_values: List[int],
    comp_cv: Optional[float],
    notes: List[str],
) -> float:
    """confidence_score theo số comparable, độ đồng thuận 3 phương pháp & độ phân tán giá.

    - Tăng theo số comparable: ``0.30 + 0.08 × comparables_used`` (cap 0.95).
    - Giảm nếu 3 phương pháp lệch > 15% so với giá blend.
    - Giảm dần nếu comparable phân tán mạnh (CV > 8%) — thị trường biến động.
    - ``comparables_used == 0`` -> ép < 0.4 (SC-005) + note "không đủ dữ liệu".
    """
    conf = min(CONF_MAX, CONF_BASE + CONF_PER_COMP * comparables_used)

    # phạt độ lệch giữa các phương pháp
    if len(method_values) >= 2 and estimated_value:
        dispersion = (max(method_values) - min(method_values)) / estimated_value
        if dispersion > METHOD_DISPERSION_TOL:
            penalty = min(0.15, (dispersion - METHOD_DISPERSION_TOL))
            conf -= penalty
            notes.append(
                f"Độ lệch giữa 3 phương pháp ~{round(dispersion * 100)}% (>15%) — giảm độ tin cậy."
            )

    # phạt độ phân tán comparable
    if comp_cv and comp_cv > COMP_CV_TOL:
        penalty = min(0.20, (comp_cv - COMP_CV_TOL) * 1.2)
        conf -= penalty
        notes.append(
            f"Giá comparable phân tán ~{round(comp_cv * 100)}% (biến động thị trường) — giảm độ tin cậy."
        )

    if comparables_used == 0:
        conf = min(conf, CONF_ZERO_COMP_CAP)
        notes.append(NO_COMPARABLE_NOTE)

    return max(CONF_FLOOR, conf)


def _value_range(estimated_value: int, confidence: float) -> tuple:
    """Khoảng tin cậy quanh giá trị điểm; biên rộng hơn khi confidence thấp.

    ``spread = 0.15 × (1 - confidence) + 0.05`` (Nguyên tắc II: không false precision).
    Bảo đảm ``low < estimated_value < high``.
    """
    spread = SPREAD_CONF_COEF * (1 - confidence) + SPREAD_BASE
    low = int(round(estimated_value * (1 - spread)))
    high = int(round(estimated_value * (1 + spread)))
    # đảm bảo bất biến low < est < high kể cả khi làm tròn.
    low = min(low, estimated_value - 1)
    high = max(high, estimated_value + 1)
    return low, high


# --------------------------------------------------------------------------- #
# Tiện ích số học & thời gian
# --------------------------------------------------------------------------- #
def _access_premium(alley_width_m: Optional[float]) -> float:
    """Premium/penalty tiếp cận: mặt tiền đường lớn (None) = +6%; hẻm hẹp bị trừ."""
    if alley_width_m is None:
        return MAIN_ROAD_PREMIUM
    w = _pos_float(alley_width_m)
    if w is None:
        return 0.0
    return _clamp(-(ALLEY_REF_M - w) * ALLEY_PENALTY_PER_M, -ACCESS_ADJ_CAP, MAIN_ROAD_PREMIUM)


def _weighted_median(values: List[float], weights: List[float]) -> float:
    """Trung vị có trọng số: giá trị tại điểm khối lượng trọng số tích luỹ đạt 50%."""
    pairs = sorted(zip(values, weights), key=lambda p: p[0])
    total = sum(w for _, w in pairs)
    if total <= 0:
        return statistics.median(values)
    acc = 0.0
    half = total / 2
    for val, w in pairs:
        acc += w
        if acc >= half:
            return val
    return pairs[-1][0]


def _coefficient_of_variation(values: List[float]) -> Optional[float]:
    vals = [v for v in values if isinstance(v, (int, float))]
    if len(vals) < 2:
        return None
    mean = statistics.fmean(vals)
    if mean <= 0:
        return None
    return statistics.pstdev(vals) / mean


def _time_factor(price_index: dict, from_period: Optional[str], to_period: Optional[str]) -> Optional[float]:
    """index[to] / index[from] (data-model.md §3 business rule)."""
    if not from_period or not to_period:
        return None
    series = price_index.get("series", []) if isinstance(price_index, dict) else []
    idx = {p.get("period"): p.get("index") for p in series if p.get("period")}
    f, t = idx.get(from_period), idx.get(to_period)
    if f and t:
        return t / f
    return None


def _resolve_period(comparables: Sequence[dict], price_index: Optional[dict]) -> Optional[str]:
    if isinstance(price_index, dict):
        periods = [p.get("period") for p in price_index.get("series", []) if p.get("period")]
        if periods:
            return max(periods)
    periods = [c.get("time_adjustment_period") for c in comparables if c.get("time_adjustment_period")]
    if periods:
        return max(periods)
    return None


def _period_from_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    m = re.match(r"(\d{4})-(\d{2})-\d{2}", date_str)
    if not m:
        return None
    year, month = int(m.group(1)), int(m.group(2))
    return f"{year}-Q{(month - 1) // 3 + 1}"


def _empty_result(notes: List[str]) -> ValuationResult:
    return {
        "estimated_value": 0,
        "value_range": {"low": 0, "high": 0},
        "value_per_m2": 0,
        "confidence_score": CONF_FLOOR,
        "methodology_breakdown": {"comparable_approach": 0, "hedonic_model": 0, "cost_approach": 0},
        "comparables_used": 0,
        "time_adjustment_index_period": None,
        "adjustment_notes": notes,
    }


def _pos_float(x) -> Optional[float]:
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return float(x) if x > 0 else None


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _billions(x: float) -> float:
    return round(x / 1_000_000_000, 2)
