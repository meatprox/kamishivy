from __future__ import annotations

import configparser
from datetime import datetime
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import ttk

from ui.base import BaseUI

# 画面の見出し。ここを変える。
LABEL_OPENING = "「{name}」を開いています"
LABEL_CHECK = "確認しました"


def _app_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _cui_path() -> Path:
    root = _app_root()
    parser = configparser.ConfigParser()
    parser.read(root / "config.ini", encoding="utf-8")
    raw = "cui.xlsx"
    if parser.has_section("cui"):
        raw = (parser.get("cui", "file", fallback="") or "").strip() or raw
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = root / path
    return path


def _mtime_text(path: Path) -> str:
    if not path.is_file():
        return "ファイルが見つかりません"
    stamp = datetime.fromtimestamp(path.stat().st_mtime)
    return stamp.strftime("%Y/%m/%d %H:%M:%S")


class UI(BaseUI):
    def build(self) -> None:
        path = _cui_path()
        self._cui_name = path.name
        self._mtime = _mtime_text(path)
        self._checked = tk.BooleanVar(value=False)
        self.ready = self._checked

        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        fg = str(design.get("text") or "#000000")
        body_font = design.get("font") or (family, size)

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        inner = ttk.Frame(frame)
        inner.grid(row=0, column=0)
        inner.columnconfigure(0, weight=1)

        ttk.Label(
            inner,
            text=LABEL_OPENING.format(name=self._cui_name),
            font=design.get("title_font"),
            foreground=str(design.get("title_text") or fg),
            anchor="center",
            justify="center",
        ).grid(row=0, column=0, pady=(24, 12), sticky="ew")

        ttk.Label(
            inner,
            text=self._mtime,
            font=body_font,
            foreground=fg,
            anchor="center",
            justify="center",
        ).grid(row=1, column=0, pady=(0, 24), sticky="ew")

        ttk.Checkbutton(
            inner,
            text=LABEL_CHECK,
            variable=self._checked,
        ).grid(row=2, column=0)

    def get_state(self) -> dict[str, Any]:
        checked = bool(self._checked.get())
        return {
            "checked": checked,
            "判定": "TRUE" if checked else "FALSE",
        }
