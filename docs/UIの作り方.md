# UI の作り方

このアプリに **画面（UI）** を追加する人向けです。アプリ本体のプログラムは触りません。exe にすると本体のコードは見えなくなるので、ここに書いた名前だけで足ります。

AI（Grok / ChatGPT / Copilot / Claude など）に画面を作らせるときは、このファイルではなく **`docs/AI向けUI作成.md`** を読み込ませてください。

**覚えてよいのは次だけです。** それ以外のこのアプリの名前（`self.parent`、`self.context`、`self.notify`、土台からの import など）は使いません。足りない処理は、その画面のファイルの中で自分で関数を書いてください。

---

## 画面とは（UI のこと）

この説明での **画面** は、窓の中央に出る **1枚の UI** のことです。`ui` フォルダの `.py` が 1種類＝1画面です。

| 呼び方 | 何を指すか |
|---|---|
| **窓** | アプリ全体。メニューと「次へ」と中央の表示域がある |
| **画面（UI）** | 中央に出る 1枚。CUI の1列目に書いた名前の `.py` |
| **表示域** | 窓の中央。今の画面が出る場所 |
| **アプリ本体** | 窓・「次へ」・通信・ログを動かしている側。exe に入っている |
| **CUI** | 画面の順番と引数を書いた Excel（基本は `cui.xlsx`）または CSV |
| **次へ** | 窓の一番下のボタン。条件を満たすまで押せない |
| **データ番号** | 通信の相手。`1`〜`9` と `comA`。COM ポート名は使わない |
| **土台クラス（`BaseUI`）** | クラス形式の画面が継承する親。`from ui.base import BaseUI` **だけ** import してよい |

CUI の1列目に `check` と書けば `ui/check.py` が1画面として出ます。次の行のマスがその画面への引数です。

---

## ファイルに定義がない名前について

画面の `.py` を単体で開くと、`cui` や `design`、`get_data` などに `def` も import もありません。これは欠けではなく、**実行時に本体が載せます。** 自分で定義しないで使ってください。

クラス形式では `from ui.base import BaseUI` 以外に、このアプリのモジュールは import しません。

---

## import してよいもの（Python がある PC と、exe だけの PC）

画面の `.py` は、Python が入った PC（ソース起動）でも、入っていない PC（exe 起動）でも同じファイルを使います。exe のときは **exe の中の Python** が動くので、配布先に Python は不要です。

ただし **`import` できる範囲が違います。**

| import | Python あり（ソース） | Python なし（exe） |
|---|---|---|
| `tkinter` / `tkinter.ttk` | 使える | 使える（exe に入っている） |
| 標準ライブラリ（`math` `time` `pathlib` など） | 使える | 使える |
| `from ui.base import BaseUI` | 使える | 使える |
| `PIL`（画像） / `cv2`（動画・カメラ） / `serial` | PC に入れてあれば使える | **exe を作ったときに入っていれば** 使える |
| `pyzbar`（バーコード） | 入れてあれば使える | **使えない**（exe に入れない） |
| その他（`numpy` `requests` など） | `pip` すればソースでは動くことがある | **動かない** |

**勝手に別パッケージを `import` しないでください。** 自分の PC では動いても、exe を配った先ではそのライブラリが入っていないことが多いです。新しく使うライブラリは、**ビルドした exe に入っているものだけ** が、Python の無い PC でも動きます。exe に無いものを足したいときは、画面だけでは足りず、本体の exe の作り直しが必要です。

迷ったら `tkinter` と標準ライブラリと、この説明の関数だけにしてください。画像は `file_path`、数値は `parse_number` を使います。

---

## 1. 追加の手順

1. `ui/{名前}.py` を作る
2. CUI の1列目にその名前を書く

簡単な形式（素の Tkinter + `return`）と、クラス形式（`BaseUI`）があります。どちらでも下の関数・変数は使えます。

---

## CUI の書き方

Excel（`cui.xlsx`）が基本です。CSV でも読めます。変数の説明入りの例は **`cui_rei.xlsx`**（同じ内容の `cui_rei.csv`）です。

- 1列目＝呼び出す UI 名（1回の起動につき1つ）。2列目＝タイトル（空なら非表示）
- 変数・ラベルは UI 名の次の行から。その行の1列目は空ける
- 1列目が `#`・`＃`・`♯` で始まる行はコメント／見出しで、画面には渡りません
- UI 名の直後の `♯` 行は、変数の見出しです
- 空行・空列と、行の右端の空セルは読み飛ばします

