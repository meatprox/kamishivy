from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

# 画面の見出し。ここを変える。
LABEL_TARGET = "目標値"
LABEL_TARE = "許容幅"


class UI(BaseUI):
    def build(self) -> None:
        info = cui()
        self._target = info.target
        self._tare = info.tare
        self._value = tk.StringVar(value="")
        self._value.trace_add("write", lambda *_: self._sync())

        fg = str(design.get("text") or "#000000")
        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        entry_font = (family, max(24, size + 16))
        textbox_bg = str(design.get("textbox") or "#ffffff")

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        inner = ttk.Frame(frame)
        inner.grid(row=0, column=0)

        self._pad = keypad(inner, self._on_key)
        self._pad.grid(row=0, column=0, padx=(0, 24), sticky="n")

        fields = ttk.Frame(inner)
        fields.grid(row=0, column=1, sticky="n")

        row = 0
        if self._target is not None:
            ttk.Label(
                fields,
                text=f"{LABEL_TARGET}  {self._target:g}　　{LABEL_TARE}  {self._tare:g}",
                anchor="center",
            ).grid(row=row, column=0, pady=(0, 12), sticky="ew")
            row += 1

        self._entry = tk.Entry(
            fields,
            textvariable=self._value,
            font=entry_font,
            fg=fg,
            bg=textbox_bg,
            insertbackground=fg,
            justify="center",
            width=12,
            relief="solid",
            bd=1,
        )
        self._entry.grid(row=row, column=0, pady=(8, 12), ipady=8)

        self._entry.bind("<KeyRelease>", lambda _e: self._sync())
        self._sync()

    def _on_key(self, key: str) -> None:
        if key == "⏎":
            self._entry.focus_set()
            self._sync()
            return
        next_text = keypad.apply(self._value.get(), key)
        if next_text is None:
            return
        self._value.set(next_text)
        self._entry.icursor("end")
        self._entry.focus_set()
        self._sync()

    def _current_value(self) -> float | None:
        return parse_number(self._value.get())

    def _sync(self) -> None:
        self.ready = self.is_condition_met()

    def is_condition_met(self) -> bool:
        value = self._current_value()
        if value is None:
            return False
        if self._target is None:
            return True
        return self._target - self._tare <= value <= self._target + self._tare

    def get_state(self) -> dict[str, Any]:
        return {
            "value": self._value.get(),
            "判定": "TRUE" if self.is_condition_met() else "FALSE",
        }
