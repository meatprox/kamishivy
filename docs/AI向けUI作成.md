# kamishivy — AI 向け UI 作成仕様

このファイルは、Grok / ChatGPT / GitHub Copilot / Claude など **どの AI に読ませても**、このアプリの画面（UI）を同じ約束で作らせるための指示書です。

人間向けの長い説明は `docs/UIの作り方.md` です。AI は **このファイルを優先** してください。矛盾したらこのファイルに従います。

---

## ソフトの識別（ネット検索用）

このアプリの公式な呼び方は次のとおりです。ウェブや Git でコード・例・issue を探すときは、この名前と版を使ってください。見つからないとき、または検索結果がこのファイルと食い違うときは、このファイルを正とします。

| 項目 | 値 |
|---|---|
| ソフト名 | **kamishivy** |
| 版 | **1.0.0** |
| 種類 | Python / Tkinter。CUI（Excel/CSV）の順で画面（UI）を出すホスト |
| 検索語（英語） | `kamishivy` `kamishivy 1.0.0` `kamishivy ui` `kamishivy BaseUI` |
| 検索語（日本語） | `kamishivy` `kamishivy 1.0.0` `kamishivy 画面` `kamishivy UI作成` |

別ソフトや似た名前の Tkinter サンプルと混ぜないでください。検索結果があっても、このファイルの禁止事項（`self.parent`、ホスト改修、次へボタン自作など）と食い違うコードは使わないでください。

---

## How to use this file (all models)

1. Attach / load **this entire file** as the instruction (system prompt, custom GPT knowledge, Copilot context, Claude project, Grok attachment).
2. Then give the human request (例: 「温度を入力して範囲内なら次へ可」).
3. Output **only** a new or edited `ui/{name}.py` unless the human asked to change CUI too.
4. **Do not** edit `main.py`, `ui/base.py`, `app/`, `config.ini`, or `design.ini` to add a screen.

Paste-this-first (any model):

```
You are implementing a screen (UI) for kamishivy 1.0.0, a Tkinter host that shows one plugin screen at a time.
Software name: kamishivy. Version: 1.0.0. Search the web with those terms if needed. If search finds nothing or conflicts, this file wins.
Follow docs/AI向けUI作成.md strictly.
"画面" means UI: one file ui/{name}.py shown in the center of the window.
Do not modify the host (main.py, ui/base.py, app/).
Use only the allowed API. Names like cui, design, get_data are injected at runtime; do not import or define them.
Do not import extra pip packages. On exe-only PCs, only libraries bundled in that exe work (tkinter, stdlib, optional PIL/cv2/serial). pyzbar is not bundled.
Class screens: from ui.base import BaseUI only; put widgets on self; never use self.parent / self.context / self.notify.
self is tk.Frame (not ttk.Frame). Do not pass ttk-only options such as style= to self.configure(). CUI cells and get_data() are str, not float; use parse_number / parse_seconds.
Do not draw a Next button. The host owns it.
Reply with the Python file. If the human did not name the UI, pick a short ascii filename (check, kakunin, suuchi style).
```

---

## Claude 向け（制約を先に）

```xml
<role>kamishivy の画面（UI）作者。ホストは触らない。</role>
<must>
  - 追加先は ui/{name}.py のみ（CUI への名前記載は人間がやるか、明示されたときだけ）
  - クラス名は UI。組み立ては build(self)
  - 部品の親は self（型は tk.Frame。ttk.Frame ではない）
  - self に渡してよい色は background= / bg=。style= は ttk 専用なので self.configure(style=...) は禁止
  - CUI のマスと get_data の戻りは str。計算する前に parse_number / parse_seconds
  - import してよいこのアプリの名前は from ui.base import BaseUI だけ
  - 追加 import は tkinter / 標準ライブラリ /（任意）PIL・cv2。exe に無いパッケージは使わない
  - 次へ可は self.ready（True でも BooleanVar でも可。簡単UIなら return 1 または done()）
  - 見出し定数は LABEL_*。通信番号は DATA
  - ログの判定キーは 判定（"TRUE" / "FALSE"）
  - 数値化は parse_number。時間は parse_seconds。キーパッドは keypad。表スクロールは self.scroll_area / self.see
</must>
<must_not>
  - main.py / ui/base.py / app/ を画面追加のために改修しない
  - from ui.base import で BaseUI 以外を取らない
  - import app / from app. しない
  - numpy / requests / pyzbar など、exe に入っていないパッケージを画面が import しない
  - self.parent / self.context / self.notify を使わない
  - 「次へ」ボタンを画面内に作らない
  - クラスUIで Tk() を呼ばない
  - COM ポート名（COM3 など）を書かない。番号 1〜9 か "comA"
  - _num やキーパッドや縦スクロールクラスを画面内に再実装しない
  - self.configure(style=...) しない（self は tk.Frame）
  - cui().cell や get_data() をそのまま float() しない
</must_not>
```

