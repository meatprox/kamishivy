from __future__ import annotations

from typing import Any


_FULLWIDTH = str.maketrans("０１２３４５６７８９．－＋", "0123456789.-+")


def parse_number(text: str) -> float | None:
    raw = str(text or "").strip().translate(_FULLWIDTH)
    raw = raw.replace(",", "").replace("，", "")
    if raw in ("", ".", "-", "+", "-.", "+."):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse_seconds(text: str) -> int | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    if ":" in raw:
        parts = [part.strip() for part in raw.split(":")]
        if not parts or any(part == "" for part in parts):
            return None
        try:
            nums = [int(part) for part in parts]
        except ValueError:
            return None
        if any(n < 0 for n in nums):
            return None
        if len(nums) == 2:
            return nums[0] * 60 + nums[1]
        if len(nums) == 3:
            return nums[0] * 3600 + nums[1] * 60 + nums[2]
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if value < 0:
        return None
    if 0 < value < 1:
        return int(round(value * 86400))
    return int(value)


PARSE_MODE_NONE = "none"
PARSE_MODE_SLICE = "slice"
PARSE_MODE_CSV = "csv"
PARSE_OUTPUT_TEXT = "text"
PARSE_OUTPUT_NUMBER = "number"
PARSE_MODES = (PARSE_MODE_NONE, PARSE_MODE_SLICE, PARSE_MODE_CSV)
PARSE_OUTPUTS = (PARSE_OUTPUT_TEXT, PARSE_OUTPUT_NUMBER)
PARSE_MODE_LABELS = {
    PARSE_MODE_NONE: "加工しない",
    PARSE_MODE_SLICE: "文字列の一部",
    PARSE_MODE_CSV: "カンマ区切り",
}
PARSE_OUTPUT_LABELS = {
    PARSE_OUTPUT_TEXT: "文字",
    PARSE_OUTPUT_NUMBER: "数値",
}


def process_received(text: str, spec: dict[str, Any]) -> str | None:
    """COM の生文字を、加工設定に従って UI へ渡す値にする。"""
    raw = str(text or "")
    mode = str(spec.get("mode") or PARSE_MODE_NONE).strip().lower()
    output = str(spec.get("output") or PARSE_OUTPUT_TEXT).strip().lower()
    if mode == PARSE_MODE_SLICE:
        try:
            start = int(spec.get("start") or 1)
        except (TypeError, ValueError):
            start = 1
        try:
            end = int(spec.get("end") or start)
        except (TypeError, ValueError):
            end = start
        start = max(1, start)
        end = max(start, end)
        piece = raw[start - 1 : end]
    elif mode == PARSE_MODE_CSV:
        try:
            index = int(spec.get("csv") or 1)
        except (TypeError, ValueError):
            index = 1
        index = max(1, index)
        parts = [part.strip() for part in raw.replace("，", ",").split(",")]
        piece = parts[index - 1] if index <= len(parts) else ""
    else:
        piece = raw
    if output == PARSE_OUTPUT_NUMBER:
        value = parse_number(piece)
        if value is None:
            return None
        if float(value).is_integer():
            return str(int(value))
        return f"{value:g}"
    return piece


def format_remain(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
