from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any

from app.paths import app_root


DESIGN_PATH = app_root() / "design.ini"

DEFAULTS: dict[str, Any] = {
    "font_family": "ＭＳ Ｐゴシック",
    "font_size": 9,
    "font_bold": 0,
    "header_font_family": "ＭＳ Ｐゴシック",
    "header_font_size": 9,
    "header_font_bold": 0,
    "footer_font_family": "ＭＳ Ｐゴシック",
    "footer_font_size": 11,
    "footer_font_bold": 0,
    "button_font_size": 9,
    "header_button_font_size": 9,
    "footer_button_font_size": 11,
    "title_font_family": "ＭＳ Ｐゴシック",
    "title_font_size": 20,
    "title_text": (0, 0, 0),
    "text": (0, 0, 0),
    "background": (240, 240, 240),
    "button": (240, 240, 240),
    "button_text": (0, 0, 0),
    "gadget": (255, 255, 255),
    "textbox": (255, 255, 255),
    "border": (160, 160, 160),
    "menu": (240, 240, 240),
    "menu_text": (0, 0, 0),
    "header_text": (0, 0, 0),
    "header_background": (240, 240, 240),
    "header_button": (240, 240, 240),
    "header_button_text": (0, 0, 0),
    "footer_text": (0, 0, 0),
    "footer_background": (240, 240, 240),
    "footer_button": (240, 240, 240),
    "footer_button_text": (0, 0, 0),
    "footer_text_disabled": (160, 160, 160),
    "footer_button_disabled": (240, 240, 240),
    "border_enabled": 1,
    "border_width": 1,
    "content_margin": 12,
}

# 中段（基準）。UI が参照するキー。
COLOR_KEYS = ("text", "background", "button", "button_text", "gadget", "textbox", "border", "menu", "menu_text", "title_text")
REGION_COLOR_KEYS = ("text", "background", "button", "button_text")
FOOTER_COLOR_KEYS = ("text", "background", "button", "button_text", "text_disabled", "button_disabled")
REGIONS = ("header", "footer")


