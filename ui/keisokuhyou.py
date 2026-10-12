from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

# 受信番号。1〜9。comA は "comA"。
DATA = 1

# 画面の見出し。ここを変える。
LABEL_REGISTER = "登録"
LABEL_ITEM = "項目"
LABEL_INPUT = "入力"
LABEL_TARGET = "目標値"
LABEL_TARE = "許容値"
LABEL_REMAIN = "残り"


class UI(BaseUI):
    def build(self) -> None:
        self._items = self._read_rows()
        self._vars: list[tk.StringVar] = []
        self._next_row = 0
        self._live = tk.StringVar(value="---")
        self.data_var = self._live

        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        weight = ("bold",) if int(design.get("font_bold") or 0) else ()
        entered_font = (family, max(24, size + 16), *weight)

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            textvariable=self._live,
            font=(family, max(28, size + 36), *weight),
            anchor="center",
        ).grid(row=0, column=0, pady=(20, 8), sticky="ew")
        ttk.Button(frame, text=LABEL_REGISTER, command=self._on_register).grid(row=1, column=0, pady=12)

        bg = str(design.get("background") or "#f0f0f0")
        frame.rowconfigure(2, weight=1)
        table = self.scroll_area(frame, background=bg, row=2, column=0, sticky="nsew", padx=16, pady=(8, 8))
        show_target = any(item["target"] is not None for item in self._items)
        self._show_target = show_target
        headers = (LABEL_ITEM, LABEL_INPUT, LABEL_TARGET, LABEL_TARE) if show_target else (LABEL_ITEM, LABEL_INPUT)
        table.columnconfigure(0, weight=0)
        for col in range(1, len(headers)):
            table.columnconfigure(col, weight=1)

        for col, text in enumerate(headers):
            if col == 0:
                head = ttk.Label(table, text=text, anchor="w")
                head.grid(row=0, column=col, padx=8, pady=(0, 8), sticky="w")
            else:
                head = ttk.Label(table, text=text, anchor="center")
                head.grid(row=0, column=col, padx=8, pady=(0, 8), sticky="ew")

        self._row_widgets: list[ttk.Label] = []
        for index, item in enumerate(self._items):
            grid_row = index + 1
            name = ttk.Label(table, text=item["label"], anchor="w", justify="left")
            name.grid(row=grid_row, column=0, padx=8, pady=6, sticky="w")
            var = tk.StringVar(value="")
            self._vars.append(var)
            value = ttk.Label(table, textvariable=var, anchor="center")
            value.grid(row=grid_row, column=1, padx=8, pady=6, sticky="ew")
            self._row_widgets.append(value)
            if show_target:
                target_text = "" if item["target"] is None else f"{item['target']:g}"
                tare_text = "" if item["target"] is None else f"{item['tare']:g}"
                tlab = ttk.Label(table, text=target_text, anchor="center")
                tlab.grid(row=grid_row, column=2, padx=8, pady=6, sticky="ew")
                alab = ttk.Label(table, text=tare_text, anchor="center")
                alab.grid(row=grid_row, column=3, padx=8, pady=6, sticky="ew")

        self._remain = tk.StringVar(value="")
        self._remain_label = ttk.Label(
            frame,
            textvariable=self._remain,
            font=entered_font,
            anchor="center",
        )
        if show_target:
            self._remain_label.grid(row=3, column=0, pady=(4, 16), sticky="ew")
        self._refresh_remain()
        self._refresh_live()

    def _read_rows(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in cui().grid:
            cells = [str(cell).strip() for cell in row]
            if not any(cells):
                continue
            label = cells[0] if cells else ""
            if not label or "=" in label:
                continue
            target = parse_number(cells[1]) if len(cells) > 1 else None
            tare_raw = parse_number(cells[2]) if len(cells) > 2 else None
            tare = abs(tare_raw) if tare_raw is not None else 0.0
            items.append({"label": label, "target": target, "tare": tare})
        if not items:
            raise ValueError("表の行がCUIから取得できませんでした")
        return items

    def _refresh_live(self) -> None:
        value = get_data(DATA)
        self._live.set("---" if value is None or value == "" else str(value))

    def _refresh_remain(self) -> None:
        if not getattr(self, "_show_target", False):
            self._remain.set("")
            return
        target_sum = 0.0
        entered_sum = 0.0
        any_target = False
        for index, item in enumerate(self._items):
            target = item["target"]
            if target is None:
                continue
            any_target = True
            target_sum += float(target)
            number = parse_number(self._vars[index].get()) if index < len(self._vars) else None
            if number is not None:
                entered_sum += number
        if not any_target:
            self._remain.set("")
            return
        self._remain.set(f"{LABEL_REMAIN}  {target_sum - entered_sum:g}")

    def _on_register(self) -> None:
        if self._next_row >= len(self._vars):
            return
        live = get_data(DATA)
        if live is None or live == "":
            return
        index = self._next_row
        item = self._items[index]
        self._vars[index].set(str(live))
        self._next_row += 1
        self._refresh_remain()
        widget = self._row_widgets[index] if index < len(self._row_widgets) else None
        if widget is not None:
            self.after_idle(lambda w=widget: self.see(w))
        ok = self.is_condition_met()
        write_log(
            {
                "データ読み込み番号": DATA,
                "index": index,
                "value": str(live),
                "判定": "TRUE" if ok else "FALSE",
            }
        )
        self.ready = ok

    def _row_ok(self, index: int) -> bool:
        text = str(self._vars[index].get() or "").strip()
        if not text:
            return False
        item = self._items[index]
        target = item["target"]
        if target is None:
            return True
        value = parse_number(text)
        if value is None:
            return False
        tare = float(item["tare"])
        return target - tare <= value <= target + tare

    def is_condition_met(self) -> bool:
        return bool(self._vars) and all(self._row_ok(index) for index in range(len(self._vars)))

    def log_headings(self) -> list[str]:
        heads = ["データ読み込み番号", LABEL_ITEM, LABEL_INPUT]
        if getattr(self, "_show_target", False):
            heads.extend([LABEL_TARGET, LABEL_TARE])
        return heads

    def get_state(self) -> list[list[Any]]:
        rows: list[list[Any]] = []
        show_target = getattr(self, "_show_target", False)
        for index, item in enumerate(self._items):
            row: list[Any] = [
                DATA,
                item["label"],
                self._vars[index].get() if index < len(self._vars) else "",
            ]
            if show_target:
                row.append("" if item["target"] is None else item["target"])
                row.append("" if item["target"] is None else item["tare"])
            rows.append(row)
        return rows
