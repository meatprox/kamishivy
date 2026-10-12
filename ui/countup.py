from __future__ import annotations

import time
from typing import Any

import tkinter as tk
from tkinter import ttk

from ui.base import BaseUI

OVER_FG = "#c0392b"

# 画面の見出し。ここを変える。
LABEL_STOP = "停止"


class UI(BaseUI):
    def build(self) -> None:
        self._after = None
        self._done = False
        self._limit = self._read_cui()
        self._start = time.monotonic()
        self._elapsed_sec = 0
        self._shown = tk.StringVar(value=format_remain(0))

        bg = str(design.get("background") or "#f0f0f0")
        self._normal_fg = str(design.get("text") or "#000000")
        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        weight = ("bold",) if int(design.get("font_bold") or 0) else ()

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        self._time_label = tk.Label(
            frame,
            textvariable=self._shown,
            font=(family, max(36, size + 40), *weight),
            fg=self._normal_fg,
            bg=bg,
        )
        self._time_label.grid(row=0, column=0, pady=(24, 16), sticky="ew")

        ttk.Button(frame, text=LABEL_STOP, command=self._on_stop).grid(row=1, column=0, pady=16)
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

    def _now_elapsed(self) -> int:
        return max(0, int(time.monotonic() - self._start))

    def _apply_color(self, elapsed: int) -> None:
        over = self._limit is not None and elapsed > self._limit
        self._time_label.config(fg=OVER_FG if over else self._normal_fg)

    def _tick(self) -> None:
        if self._stopped or self._done:
            return
        elapsed = self._now_elapsed()
        self._elapsed_sec = elapsed
        self._shown.set(format_remain(elapsed))
        self._apply_color(elapsed)
        try:
            self._after = self.after(200, self._tick)
        except tk.TclError:
            self._after = None

    def _on_stop(self) -> None:
        if self._done:
            return
        elapsed = self._now_elapsed()
        self._elapsed_sec = elapsed
        self._shown.set(format_remain(elapsed))
        self._apply_color(elapsed)
        self._done = True
        self._stopped = True
        if self._after is not None:
            try:
                self.after_cancel(self._after)
            except tk.TclError:
                pass
            self._after = None
        payload: dict[str, Any] = {
            "elapsed": format_remain(elapsed),
        }
        if self._limit is not None:
            payload["over"] = elapsed > self._limit
        payload["判定"] = "TRUE"
        write_log(payload)
        self.ready = True

    def is_condition_met(self) -> bool:
        return self._done

    def get_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {
            "elapsed": format_remain(self._elapsed_sec),
        }
        if self._limit is not None:
            state["over"] = self._elapsed_sec > self._limit
        state["判定"] = "TRUE" if self._done else "FALSE"
        return state