**下に行を足すと項目が増える画面**（`check`、`quiz`、`suuchihyou`、`keisokuhyou`、`text` / `end` / `keikoku` の本文、`illust` / `media` のマス）は、見出しにその旨を書いておくと分かります。`tounyuuhyou` は CUI の行では増えず、画面で登録すると表が増えます。

COM を使う画面の番号は、各ファイル先頭の `DATA` です。ログに残すときはキー **`データ読み込み番号`**（`keiryou` や `keisokuhyou` と同じ）。

---

## 2. 関数（本体が載せる）

簡単な形式でもクラス形式でも、同じ名前です。

### `cui()` → 情報オブジェクト

今の画面に渡された CUI の引数をまとめて返します。Excel の数値も **文字列** です。足し算の前に `parse_number` で数値へ直してください。

```python
info = cui()
info.title      # str  題。CUI の UI 名の右隣。空なら ""
info.cell       # str  先頭マス。無ければ ""
info.row        # list[str]  先頭行（空マスは下の同じ列で埋まる）
info.grid       # list[list[str]]  引数全体
info.texts      # list[str]  チェック項目など、文のリスト
info.numbers    # list[float]  マスから読めた数値
info.target     # float | None  1つ目の数値。無ければ None
info.tare       # float  2つ目の数値の絶対値。無ければ 0.0
```

```python
tkinter.Label(self, text=cui().cell).pack()
if cui().target is not None:
    lo = cui().target - cui().tare
    hi = cui().target + cui().tare
```

空行・コメント行は渡る前に落ちています。`=` を含むマスは数値としては数えません。表のように「行ごとに項目名・目標・許容」があるときは `cui().grid` を自分で読んでください。時間（`"1:30"` など）は数値ではないので `parse_seconds` を使います。

別名（関数ではなく、すでに入っている変数）:

- `cui_title` … `cui().title` と同じ `str`
- `cui_cell` … `cui().cell` と同じ `str`
- `cui_row` … `cui().row` と同じ `list[str]`
- `cui_grid` … `cui().grid` と同じ `list[list[str]]`

### `get_data(番号, raw=False)` → 文字または `None`

指定したデータ番号の、今の受信値です。まだ来ていなければ `None`。メニュー「通信データの加工」を通した値が返ります。加工しない生の文字が要るときだけ `raw=True` にします。

- 番号: `1`〜`9` または `"comA"`（COM ポート名は書かない）

```python
v = get_data(1)                 # 加工後。無ければ None
raw = get_data(1, raw=True)     # 生の文字
live = get_data(DATA)           # ファイル先頭の DATA を使うとき
```

### `write_log(内容)` → なし

本体へデータを渡し、ログに残します。数値ひとつでも、配列でも、辞書でも渡せます。配列は CSV の列方向、二次元配列は行方向に並びます。途中の記録も、確定の記録もこれです。

判定を自分で書くときはキー名 **`判定`** に `"TRUE"` または `"FALSE"`。データ番号を残すときは **`データ読み込み番号`**。

```python
write_log(12.5)
write_log([100, 20, 80])
write_log({"データ読み込み番号": DATA, "value": v, "判定": "TRUE"})
```

### `send_data(番号, 文字)` → 成功なら真

機器へ文字を送ります。通信する画面だけ使います。必要なら `flush_input=True` で、送る前に受信バッファを捨てられます。

```python
send_data(1, "D01\r\n")
send_data(DATA, "D01\r\n", flush_input=True)
```

### `done()` / `done(内容)` → なし

**簡単な UI 用**です。呼んだ瞬間から「次へ」が押せます。引数を渡すと、その内容をログにも残します。クラス形式では `self.ready = True` を使います。

```python
done()
done({"value": v})
```

最初から次へ可にするだけなら、ファイルの末尾で `return 1` でも同じです（`None` / `0` / `False` 以外なら可）。

### `keypad(親, 押したとき)` → `tk.Frame`

数値キーパッドを作ります。`親` はその部品を置く枠。`押したとき` は、キーの文字（`"7"` や `"C"`、`"←"`、`"⏎"`）を受け取る関数です。見た目は `design` に従います。