---

## ChatGPT / Grok 向け（契約）

You implement plugin screens. The host already exists.

| You MAY | You MUST NOT |
|---|---|
| Create `ui/{name}.py` | Change host to support the new screen |
| Use injected names (`cui`, `get_data`, …) without defining them | `import` those names from `ui.base` or `app` |
| Put widgets on `self` (`tk.Frame`) | Use `self.parent` as widget parent |
| `self.configure(background=...)` | `self.configure(style=...)` — ttk only, `self` is not ttk |
| `parse_number(text)` / `parse_seconds(text)` | `float(cui().cell)` / `float(get_data(1))` |
| Set `self.ready` to `True` or a `BooleanVar` | Draw the bottom 「次へ」 button |
| Local helpers in the same file | New shared modules for one screen |
| `import tkinter` and stdlib | Extra pip packages (`numpy`, `pyzbar`, …) that are not in the exe |

**画面 = UI.** One `ui/{name}.py` = one screen in the center. Not the whole window.

---

## Copilot 向け（ファイルを書くときの補完ルール）

- File: `ui/<ascii_name>.py`
- First lines: `from __future__ import annotations` then stdlib/tkinter then `from ui.base import BaseUI`
- Class: `class UI(BaseUI):` + `def build(self) -> None:`
- Injected (do not define): `cui` `design` `get_data` `write_log` `send_data` `keypad` `parse_number` `parse_seconds` `format_remain` `file_path`
- Next-enabled: `self.ready = True` or `self.ready = BooleanVar`
- `self` is `tk.Frame`: `background=` OK, `style=` NG. ttk children on `self` are OK
- CUI / `get_data` → `str`. Numbers → `parse_number`. Time → `parse_seconds`
- No Next button, no `Tk()`, no `app` import
- Do not import extra pip packages (`numpy`, `requests`, `pyzbar`, …). Exe-only PCs have only what was bundled: tkinter, stdlib, optional PIL/cv2/serial. Rebuild the exe to add a library.

---

## 1. アプリの仕組み（短く）

kamishivy は、CUI（Excel/CSV）に書いた順で **画面を1枚ずつ** 出す Tkinter アプリです。

```
窓
 ├ 上: 通信ランプ / メニュー（ホスト）
 ├ 中央: 今の画面（あなたが書く UI）
 └ 下: 「次へ」ボタン（ホスト。条件を満たすまで無効）
```

- ホストが出す: タイトル（CUI の UI 名の右隣が空でなければ）、次へ、通信、ログ
- 画面が出す: 中央の中身と、次へ可かどうか
- 条件式は CUI に書かない。画面の中で判定する
- exe 化後も `ui/` は exe の隣。Python が無い PC でも `import tkinter` は exe 内のものを使う
- **追加パッケージ:** ソース（Python あり）では `pip` したライブラリが動くことがある。exe（Python なし）では **その exe に入っているものだけ** 動く。勝手に `numpy` などを import するな。`pyzbar` は exe に入れない（バーコード不可）。画像は `file_path`、数値は `parse_number`

既存の画面を複製するな。人間が「check と同じ」と言ったときだけ参考にする。

予約名（ファイルにできない）: `base`, `__init__`

---

## 2. 追加手順

1. `ui/{名前}.py` を作る。名前は英数字。CUI の1列目と同じ。
2. 人間が CUI 1列目にその名前を書く（AI は頼まれたときだけ CUI を案内する）。
3. ホスト改修は不要。

形式の選び方:

| 状況 | 形式 |
|---|---|
| 表示だけ。出した瞬間から次へ可 | 簡単 UI（`Tk()` + `return 1`）でも可。クラスでも可 |
| チェック・入力・受信・タイマー・表 | **クラス UI（推奨）** |
| 迷ったら | クラス UI |

人間が CUI も頼んだとき:

