from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

RED = "#e00000"
BLINK_MS = 500

# 画面の見出し。ここを変える。
LABEL_CHECK = "確認しました"


class UI(BaseUI):
    def build(self) -> None:
        self._body = self._read_text()
        if not self._body:
            raise ValueError("警告文がCUIから取得できませんでした")

        self._after = None
        self._on = True
        self._bg = str(design.get("background") or "#f0f0f0")

        family = str(design.get("title_font_family") or design.get("font_family") or "ＭＳ Ｐゴシック")
        try:
            size = int(design.get("title_font_size") or 20)
        except (TypeError, ValueError):
            size = 20
        font = design.get("title_font") if isinstance(design.get("title_font"), tuple) else (family, size)

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self._frame = frame

        inner = ttk.Frame(frame)
        inner.grid(row=0, column=0)
        inner.columnconfigure(0, weight=1)

        self._label = tk.Label(
            inner,
            text=self._body,
            font=font,
            fg=RED,
            bg=self._bg,
            justify="center",
            anchor="center",
            wraplength=1,
        )
        self._label.grid(row=0, column=0, padx=16, pady=(12, 16))

        self._checked = tk.BooleanVar(value=False)
        self.ready = self._checked
        ttk.Checkbutton(
            inner,
            text=LABEL_CHECK,
            variable=self._checked,
        ).grid(row=1, column=0)

        frame.bind("<Configure>", self._on_resize)
        self._blink()

    def _read_text(self) -> str:
        lines: list[str] = []
        for row in cui().grid:
            parts = [str(cell).strip() for cell in row if str(cell).strip()]
            if parts:
                lines.append(" ".join(parts))
        return "\n".join(lines)

    def _on_resize(self, event: tk.Event) -> None:
        if event.widget is not self._frame:
            return
        width = max(1, int(event.width) - 32)
        try:
            current = str(self._label.cget("wraplength") or "0")
            if int(float(current)) != width:
                self._label.configure(wraplength=width)
        except (tk.TclError, TypeError, ValueError):
            return

    def _blink(self) -> None:
        if self._stopped:
            return
        self._on = not self._on
        try:
            self._label.configure(fg=RED if self._on else self._bg)
        except tk.TclError:
            return
        self._after = self.after(BLINK_MS, self._blink)

    def get_state(self) -> dict[str, Any]:
        checked = bool(self._checked.get())
        return {
            "checked": checked,
            "判定": "TRUE" if checked else "FALSE",
        }
