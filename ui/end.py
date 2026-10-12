from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

# 画面の見出し。ここを変える。
LABEL_EXIT = "終了"
NEXT_LABEL = LABEL_EXIT
NEXT_EXITS = True


class UI(BaseUI):
    def build(self) -> None:
        self._body = self._read_text()

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        bg = str(design.get("background") or "#f0f0f0")
        self._label = tk.Label(
            frame,
            text=self._body,
            font=design.get("title_font"),
            fg=str(design.get("title_text") or design.get("text") or "#000000"),
            bg=bg,
            justify="center",
            anchor="center",
            wraplength=1,
        )
        self._label.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)
        self._label.bind("<Configure>", self._on_resize)
        self.ready = True

    def _read_text(self) -> str:
        lines: list[str] = []
        for row in cui().grid:
            parts = [str(cell).strip() for cell in row if str(cell).strip()]
            if parts:
                lines.append(" ".join(parts))
        return "\n".join(lines)

    def _on_resize(self, event: tk.Event) -> None:
        try:
            current = str(self._label.cget("wraplength") or "0")
            width = max(1, int(event.width) - 4)
            if int(float(current)) != width:
                self._label.configure(wraplength=width)
        except (tk.TclError, TypeError, ValueError):
            return
