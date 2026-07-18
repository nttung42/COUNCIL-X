"""calculate_asset_risk_score — Risk Scoring Engine của PAA (design doc §4.3).

Chấm điểm RỦI RO NỘI TẠI của bất động sản (tách biệt rủi ro tín dụng người vay)
bằng tổng có trọng số của 5 nhóm rủi ro, trả về ``AssetRiskAssessment`` đúng schema
``specs/001-property-appraisal-agent/data-model.md §7``:

    asset_risk_score = 0.30*legal + 0.25*liquidity + 0.20*price_volatility
                     + 0.15*physical_environmental + 0.10*reputation_stigma

Mỗi nhóm cho điểm 0-100 (100 = rủi ro cao nhất).

================================================================================
NGUYÊN TẮC III (Stigma Data Isolation) — QUAN TRỌNG NHẤT
================================================================================
Nhóm ``reputation_stigma`` chỉ chiếm TRỌNG SỐ 10%. Công thức trọng số ở
``_weighted_total`` thể hiện rõ điều này: DÙ ``reputation_stigma = 100`` mà 4 nhóm
còn lại = 0 thì ``asset_risk_score`` tối đa chỉ = 10 -> KHÔNG THỂ tự nó đẩy tài sản
lên tier HIGH (>60). Không có bất kỳ nhánh code nào loại trừ/từ chối hồ sơ dựa trên
nhóm này; tin đồn chỉ sinh ``flag`` cảnh báo ``verified=false`` yêu cầu xác minh
thực địa. Xem ``self-check`` cuối file để chứng minh cơ chế cô lập.

--------------------------------------------------------------------------------
HỢP ĐỒNG INPUT/OUTPUT (để Orchestrator wiring — Nguyên tắc IV)
--------------------------------------------------------------------------------
Hàm nhận ``ValuationResult`` + các **Lookup Tool Output Envelope** (data-model.md
§5) đúng như 7 lookup tool trả về (không cần bóc tách trước):

- ``valuation``             : dict ``ValuationResult`` (§6) — dùng cho fallback biến động giá.
- ``legal_envelope``        : ``legal_status_lookup(...)`` -> data{legal_status, has_dispute, mortgaged_elsewhere}
- ``planning_envelope``     : ``planning_zoning_lookup(...)`` -> data{is_planned_overlay, road_widening_plan}
- ``liquidity_envelope``    : ``liquidity_stat_lookup(...)`` -> data{avg_days_on_market, success_rate_pct}
- ``environmental_envelope``: ``environmental_risk_lookup(...)`` -> data{flood_risk, landslide_risk, pollution_risk}
- ``stigma_envelope``       : ``stigma_reputation_lookup(...)`` -> data{rumors:[{detail, year, confidence, verified:false}]}
- ``comparables``           : list ``ComparableTransaction`` (tuỳ chọn) — cùng list
  truyền cho ``calculate_valuation`` — dùng tính độ lệch chuẩn giá cho nhóm biến động.

Mọi tham số envelope đều tuỳ chọn: thiếu/`` status != "ok"`` -> nhóm tương ứng
tính theo dữ liệu trung tính, không raise (Error Handling agent spec).

Trả về ``dict`` khớp ``AssetRiskAssessment`` (§7).
"""

from __future__ import annotations

import statistics
from typing import List, Optional, Sequence, TypedDict


# --------------------------------------------------------------------------- #
# Type hints tham chiếu data-model.md §7
# --------------------------------------------------------------------------- #
class RiskGroupScores(TypedDict):
    legal: int
    liquidity: int
    price_volatility: int
    physical_environmental: int
    reputation_stigma: int


class RiskFlag(TypedDict, total=False):
    type: str
    severity: str           # low | medium | high
    detail: str
    confidence: float
    action: str
    verified: bool          # flag type=stigma BẮT BUỘC verified=false


class AssetRiskAssessment(TypedDict):
    asset_risk_score: int
    risk_tier: str          # LOW | MEDIUM | HIGH
    recommended_ltv_cap: float
    risk_group_scores: RiskGroupScores
    flags: List[RiskFlag]
    recommended_conditions: List[str]


# --------------------------------------------------------------------------- #
# Trọng số 5 nhóm (design doc §4.3). Tổng = 1.00.
# --------------------------------------------------------------------------- #
RISK_WEIGHTS = {
    "legal": 0.30,
    "liquidity": 0.25,
    "price_volatility": 0.20,
    "physical_environmental": 0.15,
    "reputation_stigma": 0.10,   # <= trần cô lập (Nguyên tắc III)
}

