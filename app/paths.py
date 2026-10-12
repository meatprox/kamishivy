from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """設定・CUI・後付け UI の置き場。exe 化後は exe と同じフォルダ。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def ui_dir() -> Path:
    return app_root() / "ui"
