import tkinter
root = tkinter.Tk()
lbl = tkinter.Label(root, text='easy2')
s=0
for i in cui_row:
	s=s+int(i)
lb2 = tkinter.Label(root, text=s)
lb2.pack
root.mainloop()
return 1