# --- Legal (30%) ---
LEGAL_DISPUTE = 50
LEGAL_MORTGAGED = 40
LEGAL_OVERLAY = 20              # is_planned_overlay = True (quy hoạch treo)
LEGAL_ROAD_WIDENING = 15       # có kế hoạch lộ giới/mở đường ảnh hưởng một phần thửa
LEGAL_NON_STANDARD_TITLE = 25  # giấy tờ không phải sổ đỏ/sổ hồng
LEGAL_UNKNOWN = 20             # không tra cứu được pháp lý -> rủi ro tồn nghi

# --- Physical/Environmental (15%): map mức rủi ro -> điểm, lấy MAX 3 yếu tố ---
ENV_LEVEL_SCORE = {
    "none": 0, "none_recorded": 0, "no": 0, "": 0, None: 0,
    "low": 30, "low_recorded": 30,
    "medium": 60, "medium_recorded": 60,
    "high": 90, "high_recorded": 90,
    "unknown": 15,                # không rõ -> rủi ro tồn nghi nhẹ
}

# --- Reputation/Stigma (10%) ---
STIGMA_MAX_GROUP_SCORE = 70    # trần điểm nhóm; kết hợp trọng số 10% -> tối đa +7 điểm tổng
STIGMA_CONF_COEF = 0.8         # điểm tỷ lệ thuận confidence gốc tin đồn

# --- Ngưỡng tier & LTV (kb_documents/05-quy-dinh-ltv-tham-khao.md) ---
TIER_LOW_MAX = 30              # LOW  <= 30
TIER_MEDIUM_MAX = 60          # MEDIUM 31-60 ; HIGH > 60
LTV_CAP = {"LOW": 0.70, "MEDIUM": 0.65, "HIGH": 0.50}


# --------------------------------------------------------------------------- #
# Hàm chính
# --------------------------------------------------------------------------- #
def calculate_asset_risk_score(
    valuation: Optional[dict] = None,
    legal_envelope: Optional[dict] = None,
    planning_envelope: Optional[dict] = None,
    liquidity_envelope: Optional[dict] = None,
    environmental_envelope: Optional[dict] = None,
    stigma_envelope: Optional[dict] = None,
    comparables: Optional[Sequence[dict]] = None,
) -> AssetRiskAssessment:
    """Chấm điểm rủi ro tài sản 5 nhóm có trọng số -> ``AssetRiskAssessment`` (§7).

    Xem docstring module cho hợp đồng input/output & cơ chế cô lập Nguyên tắc III.
    """
    flags: List[RiskFlag] = []
    conditions: List[str] = []

    legal = _score_legal(legal_envelope, planning_envelope, flags, conditions)
    liquidity = _score_liquidity(liquidity_envelope, flags, conditions)
    price_volatility = _score_price_volatility(comparables, valuation, flags)
    physical_environmental = _score_environmental(environmental_envelope, flags, conditions)
    reputation_stigma = _score_stigma(stigma_envelope, flags, conditions)

    group_scores: RiskGroupScores = {
        "legal": legal,
        "liquidity": liquidity,
        "price_volatility": price_volatility,
        "physical_environmental": physical_environmental,
        "reputation_stigma": reputation_stigma,
    }

    asset_risk_score = _weighted_total(group_scores)
    risk_tier = _tier(asset_risk_score)
    ltv_cap = LTV_CAP[risk_tier]

    if not flags:
        flags.append({
            "type": "legal", "severity": "low",
            "detail": "Không ghi nhận yếu tố rủi ro nổi bật từ các nguồn tra cứu.",
            "confidence": 0.8,
        })

    return {
        "asset_risk_score": asset_risk_score,
        "risk_tier": risk_tier,
        "recommended_ltv_cap": ltv_cap,
        "risk_group_scores": group_scores,
        "flags": flags,
        "recommended_conditions": _dedupe(conditions),
    }