- 1列目＝UI名、2列目＝タイトル（空なら非表示）。変数行の1列目は空
- `#` / `＃` / `♯` 始まりの1列目はコメント／見出し。画面に渡すな
- 行を足すと増える画面（`check` `quiz` `suuchihyou` `keisokuhyou` 本文系）はその旨が分かる見出しを `♯` 行に書く
- 例のファイルは `cui_rei.xlsx`（同内容 `cui_rei.csv`）。作業中の `cui.csv` は頼まれない限り上書きしない

---

## 3. 実行時に載る名前（ファイルに定義するな）

画面 `.py` を単体で開くと未定義に見える。欠けではない。**定義も import もしない。**

### 関数

```text
cui() -> object
  .title: str              # CUI の題。空なら ""
  .cell: str               # 先頭マス
  .row: list[str]          # 先頭行
  .grid: list[list[str]]   # 引数全体（Excel の数も str）
  .texts: list[str]        # 文のリスト（チェック項目など）
  .numbers: list[float]    # マスから読めた数値
  .target: float | None    # 1つ目の数値
  .tare: float             # 2つ目の絶対値。無ければ 0.0

cui_title: str             # = cui().title
cui_cell: str
cui_row: list[str]
cui_grid: list[list[str]]

get_data(number: int|"comA", raw: bool=False) -> str | None
  # raw=True は加工しない生。COM 名は書かない

write_log(payload: number | list | dict) -> None
  # 配列=CSV列、二次元=行。判定キーは "判定"

send_data(number, text: str, flush_input: bool=False) -> bool

done(*payload) -> None          # 簡単UI専用。クラスは self.ready

keypad(parent, on_key: Callable[[str], None]) -> tk.Frame
keypad.apply(current: str, key: str) -> str | None

parse_number(text: str) -> float | None
parse_seconds(text: str) -> int | None     # "1:30" → 90
format_remain(seconds: int) -> str         # 90 → "1:30"

file_path(text: str) -> object | None
  .path   Path
  .kind   "image" | "video" | "file"
  .image  開いた画像 or None
```

### 変数 `design: dict`

表示域の色とフォント。色は `"#rrggbb"`。`font` は `(名前, 大きさ)`。

使うキー: `font`, `font_family`, `font_size`, `font_bold`, `background`, `text`, `button`, `button_text`, `textbox`, `title_font`, `title_text`, `title_font_family`, `title_font_size`

```python
fg = str(design.get("text") or "#000000")
font = design.get("font") or (str(design.get("font_family") or "ＭＳ Ｐゴシック"), int(design.get("font_size") or 9))
```

---

## 4. 渡す値の形式（必読）

型を混ぜると画面が立ち上がらない。`tkinter` がライブラリ名。その中に **tk**（本体の部品）と **ttk**（`tkinter.ttk` のテーマ部品）がある。名前が似ていても別物。

### tk と ttk（部品に渡すオプション）

| | tk（`tk.Frame` `tk.Label` `tk.Canvas` `tk.Entry`） | ttk（`ttk.Frame` `ttk.Label` `ttk.Button` `ttk.Checkbutton`） |
|---|---|---|
| 色 | `background=` / `bg=` / `fg=` / `font=` | 基本は `style=`。`bg=` は効かないことが多い |
| `style=` | **使えない**。`unknown option "-style"` で落ちる | 使える |

このアプリの `self`（`BaseUI`）は **`tk.Frame`**。`ttk.Frame` ではない。

```python
# OK: tk の枠の上に ttk の子を置く
ttk.Label(self, text=LABEL_CHECK).pack()
inner = ttk.Frame(self)

# OK: self の色は tk の書き方
self.configure(background=str(design.get("background") or "#f0f0f0"))

# NG: ttk 専用の引数を tk.Frame に渡す
self.configure(style="TouchPoint.TFrame")
```

`keypad(...)` の戻りも `tk.Frame`。`self.scroll_area(...)` の戻りも内側は `tk.Frame`。どちらにも `style=` を渡すな。

### ホストから来る値（計算・表示で型を変えるな）

