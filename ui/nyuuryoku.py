from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

# 画面の見出し。ここを変える。タイトルが空のときに使う。
LABEL_PROMPT = "入力してください"


class UI(BaseUI):
    def build(self) -> None:
        has_title = bool(str(cui().title or "").strip())

        fg = str(design.get("text") or "#000000")
        font = design.get("font") or (
            str(design.get("font_family") or "ＭＳ Ｐゴシック"),
            int(design.get("font_size") or 9),
        )
        textbox_bg = str(design.get("textbox") or "#ffffff")

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        text_row = 0
        if not has_title:
            frame.rowconfigure(1, weight=1)
            ttk.Label(
                frame,
                text=LABEL_PROMPT,
                font=design.get("title_font"),
                foreground=str(design.get("title_text") or fg),
                anchor="center",
                justify="center",
            ).grid(row=0, column=0, pady=(16, 12), padx=16, sticky="ew")
            text_row = 1
        else:
            frame.rowconfigure(0, weight=1)

        self._text = tk.Text(
            frame,
            font=font,
            fg=fg,
            bg=textbox_bg,
            insertbackground=fg,
            wrap="word",
            height=8,
            relief="solid",
            bd=1,
            padx=8,
            pady=8,
        )
        self._text.grid(row=text_row, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self._text.bind("<KeyRelease>", lambda _e: self._sync())
        self._text.bind("<<Paste>>", lambda _e: self.after_idle(self._sync))
        self.after_idle(self._focus_text)
        self._sync()

    def _focus_text(self) -> None:
        try:
            self._text.focus_set()
        except tk.TclError:
            return

    def _content(self) -> str:
        return self._text.get("1.0", "end-1c")

    def _sync(self) -> None:
        self.ready = bool(self._content().strip())

    def is_condition_met(self) -> bool:
        return bool(self._content().strip())

    def get_state(self) -> dict[str, Any]:
        return {
            "text": self._content(),
            "判定": "TRUE" if self.is_condition_met() else "FALSE",
        }
