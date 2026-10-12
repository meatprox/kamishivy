from __future__ import annotations

import importlib.util
import re
import sys
import textwrap
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterable

from app.channels import resolve_channel
from app.logger import normalize_headings
from app.parse import format_remain, parse_number, parse_seconds
from app.paths import app_root, ui_dir


RESERVED_UI_NAMES = {"base", "__init__"}


@dataclass
class UIContext:
    ui_name: str
    title: str
    variables: dict[str, str]
    get_data: Callable[[int], Any]
    get_all_data: Callable[[], dict[int, Any]]
    log_done: Callable[[Any], None]
    write_log: Callable[[Any], None]
    get_com_data: Callable[[], dict[str, Any] | None]
    is_com_connected: Callable[[], bool]
    notify_condition: Callable[[], None]
    design: dict[str, Any] = field(default_factory=dict)
    texts: list[str] = field(default_factory=list)
    args: list[list[str]] = field(default_factory=list)
    get_raw: Callable[[int], Any] = field(default=lambda *_a, **_k: None)
    send_data: Callable[..., bool] = field(default=lambda *_a, **_k: False)
    set_read_end: Callable[..., None] = field(default=lambda *_a, **_k: None)


def strip_trailing_cui_empties(rows: list[list[str]]) -> list[list[str]]:
    """各行の右端の空セルを落とす。空タイトル行の [\"\"] は残す。"""
    cleaned: list[list[str]] = []
    for row in rows:
        cells = [str(cell) for cell in row]
        if not any(cell.strip() for cell in cells):
            cleaned.append([""] if cells else [])
            continue
        while cells and not cells[-1].strip():
            cells.pop()
        cleaned.append(cells)
    return cleaned


class VScrollArea:
    """縦に収まらないときスクロールする表用。新しい行は see_widget / see_bottom で見せる。"""

    def __init__(self, parent, background: str = "#f0f0f0") -> None:
        self.frame = ttk.Frame(parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(
            self.frame,
            highlightthickness=0,
            bd=0,
            background=background,
        )
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, background=background)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.inner.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel_up)
        self.canvas.bind("<Button-5>", self._on_wheel_down)
        self.inner.bind("<Button-4>", self._on_wheel_up)
        self.inner.bind("<Button-5>", self._on_wheel_down)
        self._laying_out = False

    def layout(self) -> None:
        if self._laying_out:
            return
        self._laying_out = True
        try:
            self.inner.update_idletasks()
            width = max(int(self.canvas.winfo_width() or 0), int(self.inner.winfo_reqwidth() or 0), 1)
            height = max(int(self.inner.winfo_reqheight() or 0), 1)
            self.canvas.itemconfigure(self._win, width=width, height=height)
            self.canvas.configure(scrollregion=self.canvas.bbox("all") or (0, 0, width, height))
        finally:
            self._laying_out = False
        self._bind_tree(self.inner)

    def _on_inner(self, _event=None) -> None:
        self.layout()

    def _on_canvas(self, event) -> None:
        if self._laying_out:
            return
        height = max(int(self.inner.winfo_reqheight() or 0), 1)
        self.canvas.itemconfigure(self._win, width=max(int(event.width), 1), height=height)
        self.canvas.configure(scrollregion=self.canvas.bbox("all") or (0, 0, 0, 0))

    def _on_wheel(self, event) -> str:
        delta = int(getattr(event, "delta", 0) or 0)
        if delta:
            self.canvas.yview_scroll(int(-1 * (delta / 120)), "units")
        return "break"

    def _on_wheel_up(self, _event=None) -> str:
        self.canvas.yview_scroll(-1, "units")
        return "break"

    def _on_wheel_down(self, _event=None) -> str:
        self.canvas.yview_scroll(1, "units")
        return "break"

    def bind_wheel(self, widget) -> None:
        widget.bind("<MouseWheel>", self._on_wheel)
        widget.bind("<Button-4>", self._on_wheel_up)
        widget.bind("<Button-5>", self._on_wheel_down)

    def _bind_tree(self, widget) -> None:
        if getattr(widget, "_kamishivy_wheel", False):
            return
        try:
            widget._kamishivy_wheel = True  # type: ignore[attr-defined]
        except Exception:
            return
        self.bind_wheel(widget)
        try:
            children = widget.winfo_children()
        except tk.TclError:
            return
        for child in children:
            self._bind_tree(child)

    def see_bottom(self) -> None:
        self.layout()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
        self.canvas.yview_moveto(1.0)

    def see_widget(self, widget) -> None:
        self.layout()
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        total = max(1, int(bbox[3] - bbox[1]))
        view = max(1, int(self.canvas.winfo_height()))
        if total <= view:
            self.canvas.yview_moveto(0.0)
            return
        try:
            y = int(widget.winfo_y())
            height = int(widget.winfo_height())
        except tk.TclError:
            self.see_bottom()
            return
        if height <= 1:
            self.see_bottom()
            return
        top = max(0.0, min(1.0, (y + height - view) / total))
        self.canvas.yview_moveto(top)


