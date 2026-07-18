"""market_price_lookup — tra cứu giao dịch/tin rao bán BĐS so sánh.

Tool của PAA Research Agent (tool spec: SHB_ThamDinhBDS_DesignDoc_2.md §8).

Input : address, lat, long, radius_km, period_from, period_to, property_type
Output: Lookup Tool Output Envelope (data-model.md §5) với
        ``data = {comparables: [ComparableTransaction + giá quy đổi], price_index_period_used}``

Nguồn dữ liệu: ``mockdata/transactions.json`` + ``mockdata/price_index.json``.
Lọc theo khoảng cách Haversine <= ``radius_km`` quanh (lat, long), lọc theo
``property_type`` (nếu truyền), khung thời gian ``period_from``/``period_to``
(nếu truyền), rồi quy đổi giá về kỳ hiện tại theo công thức mục 4.2 design doc:
``giá_quy_đổi = giá_giao_dịch × index[kỳ_hiện_tại] / index[kỳ_giao_dịch]``.
"""

from __future__ import annotations

from typing import Optional

from ._mockdata_utils import (
    DEFAULT_RADIUS_KM,
    avg_confidence,
    envelope,
    find_series,
    haversine_km,
    index_at,
    latest_period,
    load_mock,
    period_from_date,
    ward_from_address,
)

TOOL_NAME = "market_price_lookup"


def market_price_lookup(
    address: Optional[str] = None,
    lat: Optional[float] = None,
    long: Optional[float] = None,
    radius_km: float = DEFAULT_RADIUS_KM,
    period_from: Optional[str] = None,
    period_to: Optional[str] = None,
    property_type: Optional[str] = None,
) -> dict:
    """Trả về comparables trong bán kính, đã quy đổi giá theo chỉ số thời gian.

    - Thiếu ``lat``/``long`` -> ``status="error"`` (input không hợp lệ, không thể
      lọc theo bán kính).
    - Không có comparable nào -> ``status="partial"``, ``comparables=[]``,
      confidence thấp, kèm ``warning`` (thoả SC-005: không chặn pipeline).
    """
    if not _is_num(lat) or not _is_num(long):
        return envelope(
            TOOL_NAME, "error", 0.0,
            {"comparables": [], "price_index_period_used": None},
            warning="Thiếu toạ độ lat/long — không thể lọc giao dịch so sánh theo bán kính.",
        )

    if not _is_num(radius_km) or radius_km <= 0:
        radius_km = DEFAULT_RADIUS_KM

    txns = load_mock("transactions.json").get("transactions", [])

    # Kỳ hiện tại của chính subject (dùng làm price_index_period_used tổng thể).
    subject_ward = ward_from_address(address)
    subject_series = find_series(subject_ward, property_type) if property_type else None
    period_used = latest_period(subject_series) if subject_series else None

    comparables = []
    for tx in txns:
        tlat, tlong = tx.get("lat"), tx.get("long")
        if not (_is_num(tlat) and _is_num(tlong)):
            continue

        # (1) lọc theo property_type nếu caller yêu cầu
        if property_type and tx.get("property_type") != property_type:
            continue

        # (2) lọc theo bán kính (tính lại khoảng cách thực tới subject)
        dist_km = round(haversine_km(lat, long, tlat, tlong), 3)
        if dist_km > radius_km:
            continue

        # (3) lọc theo khung thời gian (period_from/period_to dạng YYYY-Qn)
        tx_period = period_from_date(tx.get("transaction_date", ""))
        if period_from and tx_period and tx_period < period_from:
            continue
        if period_to and tx_period and tx_period > period_to:
            continue

        comp = _adjust_price(tx, dist_km, tx_period, period_used)
        comparables.append(comp)

    comparables.sort(key=lambda c: c.get("distance_from_subject_km", float("inf")))

    if not comparables:
        return envelope(
            TOOL_NAME, "partial", 0.25,
            {"comparables": [], "price_index_period_used": period_used},
            warning=(
                f"Không tìm thấy giao dịch so sánh nào trong bán kính {radius_km}km "
                f"quanh toạ độ ({lat}, {long})"
                + (f" cho loại {property_type}" if property_type else "")
                + " — cần thẩm định viên bổ sung dữ liệu."
            ),
        )

    conf = avg_confidence(comparables, default=0.5)
    warning = None
    if period_used is None:
        warning = (
            "Không xác định được kỳ chỉ số giá của subject — giá quy đổi dùng kỳ "
            "mới nhất của từng khu vực/loại tài sản tương ứng."
        )
    return envelope(
        TOOL_NAME, "ok", conf,
        {"comparables": comparables, "price_index_period_used": period_used},
        warning=warning,
    )


def _adjust_price(tx: dict, dist_km: float, tx_period: Optional[str],
                  fallback_period: Optional[str]) -> dict:
    """Sao chép comparable + thêm giá quy đổi theo chỉ số thời gian."""
    comp = dict(tx)
    comp["distance_from_subject_km"] = dist_km
    comp["transaction_period"] = tx_period

    series = find_series(ward_from_address(tx.get("address")), tx.get("property_type"))
    cur_period = latest_period(series) or fallback_period
    factor = None
    if series and cur_period and tx_period:
        cur_idx = index_at(series, cur_period)
        tx_idx = index_at(series, tx_period)
        if cur_idx and tx_idx:
            factor = cur_idx / tx_idx

    comp["time_adjustment_period"] = cur_period
    comp["time_adjustment_factor"] = round(factor, 4) if factor else None
    if factor:
        pt = tx.get("price_total")
        ppm = tx.get("price_per_m2")
        comp["adjusted_price_total"] = round(pt * factor) if _is_num(pt) else None
        comp["adjusted_price_per_m2"] = round(ppm * factor) if _is_num(ppm) else None
    else:
        # Không quy đổi được -> giữ nguyên giá gốc, đánh dấu factor null.
        comp["adjusted_price_total"] = tx.get("price_total")
        comp["adjusted_price_per_m2"] = tx.get("price_per_m2")
    return comp


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)
