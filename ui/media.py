from __future__ import annotations

from typing import Any

import tkinter as tk
from tkinter import ttk

from ui.base import BaseUI

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None  # type: ignore[assignment]
    ImageTk = None  # type: ignore[assignment]

try:
    import cv2
except ImportError:
    cv2 = None


class UI(BaseUI):
    def build(self) -> None:
        self._stopped = False
        self._after = None
        self._photos: list[Any] = []
        self._videos: list[dict[str, Any]] = []
        self._images: list[dict[str, Any]] = []
        self._stage_size = (0, 0)

        items = self._read_cui()
        if not items:
            raise ValueError("画像または動画のパスがありません")

        bg = str(design.get("background") or "#f0f0f0")
        fg = str(design.get("text") or "#000000")
        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self._frame = frame

        stage = tk.Frame(frame, bg=bg)
        stage.grid(row=0, column=0, sticky="nsew")
        self._stage = stage
        count = len(items)
        for index, info in enumerate(items):
            stage.rowconfigure(index, weight=1)
            stage.columnconfigure(0, weight=1)
            holder = tk.Frame(stage, bg=bg)
            holder.grid(row=index, column=0, sticky="nsew", padx=8, pady=8)
            label = tk.Label(holder, bg=bg, fg=fg, font=(family, size), compound="center")
            label.pack(fill="both", expand=True)
            self._add_item(info, label, count)

        stage.bind("<Configure>", self._on_stage_configure)
        self.ready = True
        self.bind("<Destroy>", self._release, add="+")
        if self._videos:
            self._tick_video()

    def _read_cui(self) -> list[Any]:
        items: list[Any] = []
        for row in cui().grid:
            for cell in row:
                text = str(cell).strip()
                if not text:
                    continue
                info = file_path(text)
                if info is not None:
                    items.append(info)
        return items

    def _add_item(self, info, label: tk.Label, count: int) -> None:
        path = info.path
        if not path.is_file():
            label.config(text=f"ファイルが見つかりません。\n{path}")
            return
        if info.kind == "video":
            if cv2 is None:
                label.config(text=f"動画を表示できません。\n{path.name}")
                return
            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                label.config(text=f"動画を開けません。\n{path.name}")
                return
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0) or 24.0
            self._videos.append(
                {
                    "path": path,
                    "label": label,
                    "cap": cap,
                    "delay": max(10, int(1000 / fps)),
                    "share": count,
                }
            )
            return
        image = info.image
        if image is None:
            label.config(text=f"画像を開けません。\n{path.name}")
            return
        self._images.append({"path": path, "label": label, "image": image, "share": count})

    def _on_stage_configure(self, event: tk.Event) -> None:
        if event.widget is not self._stage:
            return
        size = (max(1, event.width), max(1, event.height))
        if size == self._stage_size:
            return
        self._stage_size = size
        self._fit_images()

    def _slot_box(self, share: int) -> tuple[int, int]:
        width, height = self._stage_size
        if width < 20 or height < 20:
            return (400, 300)
        if share < 1:
            share = 1
        return (max(20, width - 16), max(20, (height // share) - 16))

    def _fit_images(self) -> None:
        kept: list[Any] = []
        if ImageTk is None:
            for item in self._images:
                image = item["image"]
                if isinstance(image, tk.PhotoImage):
                    item["label"].config(image=image, text="")
                    kept.append(image)
            self._photos = kept
            return
        for item in self._images:
            box = self._slot_box(int(item["share"]))
            photo = self._to_photo(item["image"], box)
            if photo is None:
                continue
            item["label"].config(image=photo, text="")
            item["photo"] = photo
            kept.append(photo)
        self._photos = kept

    def _to_photo(self, source, box: tuple[int, int]):
        if Image is None or ImageTk is None:
            return None
        if isinstance(source, tk.PhotoImage):
            return source
        image = source
        max_w, max_h = box
        width, height = image.size
        if width < 1 or height < 1:
            return None
        scale = min(max_w / width, max_h / height)
        size = (max(1, int(width * scale)), max(1, int(height * scale)))
        if size != image.size:
            resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.NEAREST)
            image = image.resize(size, resample)
        return ImageTk.PhotoImage(image)

    def _tick_video(self) -> None:
        if self._stopped:
            return
        delay = 33
        for item in self._videos:
            delay = min(delay, int(item["delay"]))
            cap = item["cap"]
            ok, frame = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = cap.read()
                if not ok:
                    continue
            box = self._slot_box(int(item["share"]))
            photo = self._frame_to_photo(frame, box)
            if photo is None:
                continue
            item["label"].config(image=photo, text="")
            item["photo"] = photo
        try:
            self._after = self.after(delay, self._tick_video)
        except tk.TclError:
            self._after = None

    def _frame_to_photo(self, frame, box: tuple[int, int]):
        if cv2 is None:
            return None
        max_w, max_h = box
        height, width = frame.shape[:2]
        if width < 1 or height < 1:
            return None
        scale = min(max_w / width, max_h / height)
        size = (max(1, int(width * scale)), max(1, int(height * scale)))
        if size != (width, height):
            frame = cv2.resize(frame, size)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if Image is None or ImageTk is None:
            return None
        return ImageTk.PhotoImage(Image.fromarray(rgb))

    def _release(self, _event=None) -> None:
        self._stopped = True
        for item in self._videos:
            cap = item.get("cap")
            if cap is not None:
                cap.release()
                item["cap"] = None
        self._videos = []
        self._images = []
        self._photos = []
