from __future__ import annotations

from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import ttk

from ui.base import BaseUI

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None  # type: ignore[assignment]
    ImageTk = None  # type: ignore[assignment]


class UI(BaseUI):
    def build(self) -> None:
        path, source, body = self._read_cui()
        if path is None:
            raise ValueError("画像のパスがありません")
        self._path = path
        self._body = body
        self._photo = None
        self._source = source
        self._stage_size = (0, 0)

        bg = str(design.get("background") or "#f0f0f0")
        fg = str(design.get("text") or "#000000")
        font = design.get("font") or (
            str(design.get("font_family") or "ＭＳ Ｐゴシック"),
            int(design.get("font_size") or 9),
        )

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self._frame = frame

        self._stage = tk.Frame(frame, bg=bg)
        self._stage.grid(row=0, column=0, sticky="nsew")
        self._image_label = tk.Label(self._stage, bg=bg, fg=fg, font=font, compound="center")
        self._image_label.pack(fill="both", expand=True, padx=8, pady=8)

        self._text_label = None
        if body:
            self._image_label.pack_configure(pady=(8, 4))
            self._text_label = tk.Label(
                frame,
                text=body,
                font=font,
                fg=fg,
                bg=bg,
                justify="left",
                anchor="nw",
                wraplength=1,
            )
            self._text_label.grid(row=1, column=0, sticky="ew", pady=(4, 12))
            frame.bind("<Configure>", self._on_frame_configure, add="+")
            frame.after_idle(self._apply_text_wrap)

        self._place_image()
        self._stage.bind("<Configure>", self._on_stage_configure)
        self.ready = True

    def _read_cui(self) -> tuple[Path | None, Any, str]:
        path: Path | None = None
        source = None
        lines: list[str] = []
        for row in cui().grid:
            parts: list[str] = []
            for cell in row:
                text = str(cell).strip()
                if not text:
                    continue
                info = file_path(text)
                if info is not None and info.kind == "image":
                    if path is None:
                        path = info.path
                        source = info.image
                    continue
                parts.append(text)
            if parts:
                lines.append(" ".join(parts))
        return path, source, "\n".join(lines)

    def _place_image(self) -> None:
        path = self._path
        if not path.is_file():
            self._image_label.config(image="", text=f"ファイルが見つかりません。\n{path}")
            return
        if self._source is None:
            self._image_label.config(image="", text=f"画像を開けません。\n{path.name}")
            return
        self._fit_image()

    def _on_stage_configure(self, event: tk.Event) -> None:
        if event.widget is not self._stage:
            return
        size = (max(1, event.width), max(1, event.height))
        if size == self._stage_size:
            return
        self._stage_size = size
        self._fit_image()

    def _on_frame_configure(self, event: tk.Event) -> None:
        if event.widget is not self._frame:
            return
        self._apply_text_wrap()

    def _apply_text_wrap(self) -> None:
        if self._text_label is None:
            return
        try:
            width = int(self._frame.winfo_width())
        except tk.TclError:
            return
        if width < 8:
            return
        try:
            current = str(self._text_label.cget("wraplength") or "0")
            wrap = max(1, width - 8)
            if int(float(current)) != wrap:
                self._text_label.configure(wraplength=wrap)
        except (tk.TclError, TypeError, ValueError):
            return

    def _fit_image(self) -> None:
        source = self._source
        if source is None:
            return
        if ImageTk is None or Image is None or isinstance(source, tk.PhotoImage):
            if isinstance(source, tk.PhotoImage):
                self._image_label.config(image=source, text="")
                self._photo = source
            return
        width, height = self._stage_size
        max_w = max(20, width - 16)
        max_h = max(20, height - 16)
        img_w, img_h = source.size
        if img_w < 1 or img_h < 1:
            return
        scale = min(max_w / img_w, max_h / img_h)
        size = (max(1, int(img_w * scale)), max(1, int(img_h * scale)))
        image = source
        if size != source.size:
            resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.NEAREST)
            image = source.resize(size, resample)
        photo = ImageTk.PhotoImage(image)
        self._image_label.config(image=photo, text="")
        self._photo = photo