def parse_rgb(text: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    parts = [part.strip() for part in str(text).replace(";", ",").split(",") if part.strip()]
    if len(parts) < 3:
        return fallback
    try:
        rgb = tuple(max(0, min(255, int(float(parts[index])))) for index in range(3))
    except ValueError:
        return fallback
    return rgb  # type: ignore[return-value]


def format_rgb(rgb: tuple[int, int, int]) -> str:
    return f"{int(rgb[0])},{int(rgb[1])},{int(rgb[2])}"


def rgb_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"


def hex_to_rgb(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    text = (value or "").strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        return fallback
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError:
        return fallback


def _get_int(parser: configparser.ConfigParser, section: str, key: str, fallback: int) -> int:
    try:
        return parser.getint(section, key, fallback=fallback)
    except (ValueError, TypeError):
        return fallback


def _clamp_size(size: int) -> int:
    return max(8, min(72, size))


def _safe_size(value: Any, fallback: int) -> int:
    try:
        return _clamp_size(int(value))
    except (TypeError, ValueError):
        return _clamp_size(int(fallback))


def _clamp_margin(value: int) -> int:
    return max(0, min(200, value))


def _safe_margin(value: Any, fallback: int) -> int:
    try:
        return _clamp_margin(int(value))
    except (TypeError, ValueError):
        return _clamp_margin(int(fallback))


def font_tuple(family: str, size: int, bold: Any = 0) -> tuple[str, int] | tuple[str, int, str]:
    try:
        is_bold = int(bold) != 0
    except (TypeError, ValueError):
        is_bold = bool(bold)
    if is_bold:
        return (str(family), int(size), "bold")
    return (str(family), int(size))


def _as_flag(value: Any, fallback: int = 0) -> int:
    try:
        return 0 if int(value if value is not None else fallback) == 0 else 1
    except (TypeError, ValueError):
        return 0 if int(fallback) == 0 else 1


def _emit_color(data: dict[str, Any], key: str, rgb: tuple[int, int, int]) -> None:
    data[key] = rgb_hex(rgb)
    data[f"{key}_r"] = rgb[0]
    data[f"{key}_g"] = rgb[1]
    data[f"{key}_b"] = rgb[2]
    data[f"{key}_rgb"] = rgb


def _read_font(
    parser: configparser.ConfigParser,
    section: str,
    fallback_family: str,
    fallback_size: int,
    fallback_bold: int = 0,
) -> tuple[str, int, int]:
    family = fallback_family
    size = fallback_size
    bold = fallback_bold
    if parser.has_section(section):
        family = parser.get(section, "family", fallback=fallback_family).strip() or fallback_family
        size = _get_int(parser, section, "size", fallback_size)
        bold = 0 if _get_int(parser, section, "bold", fallback_bold) == 0 else 1
    return family, _clamp_size(size), bold


def _read_colors(
    parser: configparser.ConfigParser,
    section: str,
    keys: tuple[str, ...],
    fallbacks: dict[str, tuple[int, int, int]],
) -> dict[str, tuple[int, int, int]]:
    colors: dict[str, tuple[int, int, int]] = {}
    for key in keys:
        fallback = fallbacks[key]
        if parser.has_section(section):
            raw = parser.get(section, key, fallback=format_rgb(fallback))
        else:
            raw = format_rgb(fallback)
        colors[key] = parse_rgb(raw, fallback)
    return colors


def _color_from_data(data: dict[str, Any], key: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    raw = data.get(f"{key}_rgb")
    if isinstance(raw, tuple) and len(raw) == 3:
        return (int(raw[0]), int(raw[1]), int(raw[2]))
    return hex_to_rgb(str(data.get(key, "")), fallback)


def load_design(path: Path | None = None) -> dict[str, Any]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(path or DESIGN_PATH, encoding="utf-8")
    family, size, bold = _read_font(
        parser,
        "font",
        str(DEFAULTS["font_family"]),
        int(DEFAULTS["font_size"]),
        int(DEFAULTS["font_bold"]),
    )
    colors = _read_colors(parser, "color", COLOR_KEYS, {key: DEFAULTS[key] for key in COLOR_KEYS})
    if not parser.has_option("color", "menu"):
        colors["menu"] = colors.get("button", DEFAULTS["button"])
    if not parser.has_option("color", "button_text"):
        colors["button_text"] = colors.get("text", DEFAULTS["text"])
    if not parser.has_option("color", "title_text"):
        colors["title_text"] = colors.get("text", DEFAULTS["text"])
    header_family, header_size, header_bold = _read_font(parser, "font_header", family, size, bold)
    footer_family, footer_size, footer_bold = _read_font(parser, "font_footer", family, size, bold)
    title_family, title_size, _ = _read_font(
        parser,
        "font_title",
        family,
        int(DEFAULTS["title_font_size"]),
        0,
    )
    button_size = _safe_size(
        _get_int(parser, "font", "button_size", size) if parser.has_option("font", "button_size") else size,
        size,
    )
    header_button_size = _safe_size(
        _get_int(parser, "font_header", "button_size", header_size)
        if parser.has_option("font_header", "button_size")
        else header_size,
        header_size,
    )
    footer_button_size = _safe_size(
        _get_int(parser, "font_footer", "button_size", footer_size)
        if parser.has_option("font_footer", "button_size")
        else footer_size,
        footer_size,
    )
    region_fallbacks = {key: colors[key] for key in REGION_COLOR_KEYS}
    header_colors = _read_colors(parser, "color_header", REGION_COLOR_KEYS, region_fallbacks)
    footer_colors = _read_colors(parser, "color_footer", REGION_COLOR_KEYS, region_fallbacks)
    if not parser.has_option("color_header", "button_text"):
        header_colors["button_text"] = header_colors.get("text", colors.get("text", DEFAULTS["text"]))
    if not parser.has_option("color_footer", "button_text"):
        footer_colors["button_text"] = footer_colors.get("text", colors.get("text", DEFAULTS["text"]))
    footer_colors.update(
        _read_colors(
            parser,
            "color_footer",
            ("text_disabled", "button_disabled"),
            {
                "text_disabled": footer_colors["text"],
                "button_disabled": footer_colors["button"],
            },
        )
    )
    if not parser.has_option("color", "menu_text"):
        colors["menu_text"] = header_colors.get("text", colors.get("text", DEFAULTS["text"]))
    border_enabled = 0 if _get_int(parser, "border", "enabled", int(DEFAULTS["border_enabled"])) == 0 else 1
    border_width = max(0, min(8, _get_int(parser, "border", "width", int(DEFAULTS["border_width"]))))
    content_margin = _safe_margin(
        _get_int(parser, "font", "margin", int(DEFAULTS["content_margin"])),
        int(DEFAULTS["content_margin"]),
    )
    return _to_runtime(
        family,
        size,
        bold,
        colors,
        header_family,
        header_size,
        header_bold,
        header_colors,
        footer_family,
        footer_size,
        footer_bold,
        footer_colors,
        border_enabled,
        border_width,
        button_size=button_size,
        header_button_size=header_button_size,
        footer_button_size=footer_button_size,
        title_family=title_family,
        title_size=title_size,
        content_margin=content_margin,
    )


def _to_runtime(
    family: str,
    size: int,
    bold: int,
    colors: dict[str, tuple[int, int, int]],
    header_family: str,
    header_size: int,
    header_bold: int,
    header_colors: dict[str, tuple[int, int, int]],
    footer_family: str,
    footer_size: int,
    footer_bold: int,
    footer_colors: dict[str, tuple[int, int, int]],
    border_enabled: int,
    border_width: int,
    button_size: int | None = None,
    header_button_size: int | None = None,
    footer_button_size: int | None = None,
    title_family: str | None = None,
    title_size: int | None = None,
    content_margin: int | None = None,
) -> dict[str, Any]:
    button_size = _safe_size(button_size, size)
    header_button_size = _safe_size(header_button_size, header_size)
    footer_button_size = _safe_size(footer_button_size, footer_size)
    title_family = str(title_family or family).strip() or family
    title_size = _safe_size(title_size, int(DEFAULTS["title_font_size"]))
    content_margin = _safe_margin(content_margin, int(DEFAULTS["content_margin"]))
    data: dict[str, Any] = {
        "font_family": family,
        "font_size": size,
        "font_bold": bold,
        "font": font_tuple(family, size, bold),
        "header_font_family": header_family,
        "header_font_size": header_size,
        "header_font_bold": header_bold,
        "header_font": font_tuple(header_family, header_size, header_bold),
        "footer_font_family": footer_family,
        "footer_font_size": footer_size,
        "footer_font_bold": footer_bold,
        "footer_font": font_tuple(footer_family, footer_size, footer_bold),
        "button_font_size": button_size,
        "header_button_font_size": header_button_size,
        "footer_button_font_size": footer_button_size,
        "button_font": font_tuple(family, button_size, bold),
        "header_button_font": font_tuple(header_family, header_button_size, header_bold),
        "footer_button_font": font_tuple(footer_family, footer_button_size, footer_bold),
        "title_font_family": title_family,
        "title_font_size": title_size,
        "title_font": font_tuple(title_family, title_size, 0),
        "border_enabled": border_enabled,
        "border_width": border_width,
        "content_margin": content_margin,
    }
    for key, rgb in colors.items():
        _emit_color(data, key, rgb)
    for key, rgb in header_colors.items():
        _emit_color(data, f"header_{key}", rgb)
    for key, rgb in footer_colors.items():
        _emit_color(data, f"footer_{key}", rgb)
    return data


def default_design() -> dict[str, Any]:
    family = str(DEFAULTS["font_family"])
    size = int(DEFAULTS["font_size"])
    bold = int(DEFAULTS["font_bold"])
    header_family = str(DEFAULTS.get("header_font_family") or family)
    header_size = int(DEFAULTS.get("header_font_size") or size)
    header_bold = int(DEFAULTS.get("header_font_bold") or 0)
    footer_family = str(DEFAULTS.get("footer_font_family") or family)
    footer_size = int(DEFAULTS.get("footer_font_size") or size)
    footer_bold = int(DEFAULTS.get("footer_font_bold") or 0)
    colors = {key: DEFAULTS[key] for key in COLOR_KEYS}
    header_colors = {key: DEFAULTS.get(f"header_{key}", colors[key]) for key in REGION_COLOR_KEYS}
    footer_colors = {key: DEFAULTS.get(f"footer_{key}", colors[key]) for key in REGION_COLOR_KEYS}
    footer_colors["text_disabled"] = DEFAULTS.get("footer_text_disabled", footer_colors["text"])
    footer_colors["button_disabled"] = DEFAULTS.get("footer_button_disabled", footer_colors["button"])
    return _to_runtime(
        family,
        size,
        bold,
        colors,
        header_family,
        header_size,
        header_bold,
        header_colors,
        footer_family,
        footer_size,
        footer_bold,
        footer_colors,
        int(DEFAULTS["border_enabled"]),
        int(DEFAULTS["border_width"]),
        button_size=int(DEFAULTS["button_font_size"]),
        header_button_size=int(DEFAULTS["header_button_font_size"]),
        footer_button_size=int(DEFAULTS["footer_button_font_size"]),
        title_family=str(DEFAULTS["title_font_family"]),
        title_size=int(DEFAULTS["title_font_size"]),
        content_margin=int(DEFAULTS["content_margin"]),
    )


def design_colors(data: dict[str, Any], keys: tuple[str, ...] | None = None) -> dict[str, tuple[int, int, int]]:
    colors: dict[str, tuple[int, int, int]] = {}
    for key in keys or COLOR_KEYS:
        fallback = DEFAULTS[key] if key in DEFAULTS else DEFAULTS["background"]
        colors[key] = _color_from_data(data, key, fallback)
    return colors


def save_design(data: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    family = str(data.get("font_family") or DEFAULTS["font_family"]).strip() or str(DEFAULTS["font_family"])
    header_family = str(data.get("header_font_family") or family).strip() or family
    footer_family = str(data.get("footer_font_family") or family).strip() or family
    try:
        size = _clamp_size(int(data.get("font_size") or DEFAULTS["font_size"]))
    except (TypeError, ValueError):
        size = int(DEFAULTS["font_size"])
    try:
        header_size = _clamp_size(int(data.get("header_font_size") or size))
    except (TypeError, ValueError):
        header_size = size
    try:
        footer_size = _clamp_size(int(data.get("footer_font_size") or size))
    except (TypeError, ValueError):
        footer_size = size
    bold = _as_flag(data.get("font_bold"), 0)
    header_bold = _as_flag(data.get("header_font_bold"), bold)
    footer_bold = _as_flag(data.get("footer_font_bold"), bold)
    colors = design_colors(data, COLOR_KEYS)
    header_colors = {
        key: _color_from_data(data, f"header_{key}", colors[key]) for key in REGION_COLOR_KEYS
    }
    footer_colors = {
        key: _color_from_data(data, f"footer_{key}", colors[key]) for key in REGION_COLOR_KEYS
    }
    footer_colors["text_disabled"] = _color_from_data(
        data, "footer_text_disabled", footer_colors["text"]
    )
    footer_colors["button_disabled"] = _color_from_data(
        data, "footer_button_disabled", footer_colors["button"]
    )
    button_size = _safe_size(data.get("button_font_size"), size)
    header_button_size = _safe_size(data.get("header_button_font_size"), header_size)
    footer_button_size = _safe_size(data.get("footer_button_font_size"), footer_size)
    title_family = str(data.get("title_font_family") or family).strip() or family
    title_size = _safe_size(data.get("title_font_size"), int(DEFAULTS["title_font_size"]))
    content_margin = _safe_margin(data.get("content_margin"), int(DEFAULTS["content_margin"]))
    try:
        border_enabled = 0 if int(data.get("border_enabled", DEFAULTS["border_enabled"])) == 0 else 1
    except (TypeError, ValueError):
        border_enabled = 1
    try:
        border_width = int(data.get("border_width", DEFAULTS["border_width"]))
    except (TypeError, ValueError):
        border_width = 1
    border_width = max(0, min(8, border_width))
    lines = [
        "; kamishivy デザイン。色は R,G,B を 0〜255 の数値で保存する。",
        "; 中段（font / color）が基準。UI は design[\"background\"] などを参照する。",
        "; 上段は font_header / color_header、下段は font_footer / color_footer。",
        "",
        "[font]",
        "; 中段（基準）。UI が使うフォント。button_size はボタン専用。",
        "; margin は表示域の左右余白（px）。左右同じ値。",
        f"family = {family}",
        f"size = {size}",
        f"bold = {bold}",
        f"button_size = {button_size}",
        f"margin = {content_margin}",
        "",
        "[font_header]",
        "; 上段（ヘッダー）",
        f"family = {header_family}",
        f"size = {header_size}",
        f"bold = {header_bold}",
        f"button_size = {header_button_size}",
        "",
        "[font_footer]",
        "; 下段（次へ）",
        f"family = {footer_family}",
        f"size = {footer_size}",
        f"bold = {footer_bold}",
        f"button_size = {footer_button_size}",
        "",
        "[font_title]",
        "; 各 UI のタイトル",
        f"family = {title_family}",
        f"size = {title_size}",
        "",
        "[color]",
        "; 中段（基準）",
    ]
    for key in COLOR_KEYS:
        lines.append(f"{key} = {format_rgb(colors[key])}")
    lines.extend(["", "[color_header]", "; 上段（ヘッダー）"])
    for key in REGION_COLOR_KEYS:
        lines.append(f"{key} = {format_rgb(header_colors[key])}")
    lines.extend(["", "[color_footer]", "; 下段（次へ）。text_disabled / button_disabled は次へを押せる前の色。"])
    for key in FOOTER_COLOR_KEYS:
        lines.append(f"{key} = {format_rgb(footer_colors[key])}")
    lines.extend(
        [
            "",
            "[border]",
            "; 1 なら縁取りあり。0 ならなし。",
            f"enabled = {border_enabled}",
            f"width = {border_width}",
            "",
        ]
    )
    target = path or DESIGN_PATH
    target.write_text("\n".join(lines), encoding="utf-8")
    return _to_runtime(
        family,
        size,
        bold,
        colors,
        header_family,
        header_size,
        header_bold,
        header_colors,
        footer_family,
        footer_size,
        footer_bold,
        footer_colors,
        border_enabled,
        border_width,
        button_size=button_size,
        header_button_size=header_button_size,
        footer_button_size=footer_button_size,
        title_family=title_family,
        title_size=title_size,
        content_margin=content_margin,
    )


DISPLAY_PRESET_KEYS = (
    "fullscreen",
    "hide_close",
    "show_page",
    "next_size_mode",
    "next_width",
    "next_height",
    "next_align",
)


def save_design_preset(
    data: dict[str, Any],
    path: Path,
    display: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = save_design(data, path)
    if not display:
        return result
    extra = ["", "[display]", "; 表示のカスタマイズ（全画面・次へボタンなど）。"]
    for key in DISPLAY_PRESET_KEYS:
        if key not in display:
            continue
        extra.append(f"{key} = {display[key]}")
    extra.append("")
    text = path.read_text(encoding="utf-8").rstrip()
    path.write_text(text + "\n" + "\n".join(extra), encoding="utf-8")
    return result


def load_design_preset(path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    data = load_design(path)
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(path, encoding="utf-8")
    display: dict[str, str] = {}
    if parser.has_section("display"):
        for key in DISPLAY_PRESET_KEYS:
            if parser.has_option("display", key):
                display[key] = parser.get("display", key).strip()
    return data, display
