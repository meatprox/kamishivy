from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI


def _set_wraplength(widget, width: int) -> None:
    try:
        current = str(widget.cget("wraplength") or "0")
        if int(float(current)) != int(width):
            widget.configure(wraplength=int(width))
    except (tk.TclError, TypeError, ValueError):
        return


class UI(BaseUI):
    def build(self) -> None:
        self._body = self._read_text()

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        bg = str(design.get("background") or "#f0f0f0")
        fg = str(design.get("text") or "#000000")
        font = design.get("font") or (
            str(design.get("font_family") or "ＭＳ Ｐゴシック"),
            int(design.get("font_size") or 9),
        )

        self._label = tk.Label(
            frame,
            text=self._body,
            font=font,
            fg=fg,
            bg=bg,
            justify="left",
            anchor="nw",
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
        _set_wraplength(self._label, max(1, int(event.width) - 4))
