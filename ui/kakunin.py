from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

# 画面の見出し。ここを変える。
LABEL_CHECK = "確認しました"


class UI(BaseUI):
    def build(self) -> None:
        self._checked = tk.BooleanVar(value=False)
        self.ready = self._checked

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        ttk.Checkbutton(
            frame,
            text=LABEL_CHECK,
            variable=self._checked,
        ).grid(row=0, column=0, pady=24)

    def get_state(self) -> dict[str, Any]:
        checked = bool(self._checked.get())
        return {
            "checked": checked,
            "判定": "TRUE" if checked else "FALSE",
        }