入力欄の文字をキーに合わせて直すときは `keypad.apply(今の文字, キー)` です。戻りは新しい文字（`str`）。小数点が二重になるなど無効なときは `None` なので、そのときは書き換えません。

```python
self._pad = keypad(inner, self._on_key)
self._pad.grid(row=0, column=0)

def _on_key(self, key: str) -> None:
    next_text = keypad.apply(self._value.get(), key)
    if next_text is None:
        return
    self._value.set(next_text)
```

### `parse_number(文字)` → `float` または `None`

文字を数値にします。全角数字・カンマも読みます。空や途中入力（`"."` や `"-"`）や読めない文字は `None` です。

```python
n = parse_number("１２.５")   # 12.5
n = parse_number(self._value.get())
if n is None:
    return
```

### `parse_seconds(文字)` → `int` または `None`

時間の文字を秒にします。`"1:30"` → 90、`"1:00:00"` → 3600。ただの数はその秒。`0.5` のように 0 より大きく 1 未満なら日として秒に直します。読めなければ `None`。

```python
sec = parse_seconds(cui().cell)
if sec is None:
    raise ValueError("設定時間がありません")
```

### `format_remain(秒)` → `str`

秒を表示用の文字にします。1時間未満は `"1:30"`、1時間以上は `"1:00:00"`。

```python
label = format_remain(90)   # "1:30"
```

### `file_path(文字)` → 情報オブジェクト または `None`

マスの文字をファイルパスとして読みます。`file:` 付きや相対パスも扱います。ファイルでも画像でも動画でもなければ `None`。

```python
info = file_path(cui().cell)
if info is None:
    raise ValueError("パスがありません")
info.path    # Path  解決済みの場所
info.kind    # str   "image" / "video" / "file"
info.image   # 画像なら開いた画像。動画や失敗は None
```

---

## 3. 変数（本体が載せる）

### `design` … `dict`

表示のカスタマイズ（表示域）の色とフォントです。色は `"#rrggbb"`。フォントは `(名前, 大きさ)` の組です。

| キー | 型 | 意味 |
|---|---|---|
| `font` | `(名前, 大きさ)` | 表示域の文字 |
| `font_family` | `str` | フォント名 |
| `font_size` | `int` | 大きさ |
| `font_bold` | `int` | 太字なら 1 |
| `background` | `str` | 背景色 |
| `text` | `str` | 文字色 |
| `button` | `str` | ボタンの背景 |
| `button_text` | `str` | ボタンの文字色 |
| `textbox` | `str` | 入力欄の背景 |
| `title_font` | `(名前, 大きさ)` | 題の文字 |
| `title_text` | `str` | 題の色 |
| `title_font_family` | `str` | 題のフォント名 |
| `title_font_size` | `int` | 題の大きさ |

```python
fg = str(design.get("text") or "#000000")
tk.Label(self, text="Hello", font=design.get("font"), fg=fg, bg=design.get("background")).pack()
```

---

## 4. クラス形式で置く名前

クラス名は必ず `UI`。画面を組み立てる関数は `build`（本体が一度呼びます）。部品の親は **`self`** です（土台が中央の枠そのもの）。

```python
from ui.base import BaseUI

class UI(BaseUI):
    def build(self) -> None:
        tkinter.Label(self, text=cui().cell, font=design["font"]).pack()
        self.ready = True
```

### `self.ready` … `bool` または `BooleanVar`

「次へ」が押せるかどうかです。

- `True` / `False` を入れると、その値になる。条件が変わったら入れ直す
- `BooleanVar` を入れると、そのオン／オフに追従する（チェック1つのとき。自分で入れ直さなくてよい）

読むと常に `bool` です（変数を渡していても、今のオン／オフが返る）。

```python
self.ready = True
self.ready = self.is_condition_met()

self._checked = tk.BooleanVar(value=False)
self.ready = self._checked
ttk.Checkbutton(self, text="確認しました", variable=self._checked).pack()
```

### `self.data_var` … `StringVar`

受信の表示だけ追うときに渡します。番号はファイル先頭の `DATA`。来た値がこの変数に入ります。

```python
self._live = tk.StringVar(value="---")
self.data_var = self._live
tk.Label(self, textvariable=self._live).pack()
```

### `self.scroll_area(親, ...)` → 部品を置く `Frame`

表が縦に収まらないときの枠です。戻った枠に見出しや行を置きます。`row=` などの grid 指定も渡せます。