def set_wraplength(widget, width: int) -> None:
    try:
        current = str(widget.cget("wraplength") or "0")
        if int(float(current)) != int(width):
            widget.configure(wraplength=int(width))
    except (tk.TclError, TypeError, ValueError):
        return


def resolve_cui_row(grid: list[list[str]]) -> list[str]:
    """引数グリッドの先頭行から読む。空なら同じ列の下を使い、まだ残るマスは後に続ける。"""
    if not grid:
        return []
    width = max(len(row) for row in grid)
    taken = [[False] * len(row) for row in grid]
    filled: list[str] = []
    for col in range(width):
        found = ""
        for row_index, row in enumerate(grid):
            if col < len(row) and str(row[col]).strip():
                found = str(row[col])
                taken[row_index][col] = True
                break
        filled.append(found)
    while filled and not filled[-1].strip():
        filled.pop()
    extras: list[str] = []
    for row_index, row in enumerate(grid):
        for col, cell in enumerate(row):
            if col < len(taken[row_index]) and taken[row_index][col]:
                continue
            if str(cell).strip():
                extras.append(str(cell))
    return filled + extras


_EOL_MARKS = ("\n", "\r", "\r\n", "\n\r")


def _cui_numbers(grid: list[list[str]]) -> list[float]:
    numbers: list[float] = []
    for row in grid:
        for cell in row:
            text = str(cell).strip()
            if not text or "=" in text:
                continue
            value = parse_number(text)
            if value is not None:
                numbers.append(value)
    return numbers


def cui_info(context: UIContext) -> SimpleNamespace:
    grid = strip_trailing_cui_empties([list(row) for row in context.args])
    row = resolve_cui_row(grid)
    numbers = _cui_numbers(grid)
    return SimpleNamespace(
        title=str(context.title or ""),
        cell=row[0] if row else "",
        row=list(row),
        grid=[list(item) for item in grid],
        texts=list(context.texts),
        numbers=list(numbers),
        target=numbers[0] if numbers else None,
        tare=abs(numbers[1]) if len(numbers) >= 2 else 0.0,
    )


def _make_get_data(context: UIContext):
    def get_data(number, raw=False):
        if raw:
            return context.get_raw(number)
        return context.get_data(number)

    return get_data


_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".webm", ".mpg", ".mpeg"}


def _clean_file_cell(text: str) -> str:
    raw = str(text or "").strip().strip('"').strip("'")
    if raw.lower().startswith("file:"):
        raw = raw[5:]
        if raw.startswith("///"):
            raw = raw[3:]
        elif raw.startswith("//"):
            raw = raw[2:]
    return raw.strip()


def _load_still(path: Path):
    try:
        from PIL import Image as _Image
    except ImportError:
        _Image = None
    if _Image is not None:
        try:
            image = _Image.open(path)
            image.load()
            return image.convert("RGBA") if image.mode not in ("RGB", "RGBA") else image
        except Exception:
            return None
    if path.suffix.lower() not in {".png", ".gif", ".pgm", ".ppm"}:
        return None
    try:
        return tk.PhotoImage(file=str(path))
    except tk.TclError:
        return None


def file_path(text: str) -> SimpleNamespace | None:
    """マスの文字をファイルパスとして読む。画像なら .image も載せる。"""
    cleaned = _clean_file_cell(text)
    if not cleaned:
        return None
    path = Path(cleaned).expanduser()
    if not path.is_absolute():
        path = app_root() / path
    suffix = path.suffix.lower()
    is_image = suffix in _IMAGE_EXT
    is_video = suffix in _VIDEO_EXT
    if not is_image and not is_video and not path.is_file():
        return None
    if is_image:
        kind = "image"
        image = _load_still(path) if path.is_file() else None
    elif is_video:
        kind = "video"
        image = None
    else:
        kind = "file"
        image = None
    return SimpleNamespace(path=path, kind=kind, image=image)