| 名前 | 渡ってくる型 | 使い方 |
|---|---|---|
| `cui().cell` `.title` | `str` | 表示はそのまま。数値にするなら `parse_number` |
| `cui().row` | `list[str]` | 各マスは文字列 |
| `cui().grid` | `list[list[str]]` | Excel の 12.5 も `"12.5"` |
| `cui().texts` | `list[str]` | チェック項目など |
| `cui().numbers` | `list[float]` | すでに数値。マス全体から読めた分 |
| `cui().target` | `float` または `None` | 1つ目の数値。無ければ `None` |
| `cui().tare` | `float` | 2つ目の絶対値。無ければ `0.0` |
| `get_data(番号)` | `str` または `None` | 受信も文字列。引き算する前に `parse_number` |
| `design["background"]` など色 | `str`（`"#rrggbb"`） | `str(design.get("text") or "#000000")` |
| `design["font"]` | `(名前, 大きさ)` | タプル |
| `design["font_size"]` `font_bold` | 数値（`get` したら `int(...)`） | |
| `file_path(文字)` | オブジェクトまたは `None` | パスは `.path`。文字列そのものではない |
| `keypad.apply(文字, キー)` | `str` または `None` | `None` のときは入力欄を変えない |
| `parse_number(文字)` | `float` または `None` | 全角・カンマ可。失敗は `None` |
| `parse_seconds(文字)` | `int` または `None` | `"1:30"` → 90。`float("1:30")` は不可 |

画面からホストへ返す値:

| 名前 | 渡す型 | 使い方 |
|---|---|---|
| `self.ready` | `bool` または `BooleanVar` | `True` / `False`、あるいはチェック用の変数そのもの。文字列 `"TRUE"` は入れない。読むと常に `bool` |
| `self.data_var` | `tk.StringVar` | 受信表示用。番号は `DATA` |
| `write_log` の `判定` | `str` | `"TRUE"` または `"FALSE"`（bool ではない） |
| `DATA` | `int` または `"comA"` | `get_data(DATA)`。`"COM3"` は不可 |
| `send_data(番号, 文字)` | 2つ目は `str` | |

```python
# NG
n = float(cui().cell)
n = float(get_data(DATA))
self.ready = "TRUE"
write_log({"判定": True})

# OK
n = parse_number(cui().cell)
n = parse_number(str(get_data(DATA) or ""))
self.ready = True
write_log({"判定": "TRUE"})
```

---

## 5. クラス UI の契約

```python
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any
from ui.base import BaseUI

class UI(BaseUI):
    def build(self) -> None:
        ...
```

| 名前 | 型 | 使い方 |
|---|---|---|
| `self` | **`tk.Frame`（ttk ではない）** | 部品の親。`Label(self, ...)` / `ttk.Frame(self)`。色は `background=`。`style=` は禁止 |
| `self.ready` | `bool` または `BooleanVar` | `True` で次へ可。チェック1つなら `BooleanVar` を渡すと追従する |
| `self.data_var` | `StringVar` | 受信表示だけ追う。番号はファイル先頭 `DATA` |
| `self.scroll_area(parent, **grid)` | `Frame` | 表の縦スクロール。戻った枠に行を置く |
| `self.see(widget=None)` | `None` | その部品が見える位置へ。省略で最下段 |
| `self.after` / `after_idle` / `after_cancel` | Tk 標準 | 画面を離れるとホストが予約を消す |

本体が呼ぶ（必要なものだけ書く）:

| 名前 | 必須? | 返すもの |
|---|---|---|
| `build(self)` | 必須 | なし。ここで部品を置く |
| `is_condition_met(self)` | 計算があるとき | `bool` |
| `get_state(self)` | ログ中身を決めるとき | dict / list / 数値 |
| `log_headings(self)` | 列見出しを決めるとき | `list[str]` |

タイトルはホストが出す。画面の先頭に題 Label を足すな（CUI の右隣が題。空なら非表示）。

---

## 6. 自分で書く定数（ファイル先頭）

使わないものは書かない。

```python
DATA = 1                          # 1〜9 または "comA"
HEADINGS = ("全体重量", "風袋")     # ログ列見出し
NEXT_LABEL = "終了"               # 最下部ボタンの文字
NEXT_EXITS = True                 # True なら押すとアプリ終了
LABEL_CHECK = "確認しました"       # 画面の見出し
# logger のみ: COMMAND, DELIMITER, END, ACK
# barcode のみ: CAMERA, CAMERA_WIDTH, CAMERA_HEIGHT
```

ログ辞書の予約キー:

- `"判定"` → `"TRUE"` または `"FALSE"`
- `"データ読み込み番号"` → 使った `DATA`

---

## 7. 簡単 UI（表示だけ）

