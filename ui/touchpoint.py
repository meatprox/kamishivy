from __future__ import annotations

import math
import tkinter as tk
from typing import Any

from ui.base import BaseUI


# CUI format (one screen row):
#   cell 1: image path / image link
#   remaining cells: x, y, [radius], x, y, [radius], ...
# Coordinates are percentages of the displayed image:
#   top-left = (0, 0), bottom-right = (100, 100).
# A point is considered touched when the click is within its radius.
# If radius is omitted, 4 (%) is used.
#
# Example:
#   assets/check.png, 25, 40, 5, 70, 65, 5
# The user must touch every configured point before the host's Next button
# becomes enabled.

DEFAULT_RADIUS = 4.0


class UI(BaseUI):
    def build(self) -> None:
        self.ready = False
        self._visited: set[int] = set()
        self._points: list[tuple[float, float, float]] = []
        self._photo: tk.PhotoImage | None = None
        self._pil_photo: Any = None
        self._image_width = 1
        self._image_height = 1
        self._image_offset_x = 0
        self._image_offset_y = 0
        self._display_width = 1
        self._display_height = 1

        cells = self._read_cells()
        image_cell = cells[0] if cells else ""
        self._points = self._parse_points(cells[1:])

        fg = str(design.get("text") or "#000000")
        bg = str(design.get("background") or "#f0f0f0")
        font = design.get("font") or (
            str(design.get("font_family") or "ＭＳ Ｐゴシック"),
            int(design.get("font_size") or 10),
        )

        self._status_var = tk.StringVar(master=self, value=self._status_text())
        self._status = tk.Label(
            self, textvariable=self._status_var, font=font, fg=fg, bg=bg
        )
        self._status.pack(pady=(8, 6))

        self._canvas = tk.Canvas(
            self,
            background=bg,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
        )
        self._canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self._canvas.bind("<Configure>", self._on_resize)
        self._canvas.bind("<Button-1>", self._on_click)

        if image_cell:
            self._load_image(image_cell)
        else:
            self._canvas.create_text(
                20, 20, anchor="nw",
                text="CUIの画像パス欄に画像ファイルのパスを指定してください。",
                fill=fg,
            )

        if self._points:
            self._draw_image()

    def _read_cells(self) -> list[str]:
        """Get the CUI values without importing or redefining injected APIs."""
        try:
            info = cui()
            grid = getattr(info, "grid", None)
            if grid:
                # The normal CUI row is represented as a list of cells.
                if isinstance(grid[0], (list, tuple)):
                    row = list(grid[0])
                    # If grid contains several rows, use the first non-empty row.
                    for candidate in grid:
                        if any(str(value).strip() for value in candidate):
                            row = list(candidate)
                            break
                    return [str(value).strip() for value in row]
                return [str(value).strip() for value in grid]
            row = getattr(info, "row", None)
            if row:
                return [str(value).strip() for value in row]
            cell = getattr(info, "cell", "")
            return [str(cell).strip()] if str(cell).strip() else []
        except Exception:
            return []

    def _parse_points(self, values: list[str]) -> list[tuple[float, float, float]]:
        # Values are grouped as x,y,radius. Radius is optional. To keep the
        # CUI easy to edit, pairs x,y are also accepted when all values are pairs.
        raw: list[float] = []
        for value in values:
            try:
                raw.append(float(str(value).replace("%", "").strip()))
            except (TypeError, ValueError):
                # Ignore blank/non-numeric cells (for example, a note column).
                continue

        points: list[tuple[float, float, float]] = []
        i = 0
        while i + 1 < len(raw):
            x, y = raw[i], raw[i + 1]
            radius = DEFAULT_RADIUS
            if i + 2 < len(raw):
                # Treat the third value as radius if it is a plausible radius
                # and enough values remain for another point or this is the end.
                candidate = raw[i + 2]
                remaining_after_radius = len(raw) - (i + 3)
                if 0 < candidate <= 25 and (remaining_after_radius == 0 or remaining_after_radius >= 2):
                    radius = candidate
                    i += 3
                else:
                    i += 2
            else:
                i += 2

            if 0 <= x <= 100 and 0 <= y <= 100:
                points.append((x, y, max(0.5, min(radius, 25.0))))
        return points

    def _load_image(self, image_cell: str) -> None:
        try:
            resolved = file_path(image_cell)
            path = str(resolved.path) if resolved is not None else image_cell
        except Exception:
            path = image_cell

        try:
            # Tk's native loader supports PNG/GIF on standard Python builds.
            self._photo = tk.PhotoImage(file=path)
            self._image_width = self._photo.width()
            self._image_height = self._photo.height()
        except Exception:
            # JPEG and other formats may be supported when Pillow is installed.
            try:
                from PIL import Image, ImageTk  # optional dependency

                image = Image.open(path).convert("RGBA")
                self._image_width, self._image_height = image.size
                self._pil_photo = ImageTk.PhotoImage(image)
            except Exception as exc:
                self._canvas.create_text(
                    20, 20, anchor="nw",
                    text=f"画像を開けませんでした:\n{path}\n{exc}",
                    fill=str(design.get("text") or "#000000"),
                )
                return
        self.after_idle(self._draw_image)

    def _on_resize(self, _event: tk.Event) -> None:
        self._draw_image()

    def _draw_image(self) -> None:
        if not hasattr(self, "_canvas"):
            return

        self._canvas.delete("all")
        image = self._photo or self._pil_photo
        canvas_w = max(1, self._canvas.winfo_width())
        canvas_h = max(1, self._canvas.winfo_height())

        if image is None:
            self._canvas.create_text(
                16, 16, anchor="nw",
                text="画像を表示できません。CUIの画像パスを確認してください。",
                fill=str(design.get("text") or "#000000"),
            )
            return

        # Fit the image into the available area while preserving aspect ratio.
        scale = min(
            (canvas_w - 16) / max(1, self._image_width),
            (canvas_h - 16) / max(1, self._image_height),
        )
        scale = max(0.01, scale)
        self._display_width = max(1, int(self._image_width * scale))
        self._display_height = max(1, int(self._image_height * scale))

        # Use integer subsampling/zoom for Tk images where possible. Pillow
        # gives smoother resizing and supports arbitrary display dimensions.
        display_image = image
        try:
            if self._photo is not None:
                # Tk PhotoImage zoom/subsample only accepts integer factors.
                # Keep the original image if exact scaling is unavailable.
                if scale >= 1:
                    factor = max(1, int(scale))
                    display_image = self._photo.zoom(factor, factor)
                else:
                    factor = max(1, int(round(1 / scale)))
                    display_image = self._photo.subsample(factor, factor)
                self._display_width = display_image.width()
                self._display_height = display_image.height()
            else:
                from PIL import Image, ImageTk

                # Reopen through the retained PhotoImage's source size is not
                # possible, so scale the source file again.
                cells = self._read_cells()
                resolved = file_path(cells[0]) if cells else None
                path = str(resolved.path) if resolved is not None else (cells[0] if cells else "")
                im = Image.open(path).convert("RGBA")
                im = im.resize((self._display_width, self._display_height), Image.Resampling.LANCZOS)
                display_image = ImageTk.PhotoImage(im)
                self._pil_photo = display_image
        except Exception:
            display_image = image

        self._image_offset_x = (canvas_w - self._display_width) // 2
        self._image_offset_y = (canvas_h - self._display_height) // 2
        self._canvas.create_image(
            self._image_offset_x, self._image_offset_y,
            anchor="nw", image=display_image, tags="background_image"
        )
        self._canvas.image = display_image

    def _on_click(self, event: tk.Event) -> None:
        if not self._points:
            return
        # Ignore clicks in the letterboxed margins around the image.
        x_img = event.x - self._image_offset_x
        y_img = event.y - self._image_offset_y
        if not (0 <= x_img <= self._display_width and 0 <= y_img <= self._display_height):
            return

        x_pct = x_img * 100.0 / self._display_width
        y_pct = y_img * 100.0 / self._display_height

        for index, (x, y, radius) in enumerate(self._points):
            if index in self._visited:
                continue
            dx = (x_pct - x) * self._display_width / 100.0
            dy = (y_pct - y) * self._display_height / 100.0
            hit_radius = max(12.0, radius * min(self._display_width, self._display_height) / 100.0)
            if math.hypot(dx, dy) <= hit_radius:
                self._visited.add(index)
                self._sync_ready()
                break

    def _sync_ready(self) -> None:
        self.ready = bool(self._points) and len(self._visited) == len(self._points)
        self._status_var.set(self._status_text())

    def _status_text(self) -> str:
        if not self._points:
            return "設定ポイントがありません"
        return f"タッチ済み: {len(self._visited)} / {len(self._points)}"

    def get_state(self) -> dict[str, Any]:
        return {
            "image": self._read_cells()[0] if self._read_cells() else "",
            "point_count": len(self._points),
            "touched_count": len(self._visited),
            "touched_points": sorted(index + 1 for index in self._visited),
            "判定": "TRUE" if self.ready else "FALSE",
        }