def _apply_key(text: str, key: str) -> str | None:
    current = str(text or "")
    if key == "⏎":
        return current
    if key == "C":
        return ""
    if key == "←":
        return current[:-1]
    if key == "-":
        return current[1:] if current.startswith("-") else "-" + current
    if key == ".":
        if "." in current.replace("-", "", 1):
            return None
        if current in ("", "-"):
            return current + "0."
        return current + "."
    return current + key


def _make_keypad(design: dict[str, Any]):
    def keypad(master, command) -> tk.Frame:
        bg = str(design.get("background") or "#f0f0f0")
        fg = str(design.get("text") or "#000000")
        font = design.get("font") or (
            str(design.get("font_family") or "ＭＳ Ｐゴシック"),
            int(design.get("font_size") or 9),
        )
        button_bg = str(design.get("button") or "#f0f0f0")
        button_fg = str(design.get("button_text") or fg)
        pad = tk.Frame(master, bg=bg)
        keys = (
            ("7", "8", "9"),
            ("4", "5", "6"),
            ("1", "2", "3"),
            ("0", ".", "-"),
            ("C", "←", "⏎"),
        )
        for r, line in enumerate(keys):
            for c, key in enumerate(line):
                col, span = (c, 1) if len(line) != 2 else ((0, 1) if c == 0 else (1, 2))
                tk.Button(
                    pad,
                    text=key,
                    font=font,
                    bg=button_bg,
                    fg=button_fg,
                    activebackground=button_bg,
                    activeforeground=button_fg,
                    relief="solid",
                    bd=1,
                    width=3,
                    height=1,
                    takefocus=0,
                    command=lambda k=key: command(k),
                ).grid(row=r, column=col, columnspan=span, padx=2, pady=2, sticky="nsew")
            pad.rowconfigure(r, weight=1)
        for col in range(3):
            pad.columnconfigure(col, weight=1)
        return pad

    keypad.apply = _apply_key  # type: ignore[attr-defined]
    return keypad


def bind_runtime(target: Any, context: UIContext, done: Callable[..., None] | None = None) -> None:
    """簡単な UI と同じ名前を、クラス UI のモジュールにも載せる。"""
    info = cui_info(context)

    def cui() -> SimpleNamespace:
        return cui_info(context)

    names = {
        "cui": cui,
        "cui_title": info.title,
        "cui_cell": info.cell,
        "cui_row": info.row,
        "cui_grid": info.grid,
        "get_data": _make_get_data(context),
        "write_log": context.write_log,
        "send_data": context.send_data,
        "design": dict(context.design),
        "keypad": _make_keypad(dict(context.design)),
        "parse_number": parse_number,
        "parse_seconds": parse_seconds,
        "format_remain": format_remain,
        "file_path": file_path,
    }
    if done is not None:
        names["done"] = done
    if isinstance(target, dict):
        target.update(names)
        return
    for key, value in names.items():
        setattr(target, key, value)


