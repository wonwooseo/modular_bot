import discord
import logging
from configobj import ConfigObj
from pydoc import locate
import _thread
import asyncio
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import colorchooser
import time

client = discord.Client()
config = ConfigObj("config.ini")
modules_list = []
enabled_list = []
command_dict = {}
command_char = ''
listening_channels = []
voice_channel = ""


class LogHandler(logging.Handler):
    """
    Class for custom logging handler. Logging message from default logger is passed to this handler and used to
    update text in ScrollText widget in GUI.
    """
    def __init__(self, log_space):
        logging.Handler.__init__(self)
        fmt = logging.Formatter("[%(asctime)s][%(levelname)s]: %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
        self.setFormatter(fmt)
        self.text = log_space

    def emit(self, record):
        log = self.format(record)
        self.text["state"] = "normal"
        self.text.insert(END, log + "\n")
        self.text["state"] = "disabled"
        self.text.see(END)


@client.event
async def on_ready():
    logging.info("Logged in as " + client.user.name + "(ID: " + client.user.id + ")")
    for channel in listening_channels:
        await client.send_message(client.get_channel(channel), ":thumbsup:")


@client.event
async def on_message(message):
    if message.content.startswith(command_char) and check_message_channel(message):
        command_term = message.content.split(" ")[0]
        executing_module = command_dict.get(command_term[1:])
        if executing_module is None:
            # Invalid command
            logging.info("Invalid command requested by " + message.author.name + " on " + message.channel.name)
            return_text = command_term[1:]
            if len(return_text) == 0:
                return_text = "null"
            await client.send_message(message.channel, "Invalid Command: " + "`" + return_text + "`")
        else:
            # Create a bundle to pass to module as argument
            bundle = {"client": client, "message": message, "vchannel": voice_channel}
            # Pass bundle to corresponding module
            await executing_module.parse_command(bundle)


def check_message_channel(msg):
    """
    Checks if bot should respond to given message by comparing channel id.
    :param msg: Message object
    :return: True if message is from listening channel, False if not.
    """
    if msg.channel.id in listening_channels:
        return True
    else:
        return False


def load_commands():
    """
    Reads all available commands from modules and update command dictionary.
    :return: No return value.
    """
    for i in range(0, len(modules_list)):
        if not enabled_list[i]:
            continue
        command_list = modules_list[i].get_all_commands()
        for command_item in command_list:
            if command_dict.get(command_item) is not None:
                logging.warning("Conflict in command " + command_item + " of module " + modules_list[i].get_module_name
                                + ". Command from existing module will be used.")
            else:
                command_dict[command_item] = modules_list[i]


def gui_setup():
    """
    Sets up GUI layout and starts TkInter GUI event loop. This function must be started in separate thread from the
    main thread.
    :return: no return value.
    """
    def sys_exit():
        """
        Logs out client and exit if user chooses to exit.
        :return: no return value.
        """
        exit_check = messagebox.askyesno("Exit?", "Do you want to shutdown the bot?")
        if exit_check:
            try:  # call client.logout in new event loop
                loop = asyncio.new_event_loop()
                loop.run_until_complete(client.logout())
            except RuntimeError:  # Suppress exception; exiting program anyway
                pass
        else:
            pass

    def open_setting():
        """
        Settings menu for GUI. Opens another window on top of main window and show settings. Grabs focus until it is
        closed by user.
        :return: no return value.
        """
        setting_window = Toplevel()
        setting_window.title("GUI Settings")
        setting_window.minsize(480, 270)
        setting_window.maxsize(480, 270)
        # Main window not focusable while in settings
        setting_window.grab_set()
        setting_notebook = ttk.Notebook(setting_window)
        # Console theme page
        console_theme_page = ttk.Frame(setting_notebook)
        console_bg_label = Label(console_theme_page, text="Background Color: ")
        console_bg_label.grid(row=0, sticky=E)
        console_bg_picker = Button(console_theme_page, bg=console_text["bg"],
                                   width=10, height=1, bd=4, command=lambda: color_picker("bg", console_bg_picker))
        console_bg_picker.grid(row=0, column=1, sticky=W)
        console_fg_label = Label(console_theme_page, text="Font Color: ")
        console_fg_label.grid(row=1, sticky=E)
        console_fg_picker = Button(console_theme_page, bg=console_text["fg"],
                                   width=10, height=1, bd=4, command=lambda: color_picker("fg", console_fg_picker))
        console_fg_picker.grid(row=1, column=1, sticky=W)
        console_theme_page.rowconfigure(0, weight=1)
        console_theme_page.rowconfigure(1, weight=1)
        console_theme_page.columnconfigure(0, weight=1)
        console_theme_page.columnconfigure(1, weight=1)
        setting_notebook.add(console_theme_page, text="Console Theme")
        setting_notebook.pack(side=TOP, fill=BOTH, expand=True)

    def color_picker(target, button):
        """
        Shows color picker and updates background / font color of console according to color picked by user.
        :param target: "bg" for console background, "fg" for console text.
        :param button: Color picker button widget on settings window.
        :return: No return value.
        """
        if target == "bg":
            new_color = colorchooser.askcolor(console_text["bg"], parent=button, title="Pick Background Color")
            if new_color[1] is None:
                return
            console_text.configure(bg=new_color[1])
        else:
            new_color = colorchooser.askcolor(console_text["fg"], parent=button, title="Pick Font Color")
            if new_color[1] is None:
                return
            console_text.configure(fg=new_color[1])
        button.configure(bg=new_color[1])

    def checkbox_toggle(index):
        """
        Callback from toggle event of checkbox. Enables or disables module in config object. Object is not written
        to actual config file before user hits Apply button.
        :param index: Index of module in modules_list
        :return: no return value.
        """
        enabled_list[index] = not enabled_list[index]
        config_modules = config["MODULES"]
        modules_path_list = config_modules["modules_list"].split("\n")
        path = modules_path_list[index].split(";")[0]
        if enabled_list[index]:
            modules_path_list[index] = path + ";T"
        else:
            modules_path_list[index] = path + ";F"
        config_modules["modules_list"] = "\n".join(modules_path_list)

    def module_onselect(event):
        """
        OnSelect event handler. Updates values of text labels every time user selects a module list item.
        :param event: Select event.
        :return: no return value.
        """
        w = event.widget
        # Clear labels from previous select
        for label in module_desc.winfo_children():
            label.destroy()
        selected_idx = int(w.curselection()[0])
        selected_module = modules_list[selected_idx]
        # Set name of module
        module_name = StringVar()
        module_name.set("Name: " + selected_module.get_module_name())
        module_name_label = Label(module_desc, textvariable=module_name, wraplength=400,
                                  justify=LEFT, anchor=W)
        module_name_label.grid(row=0, sticky=W, padx=5)
        # Set description of module
        module_description_str = StringVar()
        module_description_str.set("Description: \n" + selected_module.get_module_description())
        module_description_label = Label(module_desc, textvariable=module_description_str, wraplength=470,
                                         justify=LEFT, anchor=W)
        module_description_label.grid(row=1, sticky=W, padx=5)
        # Set commands of module
        module_command = StringVar()
        module_command.set("Commands: \n" + ", ".join(selected_module.get_all_commands()))
        module_command_label = Label(module_desc, textvariable=module_command, wraplength=470,
                                     justify=LEFT, anchor=W)
        module_command_label.grid(row=2, sticky=W, padx=5)
        # Set on/off checkbox
        module_switch = Checkbutton(module_desc, text="Enabled", command=lambda: checkbox_toggle(selected_idx))
        if enabled_list[selected_idx]:
            module_switch.select()
        else:
            module_switch.deselect()
        module_switch.grid(row=3, sticky=W, padx=5, pady=10)

    def write_config():
        """
        Writes config object to config file and notify user. Changes will be reflected after restarting.
        :return: no return value.
        """
        config.write()
        messagebox.showinfo("Changes Applied", "Changes you made will be applied after restarting the bot.")

    window = Tk()
    window.title("TestBot Configuration")
    window.minsize(800, 450)
    window.maxsize(800, 450)
    # Menu bar settings
    menu_bar = Menu(window)
    file_menu = Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Settings..", command=open_setting)
    file_menu.add_separator()
    file_menu.add_command(label="Exit..", command=sys_exit)
    menu_bar.add_cascade(label="File", menu=file_menu)
    window.config(menu=menu_bar)
    # Notebook (tabs) settings
    notebook = ttk.Notebook(window)
    # Module list tab
    module_list_page = ttk.Frame(notebook)
    # List of currently existing modules
    module_checklist = Listbox(module_list_page, bg="white", relief=SUNKEN, borderwidth=2, activestyle="none",
                               selectmode=SINGLE, highlightthickness=0, width=40)
    for i in range(0, len(modules_list)):
        module_checklist.insert(i, " " + modules_list[i].get_module_name())
    module_checklist.bind('<<ListboxSelect>>', module_onselect)
    # Module description & apply button
    module_desc = LabelFrame(module_list_page, text="Module Information")
    module_apply = Button(module_list_page, text="Apply Changes..", width=20, command=write_config)
    # Grid settings
    module_checklist.grid(column=0, row=0, sticky=N + S + E + W, padx=5, pady=5, rowspan=2)
    module_desc.grid(column=1, row=0, sticky=N + S + E + W, padx=5, pady=5)
    module_apply.grid(column=1, row=1, sticky=N + S, padx=5, pady=5)
    module_list_page.columnconfigure(1, weight=1)
    module_list_page.rowconfigure(0, weight=1)
    # Console tab
    console_page = ttk.Frame(notebook)
    console_text = scrolledtext.ScrolledText(console_page, state="disabled", wrap="none", bg="black", fg="lawn green")
    console_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
    gui_log_handler = LogHandler(console_text)
    logging.getLogger().addHandler(gui_log_handler)
    notebook.add(console_page, text="Console")
    notebook.add(module_list_page, text="Modules")
    notebook.pack(side=TOP, fill=BOTH, expand=True)
    logging.info("GUI loading complete")
    window.mainloop()


def main():
    # Logging configuration
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s][%(levelname)s]: %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
    global command_char, listening_channels, voice_channel
    # Parse config file and load settings
    logging.debug("Loading settings from config.ini")
    config_general = config["GENERAL"]
    # Set command prefix
    command_char = config_general.get("command_prefix")
    # Set auth token
    token = config_general.get("token")
    # Set listening channels
    listening_channels = config_general.get("listening_channels")
    # Set voice channel
    voice_channel = config_general.get("voice_channel")
    # Read module lists and create list of module class instances
    config_modules = config["MODULES"]
    modules_path_list = config_modules.get("modules_list").split("\n")
    for entry in modules_path_list:
        path = entry.split(";")[0]
        enabled = False
        if entry.split(";")[1] == "T":
            enabled = True
        class_attribute = locate(path)
        modules_list.append(class_attribute(command_char))
        enabled_list.append(enabled)
    # Update commands dictionary
    load_commands()
    # Check GUI option and start GUI thread
    gui_switch = config["GUI"]["use_gui"]
    if gui_switch == "1":
        _thread.start_new_thread(gui_setup, ())
        time.sleep(1)  # give some time for GUI to load
    logging.info("========== BOT BOOTING COMPLETE ==========")
    logging.info("Command prefix: " + command_char)
    logging.info("Listening to: " + str(listening_channels))
    logging.info("Voice channel: " + voice_channel)
    logging.info("Number of modules in library: " + str(len(modules_path_list)))
    logging.info("Number of modules enabled: " + str(enabled_list.count(True)))
    logging.info("==========================================")
    # Connect to server
    logging.info("Connecting to Discord server...")
    client.run(token)
