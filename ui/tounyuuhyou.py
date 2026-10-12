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
LABEL_TOTAL = "累計"
LABEL_REMAIN = "残り"
HEADINGS = (LABEL_GROSS, LABEL_FUTAI, LABEL_NET, LABEL_TOTAL)


class UI(BaseUI):
    def build(self) -> None:
        info = cui()
        self._target = info.target
        self._tare = info.tare
        self._rows: list[list[float]] = []
        self._pending_gross: float | None = None
        self._live = tk.StringVar(value="---")
        self.data_var = self._live

        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        weight = ("bold",) if int(design.get("font_bold") or 0) else ()
        self._cell_font = (family, max(16, size + 8), *weight)
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

        bg = str(design.get("background") or "#f0f0f0")
        frame.rowconfigure(row, weight=1)
        self._table = self.scroll_area(frame, background=bg, row=row, column=0, sticky="nsew", padx=16, pady=(8, 8))
        for col in range(4):
            self._table.columnconfigure(col, weight=1)
        self._headers = (LABEL_GROSS, LABEL_FUTAI, LABEL_NET, LABEL_TOTAL)
        row += 1

        self._remain = tk.StringVar(value="")
        self._remain_label = ttk.Label(
            frame,
            textvariable=self._remain,
            font=entered_font,
            anchor="center",
        )
        if self._target is not None:
            self._remain_label.grid(row=row, column=0, pady=(4, 16), sticky="ew")

        self._refresh_table()
        self._refresh_remain()
        self._refresh_live()

    def _fmt(self, value: float | None) -> str:
        return "---" if value is None else f"{value:g}"

    def _display_rows(self) -> list[list[float | None]]:
        rows: list[list[float | None]] = [list(row) for row in self._rows]
        if self._pending_gross is not None:
            rows.append([self._pending_gross, None, None, None])
        return rows

    def _refresh_table(self) -> None:
        for child in self._table.winfo_children():
            child.destroy()
        for col, heading in enumerate(self._headers):
            label = ttk.Label(self._table, text=heading, anchor="center")
            label.grid(row=0, column=col, padx=12, pady=(0, 8), sticky="ew")
        last = None
        for row_index, row in enumerate(self._display_rows(), start=1):
            for col, value in enumerate(row):
                last = ttk.Label(
                    self._table,
                    text=self._fmt(value),
                    font=self._cell_font,
                    anchor="center",
                )
                last.grid(row=row_index, column=col, padx=12, pady=6, sticky="ew")
        if last is None:
            return
        self.after_idle(self.see)
        self.after(1, self.see)

    def _refresh_remain(self) -> None:
        if self._target is None:
            self._remain.set("")
            return
        used = self._total() or 0.0
        self._remain.set(f"{LABEL_REMAIN}  {self._target - used:g}")

    def _refresh_live(self) -> None:
        value = get_data(DATA)
        self._live.set("---" if value is None or value == "" else str(value))

    def _total(self) -> float | None:
        if not self._rows:
            return None
        return self._rows[-1][3]

    def _values(self) -> list[list[float]] | None:
        if not self._rows:
            return None
        return [list(row) for row in self._rows]

    def _on_register(self) -> None:
        live = get_data(DATA)
        if live is None or live == "":
            return
        number = parse_number(str(live))
        if number is None:
            return
        if self._pending_gross is None:
            self._pending_gross = number
        else:
            net = self._pending_gross - number
            total = (self._total() or 0.0) + net
            self._rows.append([self._pending_gross, number, net, total])
            self._pending_gross = None
        self._refresh_table()
        self._refresh_remain()
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
        self.ready = self.is_condition_met()

    def is_condition_met(self) -> bool:
        total = self._total()
        if total is None:
            return False
        if self._target is None:
            return True
        return self._target - self._tare <= total <= self._target + self._tare

    def get_state(self) -> list[list[float]] | dict[str, Any]:
        values = self._values()
        if values is None:
            return {
                "データ読み込み番号": DATA,
                "判定": "FALSE",
            }
        return values