class BaseUI(tk.Frame):
    """各 UI サブプログラムの共通インタフェース。部品は self に置く。"""

    def __init__(self, parent, context: UIContext) -> None:
        bg = str(context.design.get("background") or "#f0f0f0")
        super().__init__(parent, background=bg)
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._context = context
        self._scrolls: list[VScrollArea] = []
        self._after_ids: list[Any] = []
        self._stopped = False
        self._ready = False
        self._ready_var: Any = None
        self._ready_trace_bound: Any = None
        self.data_index = resolve_channel(self._file_attr("DATA"))
        self.data_var: Any = None
        self.state: Any = {}
        self._apply_read_end()

    def _file_attr(self, name: str, default: Any = None) -> Any:
        module = sys.modules.get(getattr(self.__class__, "__module__", ""), None)
        return getattr(module, name, default)

    def _apply_read_end(self) -> None:
        if not self.data_index:
            return
        end = str(self._file_attr("END") or "")
        delimiter = str(self._file_attr("DELIMITER") or "")
        if end:
            self._context.set_read_end(self.data_index, end)
        elif delimiter in _EOL_MARKS:
            self._context.set_read_end(self.data_index, delimiter)

    def _notify(self) -> None:
        self._context.notify_condition()

    def _bind_ready_var(self, var: tk.Variable) -> None:
        self._ready_var = var
        try:
            self._ready = bool(var.get())
        except (tk.TclError, TypeError, ValueError):
            self._ready = False
        if self._ready_trace_bound is var:
            return
        self._ready_trace_bound = var
        var.trace_add("write", lambda *_a, **_k: self._notify())

    @property
    def ready(self) -> bool:
        if self._ready_var is not None:
            try:
                return bool(self._ready_var.get())
            except (tk.TclError, TypeError, ValueError):
                return False
        return bool(self._ready)

    @ready.setter
    def ready(self, value: Any) -> None:
        if isinstance(value, tk.Variable):
            self._bind_ready_var(value)
        else:
            self._ready_var = None
            self._ready = bool(value)
        self._notify()

    @property
    def ready_var(self) -> Any:
        return self._ready_var

    @ready_var.setter
    def ready_var(self, var: Any) -> None:
        self.ready = var

    def scroll_area(self, parent, background: str | None = None, **grid):
        """縦に収まらない表用の枠。戻った Frame に部品を置く。"""
        bg = background if background is not None else str(self._context.design.get("background") or "#f0f0f0")
        area = VScrollArea(parent, background=bg)
        if grid:
            area.frame.grid(**grid)
        self._scrolls.append(area)
        area.inner.after_idle(area.layout)
        return area.inner

    def see(self, widget=None) -> None:
        """widget が見える位置へ送る。省略時は最下段。"""
        if widget is None:
            for area in self._scrolls:
                area.see_bottom()
            return
        current = widget
        while current is not None:
            for area in self._scrolls:
                if current is area.inner:
                    area.see_widget(widget)
                    return
            current = getattr(current, "master", None)
        for area in self._scrolls:
            area.see_bottom()

    def after(self, ms, func=None, *args):
        aid = tk.Frame.after(self, ms, func, *args)
        self._after_ids.append(aid)
        return aid

    def after_idle(self, func=None, *args):
        aid = tk.Frame.after_idle(self, func, *args)
        self._after_ids.append(aid)
        return aid

    def after_cancel(self, aid) -> None:
        try:
            self._after_ids.remove(aid)
        except ValueError:
            pass
        return tk.Frame.after_cancel(self, aid)

    def build(self) -> None:
        raise NotImplementedError

    def get_state(self) -> dict[str, Any]:
        return self.state

    def log_headings(self) -> list[str]:
        """記録確認・ログの列見出し。ファイル先頭の HEADINGS を使う。"""
        return normalize_headings(self._file_attr("HEADINGS"))

    def is_condition_met(self) -> bool:
        """次へ可能かは self.ready。計算が必要なら各 UI が上書きする。"""
        return bool(self.ready)

    def next_label(self) -> str:
        text = str(self._file_attr("NEXT_LABEL") or "").strip()
        return text or "次へ"

    def next_exits(self) -> bool:
        return bool(self._file_attr("NEXT_EXITS"))

    def get_received_values(self) -> dict[str, Any] | list[Any]:
        state = self.get_state()
        if isinstance(state, (list, tuple)) and not isinstance(state, (str, bytes)):
            return list(state)
        if isinstance(state, dict):
            return dict(state)
        return {}

    def on_data(self, channel: int, value: Any) -> None:
        if self.data_var is None or not self.data_index or channel != self.data_index:
            return
        self.data_var.set("---" if value is None or value == "" else str(value))

    def on_com_data(self, data: dict[str, Any]) -> None:
        return None

    def destroy(self) -> None:
        self._stopped = True
        for aid in list(self._after_ids):
            try:
                tk.Frame.after_cancel(self, aid)
            except tk.TclError:
                pass
        self._after_ids.clear()
        if self.data_index:
            try:
                self._context.set_read_end(self.data_index, "")
            except Exception:
                pass
        tk.Frame.destroy(self)


def allows_next(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)) and value == 0:
        return False
    return True


def _auto_place(widget: tk.Misc) -> None:
    for child in widget.winfo_children():
        if not child.winfo_manager():
            child.pack(expand=True)


def _wrap_script_source(source: str) -> str:
    return "def __ui_script__():\n" + textwrap.indent(source.rstrip() + "\n", "    ")


def _wrap_script(source: str, filename: str) -> tuple[Callable[[], Any], dict[str, Any]]:
    return _runner_from_code(compile(_wrap_script_source(source), filename, "exec"))