# --------------------------------------------------------------------------- #
# 1. Rủi ro pháp lý (30%)
# --------------------------------------------------------------------------- #
def _score_legal(
    legal_env: Optional[dict],
    planning_env: Optional[dict],
    flags: List[RiskFlag],
    conditions: List[str],
) -> int:
    """0 nếu sổ hồng/đỏ hợp lệ + không tranh chấp/thế chấp/quy hoạch treo; cộng dồn rủi ro."""
    legal = _data(legal_env)
    planning = _data(planning_env)
    score = 0

    legal_status = legal.get("legal_status")
    has_dispute = bool(legal.get("has_dispute"))
    mortgaged = bool(legal.get("mortgaged_elsewhere"))
    is_overlay = bool(planning.get("is_planned_overlay"))
    road_widening = planning.get("road_widening_plan")

    if _status(legal_env) not in ("ok",) and not legal_status:
        score += LEGAL_UNKNOWN
        flags.append({
            "type": "legal", "severity": "medium",
            "detail": "Không tra cứu được hồ sơ pháp lý — cần đối chiếu văn phòng đăng ký đất đai/CIC.",
            "confidence": 0.4,
            "action": "Xác minh pháp lý trực tiếp trước khi định giá tài sản bảo đảm.",
        })
        conditions.append("Đối chiếu hồ sơ pháp lý gốc tại văn phòng đăng ký đất đai/CIC.")

    if has_dispute:
        score += LEGAL_DISPUTE
        flags.append({
            "type": "legal", "severity": "high",
            "detail": "Tài sản có ghi nhận tranh chấp — rủi ro pháp lý cao.",
            "confidence": 0.9,
            "action": "Yêu cầu hồ sơ giải quyết tranh chấp trước khi nhận thế chấp.",
        })
        conditions.append("Yêu cầu hồ sơ chứng minh tranh chấp đã được giải quyết dứt điểm.")

    if mortgaged:
        score += LEGAL_MORTGAGED
        flags.append({
            "type": "legal", "severity": "high",
            "detail": "Tài sản đang thế chấp tại tổ chức tín dụng khác.",
            "confidence": 0.9,
            "action": "Yêu cầu giải chấp trước khi nhận làm tài sản bảo đảm mới.",
        })
        conditions.append("Yêu cầu giải chấp tại TCTD hiện hữu trước khi ký hợp đồng bảo đảm.")

    if legal_status and legal_status not in ("so_hong", "so_do"):
        score += LEGAL_NON_STANDARD_TITLE
        flags.append({
            "type": "legal", "severity": "medium",
            "detail": f"Giấy tờ pháp lý không phải sổ đỏ/sổ hồng ({legal_status}).",
            "confidence": 0.85,
            "action": "Yêu cầu hoàn thiện thủ tục cấp giấy chứng nhận hợp lệ.",
        })
        conditions.append("Yêu cầu hoàn thiện giấy chứng nhận quyền sử dụng đất/sở hữu nhà hợp lệ.")

    if is_overlay:
        score += LEGAL_OVERLAY
        flags.append({
            "type": "legal", "severity": "medium",
            "detail": "Một phần/toàn bộ thửa nằm trong quy hoạch (planned overlay).",
            "confidence": 0.8,
            "action": "Xác minh ranh quy hoạch, phần diện tích bị ảnh hưởng.",
        })
        conditions.append("Xác minh chỉ giới quy hoạch và diện tích hợp pháp còn lại.")
    elif road_widening:
        # Không phải overlay treo, nhưng có kế hoạch lộ giới/mở đường -> rủi ro nhẹ.
        score += LEGAL_ROAD_WIDENING
        flags.append({
            "type": "planning", "severity": "low",
            "detail": f"Có kế hoạch lộ giới/mở đường liên quan: {road_widening}",
            "confidence": 0.7,
            "action": "Kiểm tra ảnh hưởng lộ giới tới diện tích/kết cấu tài sản.",
        })
        conditions.append("Kiểm tra ảnh hưởng của kế hoạch lộ giới tới diện tích khai thác thực tế.")

    return _cap100(score)


# --------------------------------------------------------------------------- #
# 2. Rủi ro thanh khoản (25%)
# --------------------------------------------------------------------------- #
def _score_liquidity(
    liquidity_env: Optional[dict],
    flags: List[RiskFlag],
    conditions: List[str],
) -> int:
    """Trung bình 2 yếu tố: thời gian bán trung bình & (100 - tỷ lệ thành công).

    - ``days_score`` = min(100, avg_days_on_market): càng lâu bán càng rủi ro.
    - ``success_score`` = 100 - success_rate_pct: tỷ lệ chốt thấp -> rủi ro cao.
    Thiếu dữ liệu -> điểm trung tính 50 + flag nhắc bổ sung.
    """
    data = _data(liquidity_env)
    days = data.get("avg_days_on_market")
    success = data.get("success_rate_pct")

    if not _is_num(days) and not _is_num(success):
        flags.append({
            "type": "liquidity", "severity": "low",
            "detail": "Thiếu thống kê thanh khoản khu vực — dùng điểm trung tính.",
            "confidence": 0.3,
        })
        return 50

    days_score = min(100, float(days)) if _is_num(days) else 50.0
    success_score = _cap100(100 - float(success)) if _is_num(success) else 50.0
    score = _cap100(round(0.5 * days_score + 0.5 * success_score))

    if score >= 55:
        flags.append({
            "type": "liquidity", "severity": "medium" if score < 75 else "high",
            "detail": (
                f"Thanh khoản khu vực chậm (bán TB {days} ngày, tỷ lệ thành công {success}%)."
            ),
            "confidence": 0.7,
        })
        conditions.append("Cân nhắc hạ tỷ lệ cho vay hoặc yêu cầu tài sản bảo đảm bổ sung do thanh khoản chậm.")
    return score


