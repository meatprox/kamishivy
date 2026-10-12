from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI


class UI(BaseUI):
    def build(self) -> None:
        self._vars: list[tk.BooleanVar] = []

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        items = ttk.Frame(frame)
        items.grid(row=0, column=0, pady=(12, 12))
        items.columnconfigure(1, weight=1)

        for index, text in enumerate(cui().texts):
            var = tk.BooleanVar(value=False)
            self._vars.append(var)
            ttk.Checkbutton(items, variable=var, command=self._sync).grid(
                row=index, column=0, sticky="nw", padx=(0, 10), pady=6
            )
            ttk.Label(items, text=text, wraplength=640, justify="left").grid(
                row=index, column=1, sticky="w", pady=6
            )

        self._sync()

    def _sync(self) -> None:
        self.ready = bool(self._vars) and all(bool(var.get()) for var in self._vars)

    def is_condition_met(self) -> bool:
        return bool(self._vars) and all(bool(var.get()) for var in self._vars)

    def get_state(self) -> dict[str, Any]:
        checked = [bool(var.get()) for var in self._vars]
        state: dict[str, Any] = {
            f"check.{index}": value for index, value in enumerate(checked)
        }
        state["判定"] = "TRUE" if self.is_condition_met() else "FALSE"
        return state