def _runner_from_code(code: Any) -> tuple[Callable[[], Any], dict[str, Any]]:
    namespace: dict[str, Any] = {"__name__": "__ui_script__"}
    exec(code, namespace)
    return namespace["__ui_script__"], namespace


def _widget_bg(widget: tk.Misc | None, fallback: str) -> str:
    if widget is None:
        return fallback
    for key in ("bg", "background"):
        try:
            value = str(widget.cget(key)).strip()
        except tk.TclError:
            continue
        if value:
            return value
    return fallback


def _label_with_parent_bg(original: type[tk.Label], fallback_bg: str, fallback_fg: str) -> type[tk.Label]:
    """bg を書いていない Label は親と同じ色にする。Tk に透過はない。"""

    class _Label(original):
        def __init__(self, master=None, cnf=None, **kw):
            options = dict(cnf or {})
            options.update(kw)
            if "bg" not in options and "background" not in options:
                options["bg"] = _widget_bg(master, fallback_bg)
            if "fg" not in options and "foreground" not in options:
                options["fg"] = fallback_fg
            super().__init__(master, **options)

    return _Label


class TkScriptUI(BaseUI):
    """素の Tkinter スクリプトを中央に埋め込み、return で次へ可否を決める。"""

    def __init__(self, parent, context: UIContext, runner: Callable[[], Any], namespace: dict[str, Any]) -> None:
        super().__init__(parent, context)
        self._runner = runner
        self._namespace = namespace
        self._result: Any = None
        self._done_value: Any = None

    def build(self) -> None:
        fake_root = tk.Frame(self)
        fake_root.grid(row=0, column=0, sticky="nsew")
        fake_root.columnconfigure(0, weight=1)
        fake_root.rowconfigure(0, weight=1)

        def script_mainloop(*_args: Any, **_kwargs: Any) -> None:
            _auto_place(fake_root)

        fake_root.mainloop = script_mainloop  # type: ignore[method-assign]
        fake_root.quit = lambda *_a, **_k: None  # type: ignore[method-assign]

        original_tk = tk.Tk
        original_label = tk.Label
        design_bg = str(self._context.design.get("background") or "#f0f0f0")
        design_fg = str(self._context.design.get("text") or "#000000")
        patched_label = _label_with_parent_bg(original_label, design_bg, design_fg)

        def fake_tk(*_args: Any, **_kwargs: Any) -> tk.Frame:
            return fake_root

        tk.Tk = fake_tk  # type: ignore[misc, assignment]
        tk.Label = patched_label  # type: ignore[misc, assignment]
        bind_runtime(self._namespace, self._context, done=self._script_done)
        try:
            fake_root.configure(bg=design_bg)
        except tk.TclError:
            pass
        try:
            self._result = self._runner()
        finally:
            tk.Tk = original_tk  # type: ignore[misc]
            tk.Label = original_label  # type: ignore[misc]
        _auto_place(fake_root)
        self._notify()

    def _script_done(self, *values: Any) -> None:
        self._result = True
        if not values:
            self._done_value = None
        elif len(values) == 1:
            self._done_value = values[0]
        else:
            self._done_value = list(values)
        self._namespace["_done_value"] = self._done_value
        self._context.log_done(self._done_value)
        self._notify()

    def is_condition_met(self) -> bool:
        return allows_next(self._result)

    def log_headings(self) -> list[str]:
        return normalize_headings(self._namespace.get("HEADINGS"))

    def get_state(self) -> dict[str, Any]:
        return {
            "result": self._result,
            "done_value": self._done_value,
            "判定": "TRUE" if self.is_condition_met() else "FALSE",
        }


def _is_class_ui(source: str) -> bool:
    return re.search(r"class\s+UI\s*\(.*BaseUI", source) is not None


@dataclass
class PreparedUI:
    is_class: bool = False
    ui_class: type | None = None
    script_code: Any = None
    error: BaseException | None = None


_PREPARED: dict[str, PreparedUI] = {}


