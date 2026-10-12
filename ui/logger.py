from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.base import BaseUI

# 受信番号。1〜9。comA は "comA"。
DATA = 1

# ロガーへ送るコマンド。複数行可。空行は送らない。
COMMAND = """
D01
"""

# 配列に分ける区切り。空なら分割せず文字列のまま。
DELIMITER = ","

# 受信1件の終わり。空なら COM の改行読み。機器が CR のみなら "\r"。
END = ""

# この応答のあとに本データが来る。空なら最初の受信で確定。
ACK = "OK"

# 画面の見出し。ここを変える。
LABEL_LIVE = "受信値"
LABEL_RESULT = "結果"
LABEL_READ = "読み込み"

_EOL_MARKS = ("\n", "\r", "\r\n", "\n\r")


class UI(BaseUI):
    def build(self) -> None:
        self._commands = [line.strip() for line in str(COMMAND or "").splitlines() if line.strip()]
        self._delimiter = str(DELIMITER or "")
        self._end = str(END or "")
        self._ack = str(ACK or "").strip()
        self._cmd_index = 0
        self._after_id: str | None = None
        self._result: str | list[Any] | None = None
        self._listening = False
        self._live = tk.StringVar(value="---")
        self._result_text = tk.StringVar(value="---")

        family = str(design.get("font_family") or "ＭＳ Ｐゴシック")
        size = int(design.get("font_size") or 9)
        weight = ("bold",) if int(design.get("font_bold") or 0) else ()
        entered_font = (family, max(24, size + 16), *weight)

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text=LABEL_LIVE, anchor="center").grid(row=0, column=0, pady=(16, 0), sticky="ew")
        ttk.Label(
            frame,
            textvariable=self._live,
            font=(family, max(28, size + 36), *weight),
            anchor="center",
        ).grid(row=1, column=0, pady=(4, 8), sticky="ew")

        ttk.Label(frame, text=LABEL_RESULT, anchor="center").grid(row=2, column=0, pady=(8, 0), sticky="ew")
        ttk.Label(
            frame,
            textvariable=self._result_text,
            font=entered_font,
            anchor="center",
        ).grid(row=3, column=0, pady=(4, 8), sticky="ew")

        ttk.Button(frame, text=LABEL_READ, command=self._on_read).grid(row=4, column=0, pady=16)

        self._refresh_live()
        self._after_id = self.after(100, self._on_read)

    def _field_delimiter(self) -> str:
        if self._delimiter in _EOL_MARKS:
            return ","
        return self._delimiter

    def _outgoing(self, line: str) -> str:
        if line.endswith("\r") or line.endswith("\n"):
            return line
        return line + (self._end or "\r\n")

    def _fmt_result(self, value: str | list[Any] | None) -> str:
        if value is None:
            return "---"
        if isinstance(value, list):
            sep = self._field_delimiter() or ","
            return sep.join(str(item) for item in value)
        return str(value)

    def _refresh_live(self) -> None:
        raw = get_data(DATA, raw=True)
        self._live.set("---" if raw is None or raw == "" else str(raw).strip() or "---")

    def _cancel_after(self) -> None:
        if self._after_id is None:
            return
        try:
            self.after_cancel(self._after_id)
        except tk.TclError:
            pass
        self._after_id = None

    def _on_read(self) -> None:
        self._cancel_after()
        self._result = None
        self._result_text.set("---")
        self._cmd_index = 0
        self._listening = True
        self._refresh_live()
        if not self._commands:
            return
        self._send_one(flush=True)
        if not self._ack:
            self._send_rest()

    def _send_one(self, flush: bool = False) -> None:
        if self._cmd_index >= len(self._commands):
            return
        text = self._outgoing(self._commands[self._cmd_index])
        send_data(DATA, text, flush_input=flush)
        self._cmd_index += 1

    def _send_rest(self) -> None:
        if self._cmd_index >= len(self._commands):
            return

        def _next() -> None:
            self._after_id = None
            self._send_one()
            self._send_rest()

        self._after_id = self.after(50, _next)

    def _split(self, text: str, delim: str) -> list[Any]:
        parts = [part.strip() for part in text.split(delim)]
        values: list[Any] = []
        for part in parts:
            number = parse_number(part)
            if number is None:
                values.append(part)
            elif float(number).is_integer():
                values.append(int(number))
            else:
                values.append(number)
        return values

    def _parse_payload(self, text: str) -> str | list[Any]:
        delim = self._field_delimiter()
        if delim and delim in text:
            return self._split(text, delim)
        return text

    def _set_result(self, value: str | list[Any]) -> None:
        self._result = value
        self._listening = False
        self._cancel_after()
        self._result_text.set(self._fmt_result(value))
        ok = self.is_condition_met()
        payload: dict[str, Any] = {
            "データ読み込み番号": DATA,
        }
        if isinstance(value, list):
            payload["受信"] = value
        else:
            payload["value"] = value
        payload["判定"] = "TRUE" if ok else "FALSE"
        write_log(payload)
        self.ready = True

    def _ingest(self, text: str) -> None:
        if not self._listening or self._result is not None:
            return
        raw = str(text or "").strip()
        if not raw:
            return
        delim = self._field_delimiter()
        if self._ack:
            if raw == self._ack:
                if self._cmd_index < len(self._commands):
                    self._send_one()
                return
            prefix = self._ack + delim if delim else ""
            if prefix and raw.startswith(prefix) and len(raw) > len(prefix):
                self._set_result(self._parse_payload(raw[len(prefix) :]))
                return
        self._set_result(self._parse_payload(raw))

    def on_data(self, channel: int, value: Any) -> None:
        key = str(DATA).lower().replace("_", "").replace("-", "")
        want = 10 if key in {"a", "coma", "10"} else int(DATA)
        if channel != want:
            return
        raw = get_data(DATA, raw=True)
        self._live.set("---" if raw is None or raw == "" else str(raw).strip() or "---")
        if raw is None:
            return
        self._ingest(str(raw))

    def is_condition_met(self) -> bool:
        if self._result is None:
            return False
        if isinstance(self._result, str):
            return bool(self._result)
        return bool(self._result)

    def get_state(self) -> list[Any] | dict[str, Any]:
        if self._result is None:
            return {
                "データ読み込み番号": DATA,
                "判定": "FALSE",
            }
        if isinstance(self._result, list):
            return list(self._result)
        return {
            "データ読み込み番号": DATA,
            "value": self._result,
            "判定": "TRUE",
        }
