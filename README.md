# kamishivy 1.0.0

CUI（Excel / CSV）に書いた順で、画面（UI）を1枚ずつ出す Tkinter アプリです。

このファイルは **ソースコード** 向けです。exe の並べ方は配布フォルダの `README.md` と `docs/exe化後の構成.md` です。

## ライセンス

ソース（`main.py`、`app/`、`ui/`、説明書、CUI 例）は [MIT](LICENSE) です。exe 配布も同じ文面です。コード用と exe 用でライセンスを分ける必要はありません。

ライセンスが無いと、著作権はあるまま「他人はコピーも改変も再配布もできない」になります。自分だけ使うなら無くても動きます。ソースや `ui/*.py` を配るなら付けてください。各 `.py` の先頭に同じ文を書く必要はありません。このフォルダの `LICENSE` が全体に効きます。

## ソースから動かす

Python 3.11 系。

```
pip install -r requirements.txt
python main.py
```

画像・動画・カメラを使う画面は、その PC に Pillow と OpenCV が必要です。バーコード（`barcode`）はソース実行かつ `pyzbar` があるときだけ使えます。`pyzbar` は exe には入れません。

## 構成

| パス | 役割 |
|---|---|
| `main.py` | 窓・次へ・通信・CUI 読み込み |
| `app/` | 通信・ログ・デザイン・パス |
| `ui/` | 画面。CUI の1列目の名前と一致する `.py` |
| `ui/base.py` | クラス画面の土台。exe に入る |
| `config.ini` | 窓・通信・ログなどの設定。無ければ起動時の初期値 |
| `design.ini` | フォントと色。無ければ初期デザイン |
| `cui.xlsx` / `cui.csv` | 画面の順番と引数 |
| `cui_rei.xlsx` | 例示用 CUI |
| `docs/` | 説明書 |
| `kamishivy.spec` | exe の作り方 |

## 画面の追加

1. `ui/{名前}.py` を作る
2. CUI の1列目にその名前を書く

`main.py` は触りません。手順は `docs/簡単なUIの作り方.md`、詳細は `docs/UIの作り方.md`、AI に作らせるときは `docs/AI向けUI作成.md` です。

## exe を作る

```
pyinstaller kamishivy.spec
```

できた `kamishivy.exe` と同じ場所に `ui/`、CUI、`LICENSE`、説明書を置きます。ffmpeg と pyzbar は exe に入りません。
