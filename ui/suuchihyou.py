from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

# 画面の見出し。ここを変える。
LABEL_ITEM = "項目"
LABEL_INPUT = "入力"
LABEL_TARGET = "目標値"
LABEL_TARE = "許容値"


class UI(BaseUI):
    def build(self) -> None:
        self._items = self._read_rows()
        self._vars: list[tk.StringVar] = []
        self._entries: list[tk.Entry] = []
        self._active: int | None = None

        fg = str(design.get("text") or "#000000")
        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        entry_font = (family, max(12, size + 4))
        textbox_bg = str(design.get("textbox") or "#ffffff")

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        inner = ttk.Frame(frame)
        inner.grid(row=0, column=0)

        self._pad = keypad(inner, self._on_key)
        self._pad.grid(row=0, column=0, padx=(16, 24), pady=(16, 8), sticky="n")

        table = ttk.Frame(inner)
        table.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky="n")
        self._table = table
        show_target = any(item["target"] is not None for item in self._items)
        self._show_target = show_target
        headers = (LABEL_ITEM, LABEL_INPUT, LABEL_TARGET, LABEL_TARE) if show_target else (LABEL_ITEM, LABEL_INPUT)
        for col in range(len(headers)):
            table.columnconfigure(col, weight=1)

        for col, text in enumerate(headers):
            ttk.Label(table, text=text, anchor="center").grid(row=0, column=col, padx=8, pady=(0, 8), sticky="ew")

        for index, item in enumerate(self._items):
            grid_row = index + 1
            ttk.Label(table, text=item["label"], anchor="w", justify="left").grid(
                row=grid_row, column=0, padx=8, pady=6, sticky="w"
            )
            var = tk.StringVar(value="")
            var.trace_add("write", lambda *_: self._sync())
            self._vars.append(var)
            entry = tk.Entry(
                table,
                textvariable=var,
                font=entry_font,
                fg=fg,
                bg=textbox_bg,
                insertbackground=fg,
                justify="center",
                width=12,
                relief="solid",
                bd=1,
            )
            entry.grid(row=grid_row, column=1, padx=8, pady=6, ipady=4, sticky="ew")
            entry.bind("<FocusIn>", lambda e, i=index: self._on_focus(i))
            entry.bind("<KeyRelease>", lambda _e: self._sync())
            self._entries.append(entry)

            if show_target:
                target_text = "" if item["target"] is None else f"{item['target']:g}"
                tare_text = "" if item["target"] is None else f"{item['tare']:g}"
                ttk.Label(table, text=target_text, anchor="center").grid(
                    row=grid_row, column=2, padx=8, pady=6, sticky="ew"
                )
                ttk.Label(table, text=tare_text, anchor="center").grid(
                    row=grid_row, column=3, padx=8, pady=6, sticky="ew"
                )

        if self._entries:
            self._active = 0
        self._sync()

    def _read_rows(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in cui().grid:
            cells = [str(cell).strip() for cell in row]
            if not any(cells):
                continue
            label = cells[0] if cells else ""
            if not label:
                raise ValueError("項目名がCUIから取得できませんでした")
            target = parse_number(cells[1]) if len(cells) > 1 else None
            tare_raw = parse_number(cells[2]) if len(cells) > 2 else None
            tare = abs(tare_raw) if tare_raw is not None else 0.0
            items.append({"label": label, "target": target, "tare": tare})
        if not items:
            raise ValueError("表の行がCUIから取得できませんでした")
        return items

    def _on_focus(self, index: int) -> None:
        self._active = index

    def _on_key(self, key: str) -> None:
        if self._active is None:
            return
        var = self._vars[self._active]
        entry = self._entries[self._active]
        if key == "⏎":
            nxt = self._active + 1
            if nxt < len(self._entries):
                self._active = nxt
                self._entries[nxt].focus_set()
            self._sync()
            return
        next_text = keypad.apply(var.get(), key)
        if next_text is None:
            return
        var.set(next_text)
        entry.icursor("end")
        entry.focus_set()
        self._sync()

    def _row_ok(self, index: int) -> bool:
        value = parse_number(self._vars[index].get())
        if value is None:
            return False
        item = self._items[index]
        target = item["target"]
        if target is None:
            return True
        tare = float(item["tare"])
        return target - tare <= value <= target + tare

    def _sync(self) -> None:
        self.ready = self.is_condition_met()

    def is_condition_met(self) -> bool:
        return bool(self._vars) and all(self._row_ok(index) for index in range(len(self._vars)))

    def log_headings(self) -> list[str]:
        if getattr(self, "_show_target", False):
            return [LABEL_ITEM, LABEL_INPUT, LABEL_TARGET, LABEL_TARE]
        return [LABEL_ITEM, LABEL_INPUT]

    def get_state(self) -> list[list[Any]]:
        rows: list[list[Any]] = []
        show_target = getattr(self, "_show_target", False)
        for index, item in enumerate(self._items):
            row: list[Any] = [item["label"], self._vars[index].get() if index < len(self._vars) else ""]
            if show_target:
                row.append("" if item["target"] is None else item["target"])
                row.append("" if item["target"] is None else item["tare"])
            rows.append(row)
        return rows