# --------------------------------------------------------------------------- #
# 3. Rủi ro biến động giá (20%)
# --------------------------------------------------------------------------- #
def _score_price_volatility(
    comparables: Optional[Sequence[dict]],
    valuation: Optional[dict],
    flags: List[RiskFlag],
) -> int:
    """Chuẩn hoá độ phân tán giá/m² của các comparable về thang 0-100.

    Dùng hệ số biến thiên (CV = std/mean) của ``adjusted_price_per_m2`` (hoặc
    ``price_per_m2``). CV càng lớn -> giá khu vực càng biến động -> điểm càng cao:

        volatility_score = min(100, CV × 300)

    (CV ~0.17 -> ~51 điểm.) Thiếu comparable -> suy từ ``confidence_score`` của
    ValuationResult (định giá kém tin cậy thường do thị trường biến động).
    """
    ppm2s = []
    for c in (comparables or []):
        v = c.get("adjusted_price_per_m2") or c.get("price_per_m2")
        if _is_num(v) and v > 0:
            ppm2s.append(float(v))

    if len(ppm2s) >= 2:
        mean = statistics.fmean(ppm2s)
        cv = statistics.pstdev(ppm2s) / mean if mean > 0 else 0.0
        score = _cap100(round(cv * 300))
        if score >= 50:
            flags.append({
                "type": "price_volatility", "severity": "medium" if score < 75 else "high",
                "detail": f"Giá khu vực biến động mạnh (hệ số biến thiên ~{round(cv * 100)}%).",
                "confidence": 0.6,
            })
        return score

    # fallback: dựa confidence định giá.
    conf = (valuation or {}).get("confidence_score")
    if _is_num(conf):
        return _cap100(round((1 - float(conf)) * 60))
    return 40


# --------------------------------------------------------------------------- #
# 4. Rủi ro vật lý/môi trường (15%)
# --------------------------------------------------------------------------- #
def _score_environmental(
    env_env: Optional[dict],
    flags: List[RiskFlag],
    conditions: List[str],
) -> int:
    """MAX điểm của {flood, landslide, pollution}; none->0, low->30, medium->60, high->90."""
    data = _data(env_env)
    factors = {
        "flood_risk": data.get("flood_risk"),
        "landslide_risk": data.get("landslide_risk"),
        "pollution_risk": data.get("pollution_risk"),
    }
    scores = {k: ENV_LEVEL_SCORE.get(_norm(v), 15 if v else 0) for k, v in factors.items()}
    score = max(scores.values()) if scores else 0

    for key, raw in factors.items():
        level = _norm(raw)
        if level in ("low", "low_recorded", "medium", "medium_recorded", "high", "high_recorded"):
            sev = "low" if level.startswith("low") else ("medium" if level.startswith("medium") else "high")
            flags.append({
                "type": "environmental", "severity": sev,
                "detail": f"{_env_label(key)}: mức {raw}.",
                "confidence": _conf(env_env, 0.7),
                "action": "Khảo sát thực địa & cân nhắc yêu cầu bảo hiểm tài sản.",
            })
            if key == "flood_risk":
                conditions.append("Mua bảo hiểm tài sản do khu vực từng ghi nhận ngập.")
            else:
                conditions.append(f"Đánh giá kỹ {_env_label(key).lower()} khi thẩm định thực địa.")

    return _cap100(score)


