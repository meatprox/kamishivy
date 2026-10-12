from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI


def _choice_number(text: str) -> int | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        value = int(float(raw))
    except ValueError:
        return None
    if value < 1:
        return None
    return value


class UI(BaseUI):
    def build(self) -> None:
        self._items = self._read_questions()
        self._vars: list[tk.IntVar] = []
        self._wrap_labels: list[ttk.Label] = []

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        self._frame = frame

        for q_index, item in enumerate(self._items):
            block = ttk.Frame(frame)
            block.grid(row=q_index, column=0, sticky="ew", padx=16, pady=(20 if q_index == 0 else 12, 8))
            block.columnconfigure(1, weight=1)

            question = ttk.Label(block, text=item["question"], justify="left", wraplength=640)
            question.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
            self._wrap_labels.append(question)

            var = tk.IntVar(value=0)
            self._vars.append(var)
            for number, choice in enumerate(item["choices"], start=1):
                ttk.Radiobutton(block, variable=var, value=number, command=self._sync).grid(
                    row=number, column=0, sticky="nw", padx=(8, 8), pady=3
                )
                label = ttk.Label(block, text=choice, justify="left", wraplength=640)
                label.grid(row=number, column=1, sticky="w", pady=3)
                self._wrap_labels.append(label)

        frame.bind("<Configure>", self._on_resize)
        self._sync()

    def _read_questions(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in cui().grid:
            cells = [str(cell).strip() for cell in row]
            if not any(cells):
                continue
            question = cells[0] if cells else ""
            correct_raw = cells[1] if len(cells) > 1 else ""
            choices = [cell for cell in cells[2:] if cell]
            correct = _choice_number(correct_raw)
            if not question or correct is None or not choices:
                raise ValueError("設問・正解番号・選択肢がCUIから取得できませんでした")
            if correct > len(choices):
                raise ValueError("正解番号が選択肢の数を超えています")
            items.append({"question": question, "correct": correct, "choices": choices})
        if not items:
            raise ValueError("設問がCUIから取得できませんでした")
        return items

    def _on_resize(self, event: tk.Event) -> None:
        if event.widget is not self._frame:
            return
        width = max(1, int(event.width) - 48)
        for label in self._wrap_labels:
            try:
                current = str(label.cget("wraplength") or "0")
                if int(float(current)) != width:
                    label.configure(wraplength=width)
            except (tk.TclError, TypeError, ValueError):
                pass

    def _ok(self) -> bool:
        return bool(self._vars) and all(
            int(var.get()) == int(item["correct"]) for var, item in zip(self._vars, self._items)
        )

    def _sync(self) -> None:
        self.ready = self._ok()

    def is_condition_met(self) -> bool:
        return self._ok()

    def get_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {
            f"quiz.{index}": int(var.get()) for index, var in enumerate(self._vars)
        }
        state["判定"] = "TRUE" if self._ok() else "FALSE"
        return state
