from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

# 受信番号。1〜9。comA は "comA"。
DATA = 1

# 画面の見出し。ここを変える。
LABEL_REGISTER = "登録"


class UI(BaseUI):
    def build(self) -> None:
        self._registered = False
        self._value_var = tk.StringVar(value="---")
        self.data_var = self._value_var

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        family = str(design.get("font_family") or "Yu Gothic UI")
        size = int(design.get("font_size") or 12)
        weight = ("bold",) if int(design.get("font_bold") or 0) else ()

        ttk.Label(
            frame,
            textvariable=self._value_var,
            font=(family, max(28, size + 36), *weight),
            anchor="center",
        ).grid(row=0, column=0, pady=(24, 16), sticky="ew")

        ttk.Button(frame, text=LABEL_REGISTER, command=self._on_register).grid(row=1, column=0, pady=16)
        self._refresh_value()

    def _refresh_value(self) -> None:
        value = get_data(DATA)
        self._value_var.set("---" if value is None or value == "" else str(value))

    def _on_register(self) -> None:
        self._registered = True
        self.ready = True
        write_log(
            {
                "データ読み込み番号": DATA,
                "value": get_data(DATA),
                "判定": "TRUE",
            }
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "データ読み込み番号": DATA,
            "value": get_data(DATA),
            "registered": self._registered,
            "判定": "TRUE" if self._registered else "FALSE",
        }