# --------------------------------------------------------------------------- #
# 5. Rủi ro danh tiếng/tâm linh (10%) — NGUYÊN TẮC III
# --------------------------------------------------------------------------- #
def _score_stigma(
    stigma_env: Optional[dict],
    flags: List[RiskFlag],
    conditions: List[str],
) -> int:
    """Điểm nhóm tin đồn/tâm linh — LUÔN chỉ tạo flag cảnh báo, không loại trừ hồ sơ.

    KHÔNG có tin đồn -> 0. Có tin đồn -> điểm tỷ lệ thuận confidence GỐC của tin đồn:

        score = min(70, max(confidence_i) × 100 × 0.8)

    Trọng số nhóm là 10% (``_weighted_total``) nên dù score=70 cũng chỉ đóng góp
    tối đa 7 điểm vào tổng -> KHÔNG thể một mình đẩy tài sản lên HIGH (Nguyên tắc III).
    Mọi flag sinh ra ở đây BẮT BUỘC ``verified=False`` (truyền nguyên từ input,
    không bao giờ set lại True).
    """
    data = _data(stigma_env)
    rumors = data.get("rumors") or []
    if not rumors:
        return 0

    max_conf = 0.0
    for r in rumors:
        conf = r.get("confidence")
        conf = float(conf) if _is_num(conf) else 0.3
        max_conf = max(max_conf, conf)
        # RÀNG BUỘC CỨNG: verified luôn False (không đọc/không set True từ bất cứ đâu).
        flags.append({
            "type": "stigma", "severity": "medium",
            "detail": r.get("detail", "Tin đồn/dư luận chưa xác thực về tài sản/khu vực."),
            "confidence": conf,
            "action": "Yêu cầu khảo sát thực địa xác minh — KHÔNG dùng làm căn cứ từ chối tín dụng.",
            "verified": False,
        })

    conditions.append(
        "Yêu cầu thẩm định viên khảo sát thực địa xác minh thông tin dư luận chưa kiểm chứng "
        "(chỉ để tham khảo, không phải căn cứ pháp lý)."
    )
    return int(min(STIGMA_MAX_GROUP_SCORE, round(max_conf * 100 * STIGMA_CONF_COEF)))


# --------------------------------------------------------------------------- #
# Tổng hợp có trọng số + tier
# --------------------------------------------------------------------------- #
def _weighted_total(groups: RiskGroupScores) -> int:
    """asset_risk_score = Σ trọng_số × điểm_nhóm (design doc §4.3).

    Cơ chế cô lập Nguyên tắc III nằm ngay ở đây: reputation_stigma nhân đúng 0.10,
    không có bất kỳ đường tắt nào cho phép nhóm này vượt trần 10% ảnh hưởng.
    """
    total = sum(RISK_WEIGHTS[k] * groups[k] for k in RISK_WEIGHTS)
    return int(round(_cap100(total)))


def _tier(score: int) -> str:
    if score <= TIER_LOW_MAX:
        return "LOW"
    if score <= TIER_MEDIUM_MAX:
        return "MEDIUM"
    return "HIGH"


# --------------------------------------------------------------------------- #
# Tiện ích
# --------------------------------------------------------------------------- #
def _data(env: Optional[dict]) -> dict:
    if isinstance(env, dict):
        d = env.get("data")
        if isinstance(d, dict):
            return d
        # cho phép truyền thẳng payload data (không bọc envelope)
        return env
    return {}


def _status(env: Optional[dict]) -> Optional[str]:
    return env.get("status") if isinstance(env, dict) else None


def _conf(env: Optional[dict], default: float) -> float:
    if isinstance(env, dict) and _is_num(env.get("confidence")):
        return float(env["confidence"])
    return default


def _env_label(key: str) -> str:
    return {
        "flood_risk": "Rủi ro ngập úng",
        "landslide_risk": "Rủi ro sạt lở",
        "pollution_risk": "Rủi ro ô nhiễm",
    }.get(key, key)


def _norm(v) -> str:
    return v.strip().lower() if isinstance(v, str) else ("" if v is None else str(v).lower())


def _dedupe(items: List[str]) -> List[str]:
    seen, out = set(), []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _cap100(x) -> int:
    return int(max(0, min(100, x)))


# --------------------------------------------------------------------------- #
# Self-check nội bộ (Nguyên tắc III) — chạy: python -m app.tools.calculate_asset_risk_score
# Chứng minh: reputation_stigma=100 mà 4 nhóm khác = 0 -> tổng chỉ = 10 (LOW).
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    isolated = _weighted_total({
        "legal": 0, "liquidity": 0, "price_volatility": 0,
        "physical_environmental": 0, "reputation_stigma": 100,
    })
    assert isolated == 10, f"Cô lập stigma sai: {isolated}"
    assert _tier(isolated) == "LOW", "Stigma tối đa vẫn phải là LOW"
    print("OK — Nguyên tắc III: reputation_stigma=100 (4 nhóm khác=0) -> asset_risk_score =",
          isolated, "(", _tier(isolated), ") — không thể đẩy lên HIGH.")