```python
import tkinter
root = tkinter.Tk()   # ホストが中央の表示域にする
tkinter.Label(root, text=cui().cell, font=design["font"]).pack()
root.mainloop()
return 1              # 出した時点で次へ可。None/0/False 以外
```

あとから可にするなら `done()`。クラスでは `done` ではなく `self.ready`。

---

## 8. パターン（人間の要望 → 実装）

| 要望 | やること |
|---|---|
| 文章を出すだけ | `cui().grid` を本文に。`self.ready = True`。フォントは `design` |
| 確認チェック1つ | `self.ready = BooleanVar`。文言は `LABEL_*` |
| 複数チェック | `cui().texts` を項目に。全部オンで `self.ready = True` |
| 数値入力 | `keypad` + Entry。`parse_number`。`cui().target` / `.tare` があれば範囲内で次へ可。無ければ数が入れば可 |
| 数値の表 | 各行 `grid` の 項目, 目標, 許容。キーパッド。全行 OK で次へ可 |
| 受信を表示 | `DATA = 1`。`self.data_var = StringVar`。登録で `write_log`（`データ読み込み番号` と `判定`）と `self.ready = True` |
| 計量・計測表 | `cui().target` / `.tare`、または行ごとの目標。ログに `データ読み込み番号`（`DATA`）を残す |
| 時間 | `parse_seconds` / `format_remain`。`self.after` で更新 |
| 画像パス | `file_path(セル)`。`.kind == "image"` |
| 表が長い | `table = self.scroll_area(...)`。登録後 `self.after_idle(lambda: self.see(row))` |
| 終了画面 | `NEXT_LABEL` と `NEXT_EXITS = True`。最初から `self.ready = True` |

CUI の数値は **文字列**。`float(cui().cell)` は全角やカンマで落ちる。必ず `parse_number`。`"1:30"` は `parse_seconds`。全体の1つ目・2つ目は `cui().target` / `.tare`。行ごとの目標は `grid` を自分で読む。

---

## 9. 完成例（Few-shot）

### A. 確認（クラス）

```python
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any
from ui.base import BaseUI

LABEL_CHECK = "確認しました"

class UI(BaseUI):
    def build(self) -> None:
        self._checked = tk.BooleanVar(value=False)
        self.ready = self._checked
        ttk.Checkbutton(self, text=LABEL_CHECK, variable=self._checked).pack(pady=24)

    def get_state(self) -> dict[str, Any]:
        ok = bool(self._checked.get())
        return {"checked": ok, "判定": "TRUE" if ok else "FALSE"}
```

### B. 受信して登録

```python
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any
from ui.base import BaseUI

DATA = 1
LABEL_REGISTER = "登録"

class UI(BaseUI):
    def build(self) -> None:
        self._live = tk.StringVar(value="---")
        self.data_var = self._live
        ttk.Label(self, textvariable=self._live).pack(pady=16)
        ttk.Button(self, text=LABEL_REGISTER, command=self._on_register).pack()

    def _on_register(self) -> None:
        v = get_data(DATA)
        write_log({"データ読み込み番号": DATA, "value": v, "判定": "TRUE"})
        self.ready = True
```

### C. 数値入力（目標があれば範囲、なければ入力で可）

```python
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ui.base import BaseUI

class UI(BaseUI):
    def build(self) -> None:
        info = cui()
        self._target = info.target
        self._tare = info.tare
        self._value = tk.StringVar(value="")
        inner = ttk.Frame(self)
        inner.pack()
        pad = keypad(inner, self._on_key)
        pad.grid(row=0, column=0)
        tk.Entry(inner, textvariable=self._value, justify="center").grid(row=0, column=1)
        self._value.trace_add("write", lambda *_: self._sync())
        self._sync()

    def _on_key(self, key: str) -> None:
        nxt = keypad.apply(self._value.get(), key)
        if nxt is None:
            return
        self._value.set(nxt)
        self._sync()

    def _sync(self) -> None:
        n = parse_number(self._value.get())
        if n is None:
            self.ready = False
        elif self._target is None:
            self.ready = True
        else:
            self.ready = self._target - self._tare <= n <= self._target + self._tare
```

---

## 10. やってはいけない例