```python
table = self.scroll_area(frame, background=bg, row=2, column=0, sticky="nsew")
ttk.Label(table, text="項目").grid(row=0, column=0)
```

### `self.see(部品=省略)` → なし

スクロールを、その部品が見える位置へ送ります。省略すると最下段です。登録した直後など、`after_idle` と組み合わせると確実です。

```python
self.see(row_label)
self.after_idle(self.see)   # 最下段
```

遅延実行は Tkinter 標準の `self.after(ミリ秒, 関数)` / `self.after_idle(関数)` / `self.after_cancel(予約)` です。画面を離れると土台が予約を取り消します。

---

## 5. 自分で書く定数（ファイル先頭）

本体が読みます。使わない画面では書かなくてよいです。

| 名前 | 型 | 意味 |
|---|---|---|
| `DATA` | `int` または `"comA"` | この画面が使うデータ番号。初期は `1` |
| `HEADINGS` | 文字列の組やリスト | ログの列見出し |
| `NEXT_LABEL` | `str` | 最下部ボタンの文字（例: 「終了」） |
| `NEXT_EXITS` | `bool` | `True` ならボタンでアプリを閉じる |
| `LABEL_*` | `str` | 画面に出す見出し。そのファイル専用 |
| `COMMAND` | `str` | `logger` が送るコマンド |
| `DELIMITER` | `str` | `logger` の配列の区切り。空なら分割しない |
| `END` | `str` | `logger` の受信の終わり。空なら改行読み |
| `ACK` | `str` | `logger` で、この応答の次を本データにする |
| `CAMERA` | `int` | `barcode` のカメラ番号。`0` が1台目 |
| `CAMERA_WIDTH` / `CAMERA_HEIGHT` | `int` | `barcode` の解像度 |

ログの判定キーは **`判定`**（`"TRUE"` / `"FALSE"`）です。TRUE/FALSE の代わりに日時を書くのは、記録確認の保存だけです。

---

## 6. 本体が呼ぶ関数（クラス形式で書いてよい）

必須なのは `build` だけです。あとは必要な画面だけ書きます。

| 名前 | いつ呼ばれるか | 返すもの |
|---|---|---|
| `build(self)` | 画面を出すとき、一度 | なし |
| `is_condition_met(self)` | 次へ可かを見るとき | `bool` |
| `get_state(self)` | ログに残す中身を取るとき | 辞書・配列・数値など |
| `log_headings(self)` | 列見出しを自分で決めるとき | 文字列のリスト |

条件の計算が要るときは `is_condition_met` を書き、変わったら `self.ready = ...` を代入します。途中の記録は `write_log`、最後に残す中身は `get_state` です。

---

## 7. 通信のまとめ

- 番号は `1`〜`9` と `comA` だけ。COM ポート名は使わない
- 読む: `get_data(1)`。生が要るとき `get_data(1, raw=True)`
- 送る: `send_data(1, "D01\r\n")`
- 表示だけ追う: `self.data_var = StringVar(...)`（番号は `DATA`）
- どの COM か、どう切るかはメニュー「通信」「通信データの加工」で人が設定する

---

## 8. 最小の例

簡単な UI（出した時点で次へ可）:

```python
import tkinter
root = tkinter.Tk()
tkinter.Label(root, text=cui().cell, font=design["font"]).pack()
root.mainloop()
return 1
```

- `Tk()` は中央の表示域になる
- `import` でこのアプリ専用のものを取り込む必要はない

クラス（チェックで次へ可）:

```python
import tkinter as tk
from tkinter import ttk
from ui.base import BaseUI

class UI(BaseUI):
    def build(self) -> None:
        self._checked = tk.BooleanVar(value=False)
        self.ready = self._checked
        ttk.Checkbutton(self, text="確認しました", variable=self._checked).pack(pady=24)
```

クラス（受信を表示し、登録でログ）:

```python
import tkinter as tk
from ui.base import BaseUI

DATA = 1

class UI(BaseUI):
    def build(self) -> None:
        self._live = tk.StringVar(value="---")
        self.data_var = self._live
        tk.Label(self, textvariable=self._live).pack()
        tk.Button(self, text="登録", command=self._on_register).pack()

    def _on_register(self):
        v = get_data(DATA)
        write_log({"データ読み込み番号": DATA, "value": v, "判定": "TRUE"})
        self.ready = True
```
