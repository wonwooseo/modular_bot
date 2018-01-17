from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from tkinter import scrolledtext
import sys

window = Tk()
window.title("TestBot Configuration")
window.minsize(640, 480)
window.maxsize(640, 480)


def sys_exit():
    exit_check = messagebox.askyesno("Exit", "Shutdown TestBot?")
    if exit_check:
        sys.exit(0)
    else:
        pass


# Menu bar settings
menu_bar = Menu(window)
file_menu = Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Exit..", command=sys_exit)
menu_bar.add_cascade(label="File", menu=file_menu)
window.config(menu=menu_bar)
# Notebook (tabs) settings
notebook = ttk.Notebook(window)
# Module list tab
module_list_page = ttk.Frame(notebook)
# List of currently existing modules
module_checklist = Listbox(module_list_page, bg="white", relief=SUNKEN, borderwidth=2,
                           selectmode=SINGLE, highlightthickness=0)
module_checklist.insert(0, "wow")
# Module description & apply button
module_desc = LabelFrame(module_list_page, text="Module Information")
module_name = StringVar()
module_name.set("test name")
module_name_label = Label(module_desc, text="Name: ")
module_name_label.grid(row=0, sticky=W, padx=5)
module_apply = Button(module_list_page, text="Apply", width=15)
# Grid settings
module_checklist.grid(column=0, row=0, sticky=N+S+E+W, padx=5, pady=5, rowspan=2)
module_desc.grid(column=1, row=0, sticky=N+S+E+W, padx=5, pady=5)
module_apply.grid(column=1, row=1, sticky=N+S, padx=5, pady=5)
module_list_page.columnconfigure(0, weight=1)
module_list_page.columnconfigure(1, weight=1)
module_list_page.rowconfigure(0, weight=1)
# Console tab
console_page = ttk.Frame(notebook)
console_text = scrolledtext.ScrolledText(console_page, state="disabled", wrap="none", bg="black", fg="lawn green")
console_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
console_text['state'] = 'normal'
console_text.insert(END, "test log")
console_text['state'] = 'disabled'
console_text.see(END)
notebook.add(module_list_page, text="Modules")
notebook.add(console_page, text="Console")
notebook.pack(side=TOP, fill=BOTH, expand=True)
window.mainloop()
