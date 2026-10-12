from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk
from typing import Any

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

# カメラ番号。0 が1台目、1 が2台目。ここを変える。
CAMERA = 0
# カメラ解像度。低いとバーコードが読めない。
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# 画面の見出し。ここを変える。
MSG_FROZEN = "この版ではバーコードを使えません。"
MSG_NOT_READY = "バーコードを読む準備がありません。"
MSG_NO_PREVIEW = "カメラを表示できません。"
MSG_NO_CAMERA = "カメラを開けません。"

_decode = None
# JAN は EAN-13/8。近い ISBN / UPC も JAN として扱う。
_ALLOWED_TYPES = frozenset({"EAN13", "EAN8", "UPCA", "ISBN13", "ISBN10", "CODE39", "CODE128"})

try:
    from pyzbar.pyzbar import decode as _pyzbar_decode
except Exception:
    _pyzbar_decode = None
else:
    _decode = _pyzbar_decode


def _barcode_available() -> bool:
    if getattr(sys, "frozen", False):
        return False
    return _decode is not None


def _item_type_name(item: Any) -> str:
    kind = getattr(item, "type", None)
    name = getattr(kind, "name", None)
    if name:
        return str(name).upper()
    return str(kind or "").upper().replace("ZBARSYMBOL.", "").replace("EAN-13", "EAN13").replace("EAN-8", "EAN8")


def _texts_from_found(found: Any) -> list[str]:
    texts: list[str] = []
    for item in found or ():
        if _item_type_name(item) not in _ALLOWED_TYPES:
            continue
        data = getattr(item, "data", b"")
        if isinstance(data, bytes):
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                text = data.decode("latin-1", errors="replace")
        else:
            text = str(data)
        text = text.strip()
        if text and text not in texts:
            texts.append(text)
    return texts


def _decode_image(image: Any) -> list[str]:
    if not _barcode_available() or _decode is None or image is None:
        return []
    try:
        return _texts_from_found(_decode(image))
    except Exception:
        return []


def _decode_frame(frame: Any) -> list[str]:
    """カメラ映像から JAN / Code39 / Code128 の記載内容を拾う。"""
    if frame is None or cv2 is None:
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    views: list[Any] = [gray, rgb]
    if Image is not None:
        views = [
            Image.fromarray(rgb),
            Image.fromarray(gray),
            Image.fromarray(cv2.bitwise_not(gray)),
        ]
        height, width = gray.shape[:2]
        if width >= 640:
            small = cv2.resize(gray, (width // 2, height // 2))
            views.append(Image.fromarray(small))
    for view in views:
        texts = _decode_image(view)
        if texts:
            return texts
    return []


class UI(BaseUI):
    def build(self) -> None:
        self._stopped = False
        self._after = None
        self._cap = None
        self._photo = None
        self._scanned = ""
        self._logged = ""
        self._stage_size = (0, 0)

        bg = str(design.get("background") or "#f0f0f0")
        fg = str(design.get("text") or "#000000")
        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        weight = ("bold",) if int(design.get("font_bold") or 0) else ()

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self._stage = tk.Frame(frame, bg=bg)
        self._stage.grid(row=0, column=0, sticky="nsew")
        self._preview = tk.Label(self._stage, bg=bg, fg=fg, font=(family, size), compound="center")
        self._preview.pack(fill="both", expand=True, padx=8, pady=8)

        self._value = tk.StringVar(value="")
        ttk.Label(
            frame,
            textvariable=self._value,
            font=(family, max(20, size + 12), *weight),
            anchor="center",
        ).grid(row=1, column=0, pady=(0, 16), sticky="ew")

        self._stage.bind("<Configure>", self._on_stage_configure)
        self.bind("<Destroy>", self._release, add="+")
        self._start()

    def _start(self) -> None:
        if not _barcode_available():
            if getattr(sys, "frozen", False):
                self._preview.config(text=MSG_FROZEN)
            else:
                self._preview.config(text=MSG_NOT_READY)
            return
        if cv2 is None or Image is None or ImageTk is None:
            self._preview.config(text=MSG_NO_PREVIEW)
            return
        backends = []
        if sys.platform.startswith("win"):
            backends.append(getattr(cv2, "CAP_DSHOW", None))
        backends.append(None)
        cap = None
        for backend in backends:
            trial = cv2.VideoCapture(CAMERA) if backend is None else cv2.VideoCapture(CAMERA, backend)
            if trial.isOpened():
                cap = trial
                break
            trial.release()
        if cap is None:
            self._preview.config(text=MSG_NO_CAMERA)
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap = cap
        self._value.set("バーコードを向けてください")
        self._tick()

    def _on_stage_configure(self, event: tk.Event) -> None:
        if event.widget is not self._stage:
            return
        size = (max(1, event.width), max(1, event.height))
        if size != self._stage_size:
            self._stage_size = size

    def _tick(self) -> None:
        if self._stopped or self._cap is None or cv2 is None:
            return
        ok, frame = self._cap.read()
        if ok:
            texts = _decode_frame(frame)
            if texts:
                self._on_decoded(texts[0])
            photo = self._frame_to_photo(frame)
            if photo is not None:
                self._preview.config(image=photo, text="")
                self._photo = photo
        try:
            self._after = self.after(80, self._tick)
        except tk.TclError:
            self._after = None

    def _frame_to_photo(self, frame):
        if cv2 is None or Image is None or ImageTk is None:
            return None
        width, height = self._stage_size
        if width < 20 or height < 20:
            width, height = 480, 360
        max_w, max_h = max(20, width - 16), max(20, height - 16)
        src_h, src_w = frame.shape[:2]
        if src_w < 1 or src_h < 1:
            return None
        scale = min(max_w / src_w, max_h / src_h)
        size = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
        if size != (src_w, src_h):
            frame = cv2.resize(frame, size)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(Image.fromarray(rgb))

    def _on_decoded(self, text: str) -> None:
        if text == self._scanned:
            return
        self._scanned = text
        self._value.set(text)
        if text != self._logged:
            self._logged = text
            write_log(text)
        self.ready = True

    def is_condition_met(self) -> bool:
        return bool(self._scanned)

    def get_state(self) -> dict[str, Any]:
        return {
            "barcode": self._scanned,
            "判定": "TRUE" if self.is_condition_met() else "FALSE",
        }

    def _release(self, _event=None) -> None:
        self._stopped = True
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._photo = None
