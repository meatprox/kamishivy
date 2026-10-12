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
LABEL_REGISTER = "登録"
LABEL_GROSS = "全体重量"
LABEL_FUTAI = "風袋"
LABEL_NET = "投入値"
HEADINGS = (LABEL_GROSS, LABEL_FUTAI, LABEL_NET)


class UI(BaseUI):
    def build(self) -> None:
        info = cui()
        self._target = info.target
        self._tare = info.tare
        self._gross: float | None = None
        self._futai: float | None = None
        self._live = tk.StringVar(value="---")
        self.data_var = self._live
        self._gross_text = tk.StringVar(value="---")
        self._futai_text = tk.StringVar(value="---")
        self._net_text = tk.StringVar(value="---")

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

        ttk.Button(frame, text=LABEL_REGISTER, command=self._on_register).grid(row=row, column=0, pady=16)
        row += 1

        table = ttk.Frame(frame)
        table.grid(row=row, column=0, sticky="n", padx=16, pady=(8, 16))
        for col in range(3):
            table.columnconfigure(col, weight=1)

        for col, heading in enumerate((LABEL_GROSS, LABEL_FUTAI, LABEL_NET)):
            ttk.Label(table, text=heading, anchor="center").grid(
                row=0, column=col, padx=12, pady=(0, 8), sticky="ew"
            )

        values = (self._gross_text, self._futai_text, self._net_text)
        for col, var in enumerate(values):
            ttk.Label(table, textvariable=var, font=entered_font, anchor="center").grid(
                row=1, column=col, padx=12, pady=6, sticky="ew"
            )

        self._refresh_live()

    def _fmt(self, value: float | None) -> str:
        return "---" if value is None else f"{value:g}"

    def _refresh_shown(self) -> None:
        self._gross_text.set(self._fmt(self._gross))
        self._futai_text.set(self._fmt(self._futai))
        self._net_text.set(self._fmt(self._net()))

    def _refresh_live(self) -> None:
        value = get_data(DATA)
        self._live.set("---" if value is None or value == "" else str(value))

    def _net(self) -> float | None:
        if self._gross is None or self._futai is None:
            return None
        return self._gross - self._futai

    def _values(self) -> list[float] | None:
        net = self._net()
        if self._gross is None or self._futai is None or net is None:
            return None
        return [self._gross, self._futai, net]

    def _on_register(self) -> None:
        live = get_data(DATA)
        if live is None or live == "":
            return
        number = parse_number(str(live))
        if number is None:
            return
        if self._gross is None:
            self._gross = number
        else:
            self._futai = number
        self._refresh_shown()
        values = self._values()
        if values is not None:
            write_log(values)
        else:
            write_log(
                {
                    "データ読み込み番号": DATA,
                    "判定": "FALSE",
                }
            )

    def is_condition_met(self) -> bool:
        values = self._values()
        if values is None:
            return False
        if self._target is None:
            return True
        net = values[2]
        return self._target - self._tare <= net <= self._target + self._tare

    def get_state(self) -> list[float] | dict[str, Any]:
        values = self._values()
        if values is None:
            return {
                "データ読み込み番号": DATA,
                "判定": "FALSE",
            }
        return values