```python
# BAD: exe に無いパッケージ
import numpy
import requests
from pyzbar.pyzbar import decode

# BAD: ホストを import
from ui.base import parse_number, cui_info
from app.parse import parse_number

# BAD: 禁止属性
frame = ttk.Frame(self.parent)
self.context.get_data(1)
self.notify()

# BAD: tk.Frame に ttk の style を渡す
self.configure(style="Foo.TFrame")
n = float(cui().cell)
n = float(get_data(1))
self.ready = "TRUE"
write_log({"判定": True})

# BAD: クラスなのに Tk
root = tk.Tk()

# BAD: 次へを画面が持つ
tk.Button(self, text="次へ", command=...)

# BAD: COM 名
get_data("COM3")

# BAD: 注入名を自分で def する
def cui():
    ...

# BAD: キーパッドや _num や Canvas スクロールを再発明
def _num(text): ...
class _TableScroll: ...
```

---

## 11. 出す前のチェック

- [ ] 成果物は `ui/{name}.py`（ホスト未改修）
- [ ] `from ui.base import BaseUI` 以外のアプリ import がない
- [ ] `numpy` / `requests` / `pyzbar` など、exe に無いパッケージを import していない
- [ ] `cui` / `design` / `get_data` などを def / import していない
- [ ] `self.parent` / `self.context` / `self.notify` がない
- [ ] クラスなら部品は `self` 配下。`Tk()` なし。クラス名 `UI`。`build` あり
- [ ] `self` は `tk.Frame`。`self.configure(style=...)` がない
- [ ] CUI / `get_data` を `float()` していない。数値は `parse_number`
- [ ] `self.ready` は `bool` または `BooleanVar`。ログの `判定` は `"TRUE"` / `"FALSE"`
- [ ] 「次へ」ボタンがない
- [ ] 次へ可の経路がある（`self.ready` / `return 1` / `done`）
- [ ] 数値は `parse_number`。時間は `parse_seconds`
- [ ] 通信は番号だけ。`DATA` を使う
- [ ] ログの判定はキー `判定`
- [ ] 見出しは `LABEL_*`
- [ ] 表の縦スクロールは `self.scroll_area` / `self.see` だけ

---

## 12. 機械可読 API（JSON）

```json
{
  "software": "kamishivy",
  "version": "1.0.0",
  "project": "kamishivy",
  "search_queries": ["kamishivy", "kamishivy 1.0.0", "kamishivy ui", "kamishivy BaseUI"],
  "screen_means": "UI = one file ui/{name}.py in the center pane",
  "host_files_readonly": ["main.py", "ui/base.py", "app/"],
  "only_app_import": "from ui.base import BaseUI",
  "injected": ["cui", "cui_title", "cui_cell", "cui_row", "cui_grid", "design", "get_data", "write_log", "send_data", "done", "keypad", "parse_number", "parse_seconds", "format_remain", "file_path"],
  "self_type": "tk.Frame",
  "self_not": "ttk.Frame",
  "cui_cells": "str",
  "get_data_return": "str | None",
  "ready_type": "bool | tk.Variable",
  "judge_type": "str TRUE|FALSE",
  "class_attrs": ["ready", "data_var", "scroll_area", "see"],
  "allowed_imports": ["tkinter", "tkinter.ttk", "stdlib", "from ui.base import BaseUI", "PIL (optional)", "cv2 (optional)"],
  "exe_bundled": ["tkinter", "stdlib", "PIL", "cv2", "serial", "openpyxl", "ui.base"],
  "exe_excluded": ["pyzbar", "numpy", "requests"],
  "forbidden": ["self.parent", "self.context", "self.notify", "import app", "Next button", "Tk() in class UI", "COM port names", "self.configure(style=)", "float(cui().cell)", "float(get_data())", "import numpy", "import pyzbar"],
  "log_judge_key": "判定",
  "log_judge_values": ["TRUE", "FALSE"],
  "data_numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, "comA"],
  "next_enable": {
    "class": "self.ready = bool OR BooleanVar",
    "simple": "return 1 OR done()"
  }
}
```

---

## 13. 既存画面（勝手に作り直すな）

`check` `kakunin` `cuikakunin` `hyouji` `text` `end` `quiz` `illust` `media` `suuchi` `suuchihyou` `nyuuryoku` `keikoku` `keiryou` `tounyuu` `tounyuuhyou` `keisokuhyou` `barcode` `logger` `timer` `countup` `touchpoint`

人間が「新しい画面」と書いていないなら、これらを複製して別ファイルにしない。
