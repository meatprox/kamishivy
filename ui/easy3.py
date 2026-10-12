import tkinter

# main から受け取るデータ番号。1〜9。comA は "comA"。
DATA = 1

root = tkinter.Tk()
mokuhyo = float(cui_row[0])
hani = float(cui_row[1])
now = tkinter.StringVar(value="---")

tkinter.Label(root, textvariable=now, font=("Yu Gothic UI", 40)).pack(pady=8)
tkinter.Label(root, text="目標値  " + cui_row[0], font=("Yu Gothic UI", 16)).pack(pady=8)
btn = tkinter.Button(root, text="登録", state="disabled")


def tick():
    try:
        v = get_data(DATA)
        now.set("---" if v in (None, "") else str(v))
        try:
            n = float(v)
            ok = mokuhyo - hani <= n <= mokuhyo + hani
        except (TypeError, ValueError):
            ok = False
        btn.config(state="normal" if ok else "disabled")
        root.after(200, tick)
    except tkinter.TclError:
        return


def on_reg():
    v = get_data(DATA)
    write_log({"データ読み込み番号": DATA, "value": v, "判定": "TRUE"})
    done(v)


btn.config(command=on_reg)
tick()
root.mainloop()