def prepare_ui(ui_name: str) -> PreparedUI:
    """UI のコードを読み、コンパイル結果を保持する。画面の部品はまだ作らない。"""
    name = ui_name.strip()
    cached = _PREPARED.get(name)
    if cached is not None:
        return cached
    prepared = PreparedUI()
    _PREPARED[name] = prepared
    try:
        if not name or name.lower() in RESERVED_UI_NAMES:
            raise ValueError(f"UI名が不正です: {ui_name!r}")
        path = ui_dir() / f"{name}.py"
        if not path.exists():
            raise FileNotFoundError(f"UIファイルが見つかりません: {path}")
        source = path.read_text(encoding="utf-8")
        if _is_class_ui(source):
            module = _load_ui_module(name, path)
            ui_class = getattr(module, "UI", None)
            if ui_class is None or not issubclass(ui_class, BaseUI):
                raise TypeError(f"{name} に BaseUI を継承した UI クラスがありません")
            prepared.is_class = True
            prepared.ui_class = ui_class
        else:
            prepared.script_code = compile(_wrap_script_source(source), str(path), "exec")
    except Exception as exc:
        prepared.error = exc
    return prepared


def preload_uis(names: Iterable[str]) -> None:
    seen: set[str] = set()
    for raw in names:
        name = (raw or "").strip()
        if not name or name.lower() in RESERVED_UI_NAMES or name in seen:
            continue
        seen.add(name)
        prepare_ui(name)


def _title_font_and_fg(design: dict[str, Any]) -> tuple[tuple, str]:
    font = design.get("title_font")
    if not (isinstance(font, tuple) and len(font) >= 2):
        family = str(design.get("title_font_family") or design.get("font_family") or "ＭＳ Ｐゴシック")
        try:
            size = int(design.get("title_font_size") or 20)
        except (TypeError, ValueError):
            size = 20
        font = (family, size)
    fg = str(design.get("title_text") or design.get("text") or "#000000")
    return font, fg


def _host_with_cui_title(parent, context: UIContext):
    """CUI のタイトルがあれば画面先頭に出す。文字は表示のカスタマイズに従う。"""
    title = str(context.title or "").strip()
    parent.columnconfigure(0, weight=1)
    if not title:
        parent.rowconfigure(0, weight=1)
        return parent
    parent.rowconfigure(0, weight=0)
    parent.rowconfigure(1, weight=1)
    font, fg = _title_font_and_fg(context.design)
    bg = str(context.design.get("background") or "#f0f0f0")
    label = tk.Label(
        parent,
        text=title,
        font=font,
        fg=fg,
        bg=bg,
        anchor="n",
        justify="center",
    )
    label.grid(row=0, column=0, sticky="new", padx=16, pady=(20, 35))

    def _apply_wrap(_event: tk.Event | None = None) -> None:
        try:
            width = int(parent.winfo_width())
        except tk.TclError:
            return
        if width < 40:
            return
        set_wraplength(label, max(1, width - 32))

    parent.bind("<Configure>", _apply_wrap, add="+")
    parent.after_idle(_apply_wrap)
    host = ttk.Frame(parent)
    host.grid(row=1, column=0, sticky="nsew")
    host.columnconfigure(0, weight=1)
    host.rowconfigure(0, weight=1)
    return host


def create_ui(ui_name: str, parent, context: UIContext) -> BaseUI:
    name = ui_name.strip()
    prepared = prepare_ui(name)
    if prepared.error is not None:
        raise prepared.error
    host = _host_with_cui_title(parent, context)
    if prepared.is_class:
        ui_class = prepared.ui_class
        if ui_class is None:
            raise TypeError(f"{name} に BaseUI を継承した UI クラスがありません")
        module = sys.modules.get(ui_class.__module__)
        if module is not None:
            bind_runtime(module, context)
        ui = ui_class(host, context)

        def _class_done(*values: Any) -> None:
            if values:
                payload = values[0] if len(values) == 1 else list(values)
                context.write_log(payload)
                ui.state = payload
            ui.ready = True

        if module is not None:
            bind_runtime(module, context, done=_class_done)
        ui.build()
        ui._notify()
        return ui
    if prepared.script_code is None:
        raise TypeError(f"{name} のスクリプトを実行できません")
    runner, namespace = _runner_from_code(prepared.script_code)
    ui = TkScriptUI(host, context, runner, namespace)
    ui.build()
    return ui


def _load_ui_module(name: str, path: Path):
    """exe 内蔵の ui.base を使いつつ、exe 隣の ui/名前.py をファイルとして読み込む。"""
    mod_name = f"kamishivy_plugin_{name}"
    existing = sys.modules.get(mod_name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"UIモジュールを読み込めません: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module
