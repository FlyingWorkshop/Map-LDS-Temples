import TempleGuide as tg
import tkinter as tk

DROPDOWN_WIDTH = 10
ENTRY_WIDTH = 40


def main():
    db = tg.Database()
    search_box(db)

def search_box(db):
    root = tk.Tk()
    root.title('Temple Guide (a.1)')

    label = tk.Label(root, text='Search: ')
    label.grid(row=0, column=0)

    attrs = list(tg.Temple().__dict__)
    s = tk.StringVar(root)
    s.set(attrs[0])  # default value
    menu = tk.OptionMenu(root, s, *attrs)
    menu.config(width=DROPDOWN_WIDTH)
    menu.grid(row=0, column=1)

    entry = tk.Entry(root, width=ENTRY_WIDTH)
    entry.config(width=ENTRY_WIDTH)
    entry.grid(row=0, column=2)

    lb = tk.Listbox(root, width=ENTRY_WIDTH)
    for name in db.data['name']:
        lb.insert('end', name)
    lb.grid(row=1, column=2)

    root.mainloop()


if __name__ == '__main__':
    main()
