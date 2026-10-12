from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

# 受信番号。1〜9。comA は "comA"。
DATA = 1

# 画面の見出し。ここを変える。
LABEL_TARGET = "目標値"
LABEL_TARE = "許容幅"
LABEL_LIVE = "入力値"
LABEL_SAVED = "登録値"
LABEL_REGISTER = "登録"


class UI(BaseUI):
    def build(self) -> None:
        info = cui()
        self._target = info.target
        self._tare = info.tare
        self._live = tk.StringVar(value="---")
        self.data_var = self._live
        self._value = tk.StringVar(value="---")

        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        weight = ("bold",) if int(design.get("font_bold") or 0) else ()
        entered_font = (family, max(24, size + 16), *weight)

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        row = 0
        if self._target is not None:
            ttk.Label(
                frame,
                text=f"{LABEL_TARGET}  {self._target:g}　　{LABEL_TARE}  {self._tare:g}",
                anchor="center",
            ).grid(row=row, column=0, pady=(0, 12), sticky="ew")
            row += 1

        ttk.Label(frame, text=LABEL_LIVE, anchor="center").grid(row=row, column=0, pady=(16, 0), sticky="ew")
        row += 1
        ttk.Label(
            frame,
            textvariable=self._live,
            font=(family, max(28, size + 36), *weight),
            anchor="center",
        ).grid(row=row, column=0, pady=(4, 8), sticky="ew")
        row += 1

        ttk.Label(frame, text=LABEL_SAVED, anchor="center").grid(row=row, column=0, pady=(8, 0), sticky="ew")
        row += 1
        ttk.Label(
            frame,
            textvariable=self._value,
            font=entered_font,
            anchor="center",
        ).grid(row=row, column=0, pady=(4, 8), sticky="ew")
        row += 1

        ttk.Button(frame, text=LABEL_REGISTER, command=self._on_register).grid(row=row, column=0, pady=16)
        self._refresh_live()

    def _refresh_live(self) -> None:
        value = get_data(DATA)
        self._live.set("---" if value is None or value == "" else str(value))

    def _on_register(self) -> None:
        live = get_data(DATA)
        if live is None or live == "":
            return
        self._value.set(str(live))
        ok = self.is_condition_met()
        write_log(
            {
                "データ読み込み番号": DATA,
                "value": str(live),
                "判定": "TRUE" if ok else "FALSE",
            }
        )

    def _entered(self) -> str:
        text = str(self._value.get() or "").strip()
        if text in ("", "---"):
            return ""
        return text

    def is_condition_met(self) -> bool:
        text = self._entered()
        if not text:
            return False
        if self._target is None:
            return True
        value = parse_number(text)
        if value is None:
            return False
        return self._target - self._tare <= value <= self._target + self._tare

    def get_state(self) -> dict[str, Any]:
        return {
            "データ読み込み番号": DATA,
            "value": self._entered(),
            "判定": "TRUE" if self.is_condition_met() else "FALSE",
        }
