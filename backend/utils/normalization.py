from __future__ import annotations

import math
from typing import Any, Optional, Tuple


def parse_json_numeric_coord(val: Any) -> Optional[float]:
    """
    Coordinates from JSON body: only int or float (not bool, not string).
    """
    if val is None:
        return None
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        try:
            x = float(val)
        except (TypeError, ValueError):
            return None
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    return None


def parse_optional_coord(val: Any) -> Optional[float]:
    """
    Parse latitude/longitude from JSON or MongoDB types. Invalid or empty → None.
    Accepts comma decimals (e.g. 19,076), stripped strings, Decimal128, numpy scalars.
    """
    if val is None:
        return None
    if isinstance(val, str):
        s = val.strip().replace(",", ".")
        if not s:
            return None
        val = s
    if hasattr(val, "item") and callable(getattr(val, "item", None)):
        try:
            val = val.item()
        except Exception:
            pass
    try:
        from bson.decimal128 import Decimal128

        if isinstance(val, Decimal128):
            val = val.to_decimal()
    except Exception:
        pass
    try:
        from bson.int64 import Int64

        if isinstance(val, Int64):
            val = int(val)
    except Exception:
        pass
    try:
        x = float(val)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def is_valid_lat_lon(lat: Optional[float], lon: Optional[float]) -> bool:
    """True if both are finite and within geographic bounds."""
    if lat is None or lon is None:
        return False
    if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
        return False
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def extract_lat_lng(doc: Any) -> Tuple[Optional[float], Optional[float]]:
    """
    Read latitude/longitude from a user or task document.

    Tries, in order:
    - GeoJSON: location.type == Point → location.coordinates [lng, lat]
    - location_lat / location_lng (app schema)
    - location_lat / location_long (common typo)
    - latitude / longitude (ML seed data, CSV imports)
    - lat / lng
    """
    if not doc or not isinstance(doc, dict):
        return None, None

    loc = doc.get("location")
    if isinstance(loc, dict):
        if str(loc.get("type") or "").lower() == "point":
            coords = loc.get("coordinates")
            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                lng = parse_optional_coord(coords[0])
                lat = parse_optional_coord(coords[1])
                if lat is not None and lng is not None and is_valid_lat_lon(lat, lng):
                    return lat, lng

    key_pairs = (
        ("location_lat", "location_lng"),
        ("location_lat", "location_long"),
        ("latitude", "longitude"),
        ("lat", "lng"),
    )
    for ak, ok in key_pairs:
        la = parse_optional_coord(doc.get(ak))
        lo = parse_optional_coord(doc.get(ok))
        if la is not None and lo is not None and is_valid_lat_lon(la, lo):
            return la, lo
    for ak, ok in key_pairs:
        la = parse_optional_coord(doc.get(ak))
        lo = parse_optional_coord(doc.get(ok))
        if la is not None and lo is not None:
            return la, lo
    return None, None


def normalize(value: Any, max_value: Any) -> float:
    """
    Normalize value to [0, 1] using max_value.
    Safe for divide-by-zero and malformed inputs.
    """
    try:
        v = float(value)
    except Exception:
        v = 0.0
    try:
        m = float(max_value)
    except Exception:
        m = 0.0

    if m <= 0:
        return 0.0
    if v <= 0:
        return 0.0
    if v >= m:
        return 1.0
    return v / m

