from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

HEADING_KEY = "見出し"
HEADING_MARK = "♯"
HEADING_MARKS = ("#", "＃", "♯")


def _is_seq(value: Any) -> bool:
    return isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes))


def _is_table(value: Any) -> bool:
    return _is_seq(value) and bool(value) and all(_is_seq(item) for item in value)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def normalize_headings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not _is_seq(value):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def is_heading_row(row: list[str]) -> bool:
    return bool(row) and str(row[0]).strip() in HEADING_MARKS


def heading_cells(row: list[str]) -> list[str]:
    if not is_heading_row(row):
        return []
    return [str(cell) for cell in row[1:]]


def _dict_items(values: dict[str, Any]) -> list[tuple[str, Any]]:
    items = [(str(key), value) for key, value in values.items() if str(key) != "判定"]
    if "判定" in values:
        items.append(("判定", values["判定"]))
    return items


class SessionLogger:
    def __init__(
        self,
        directory: Path,
        cui_name: str = "",
        backup_directory: Path | None = None,
    ) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.cui_name = str(cui_name or "")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = self.directory / f"session_{stamp}.csv"
        self.backup_path: Path | None = None
        with self.path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["CUI", self.cui_name])
            writer.writerow(["timestamp", "ui_name", "title", "key", "value"])
        self.set_backup(backup_directory)

    def set_backup(self, directory: Path | None) -> None:
        self.backup_path = None
        if directory is None:
            return
        try:
            dest_dir = Path(directory)
            if dest_dir.resolve() == self.directory.resolve():
                return
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / self.path.name
            dest.write_bytes(self.path.read_bytes())
            self.backup_path = dest
        except OSError:
            self.backup_path = None

    def _append_backup(self, rows: list[list[Any]]) -> None:
        path = self.backup_path
        if path is None or not rows:
            return
        try:
            with path.open("a", encoding="utf-8-sig", newline="") as handle:
                csv.writer(handle).writerows(rows)
        except OSError:
            return

    def write(
        self,
        ui_name: str,
        values: dict[str, Any] | list[Any] | tuple[Any, ...],
        title: str = "",
        headings: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        labels = normalize_headings(headings)
        payload: Any = values
        if isinstance(values, dict):
            payload = dict(values)
            extra = payload.pop(HEADING_KEY, None)
            if extra is not None:
                labels = normalize_headings(extra) or labels
        if not payload and not labels:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        heading = str(title or "")
        rows: list[list[Any]] = []
        if labels:
            rows.append([timestamp, ui_name, heading, HEADING_MARK, *labels])
        if payload:
            if _is_table(payload):
                for row in payload:
                    rows.append([timestamp, ui_name, heading, *list(row)])
            elif _is_seq(payload):
                rows.append([timestamp, ui_name, heading, *list(payload)])
            elif not isinstance(payload, dict):
                rows.append([timestamp, ui_name, heading, "log", payload])
            elif payload and all(_is_number(item) for item in payload.values()):
                rows.append([timestamp, ui_name, heading, *list(payload.values())])
            else:
                for key, value in _dict_items(payload):
                    if _is_table(value):
                        for row in value:
                            rows.append([timestamp, ui_name, heading, str(key), *list(row)])
                    elif _is_seq(value):
                        rows.append([timestamp, ui_name, heading, str(key), *list(value)])
                    else:
                        rows.append([timestamp, ui_name, heading, str(key), value])
        if not rows:
            return
        with self.path.open("a", encoding="utf-8-sig", newline="") as handle:
            csv.writer(handle).writerows(rows)
        self._append_backup(rows)

    def read_records(self) -> list[list[str]]:
        return read_log_records(self.path)


def read_log_records(path: Path) -> list[list[str]]:
    if not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if len(rows) <= 2:
        return []
    return [list(row) for row in rows[2:]]
