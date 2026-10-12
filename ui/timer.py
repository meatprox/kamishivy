from __future__ import annotations

import math
import time
from typing import Any

import tkinter as tk
from tkinter import ttk

from ui.base import BaseUI


class UI(BaseUI):
    def build(self) -> None:
        self._after = None
        self._done = False
        seconds = self._read_cui()
        if seconds is None:
            raise ValueError("設定時間がCUIから取得できませんでした")

        self._total = seconds
        self._end = time.monotonic() + seconds
        self._remain = tk.StringVar(value=format_remain(seconds))

        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        weight = ("bold",) if int(design.get("font_bold") or 0) else ()

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            textvariable=self._remain,
            font=(family, max(36, size + 40), *weight),
            anchor="center",
        ).grid(row=0, column=0, pady=(24, 16), sticky="ew")

        if seconds <= 0:
            self._done = True
            self.ready = True
        else:
            self._tick()

    def _read_cui(self) -> int | None:
        for row in cui().grid:
            for cell in row:
                text = str(cell).strip()
                if not text:
                    continue
                parsed = parse_seconds(text)
                if parsed is not None:
                    return parsed
        return None

    def _tick(self) -> None:
        if self._stopped:
            return
        left = max(0, math.ceil(self._end - time.monotonic()))
        self._remain.set(format_remain(left))
        if left <= 0:
            self._done = True
            self.ready = True
            return
        try:
            self._after = self.after(200, self._tick)
        except tk.TclError:
            self._after = None

    def is_condition_met(self) -> bool:
        return self._done

    def get_state(self) -> dict[str, Any]:
        return {
            "remain": self._remain.get() if hasattr(self, "_remain") else "",
            "判定": "TRUE" if self._done else "FALSE",
        }
