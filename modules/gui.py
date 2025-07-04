import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from modules.android import check_dependencies, run_apk_script
from modules.ios import run_ipa_script

def add_placeholder(entry, placeholder):
    # Create a placeholder behavior
    entry.insert(0, placeholder)
    entry.configure(foreground="#A9A9A9")

    def on_focus_in(event):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.configure(foreground="white")

    def on_focus_out(event):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.configure(foreground="#A9A9A9")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)



def configure_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background="#2e2e2e", foreground="#ffffff")
    style.configure("TButton", background="#4a4a4a", foreground="#ffffff")
    style.configure("TEntry", fieldbackground="#4a4a4a", foreground="#ffffff")
    style.configure("TFrame", background="#2e2e2e")
    return style


def start_selection():
    selection_root = tk.Tk()
    selection_root.title("TSTO Patcher")
    selection_root.geometry("400x250")
    selection_root.configure(bg="#2e2e2e")

    configure_style()

    # Main (selection_root)
    label = ttk.Label(selection_root, text="Choose patcher:", font=("Arial", 14))
    label.pack(pady=10)

    apk_button = ttk.Button(
        selection_root,
        text="Patch APK",
        command=lambda: [selection_root.destroy(), start_apk_patcher()],
    )
    apk_button.pack(pady=5)

    ipa_button = ttk.Button(
        selection_root,
        text="Patch IPA",
        command=lambda: [selection_root.destroy(), start_ipa_patcher()],
    )
    ipa_button.pack(pady=5)

    ipa_button = ttk.Button(
        selection_root,
        text="Credits",
        command=lambda: [selection_root.destroy(), show_credits()],
    )
    ipa_button.pack(pady=5)

    # Footer
    footer_frame = tk.Frame(selection_root, bg="#2e2e2e")
    footer_frame.pack(side="bottom", fill="x")

    close_button = ttk.Button(footer_frame, text="Close", command=lambda: [quit()])
    close_button.pack(side="left", padx=10, pady=5)

    footer_label = tk.Label(
        footer_frame, text="Bodnjenie™ & Dractiums", bg="#2e2e2e", fg="#ffffff", anchor="e"
    )
    footer_label.pack(side="right", padx=10, pady=5)

    selection_root.mainloop()


######################CREDITS
def show_credits():
    root = tk.Tk()
    root.title("Credits")
    root.geometry("500x400")
    root.configure(bg="#2e2e2e")

    configure_style()

    # Credits section
    credits_frame = tk.Frame(root, bg="#2e2e2e")
    credits_frame.pack(fill="x", padx=10, pady=10)

    credits_title = tk.Label(
        credits_frame,
        text="Credits",
        bg="#2e2e2e",
        fg="#ffffff",
        font=("Arial", 15),
        justify="center",
    )
    credits_title.pack(anchor="n", pady=5)

    credits_label = tk.Label(
        credits_frame,
        text="@BodNJenie\n@tjac\n@AlekPM\n@Dractiums",
        bg="#2e2e2e",
        fg="#ffffff",
        font=("Arial", 12),
        justify="center",
    )
    credits_label.pack(anchor="n", pady=5)

    # Testers section
    testers_frame = tk.Frame(root, bg="#2e2e2e")
    testers_frame.pack(fill="x", padx=10, pady=10)

    testers_title = tk.Label(
        testers_frame,
        text="Testers",
        bg="#2e2e2e",
        fg="#ffffff",
        font=("Arial", 15),
        justify="center",
    )
    testers_title.pack(anchor="n", pady=5)  # Reduced padding for better alignment

    testers_label = tk.Label(
        testers_frame,
        text="@rudeboy\n@jjay121212\n@Popo\n@avariss\n@jani",
        bg="#2e2e2e",
        fg="#ffffff",
        font=("Arial", 12),
        justify="center",
    )
    testers_label.pack(anchor="n", pady=5)  # Reduced padding to minimize gap

    # Footer section
    footer_frame = tk.Frame(root, bg="#2e2e2e")
    footer_frame.pack(side="bottom", fill="x")

    back_button = ttk.Button(
        footer_frame, text="Back", command=lambda: [root.destroy(), start_selection()]
    )
    back_button.pack(side="left", padx=10, pady=5)

    root.mainloop()


#############################APK PATCHER
def start_apk_patcher():

    print("Starting APK patcher")
    root = tk.Tk()
    root.title("TSTO Patcher")

    configure_style()

    frame = ttk.Frame(root, padding="10")
    frame.pack(fill="both", expand=True)

    # Main (frame)
    apk_label = ttk.Label(frame, text="APK File:")
    apk_label.grid(row=0, column=0, sticky="w")

    apk_entry = ttk.Entry(frame, width=50)
    apk_entry.grid(row=0, column=1, padx=5)

    def browse_apk_file():
        initialdir = Path.cwd()
        if Path("Original Files").exists() is True:
            initialdir = Path("Original Files")
        file_path = filedialog.askopenfilename(
            initialdir=initialdir, filetypes=[("APK files", "*.apk")]
        )
        apk_entry.delete(0, tk.END)
        apk_entry.insert(0, file_path)

    browse_button = ttk.Button(frame, text="Browse", command=browse_apk_file)
    browse_button.grid(row=0, column=2, padx=5)

    gameserver_label = ttk.Label(frame, text="New Gameserver URL:")
    gameserver_label.grid(row=1, column=0, sticky="w")

    gameserver_entry = ttk.Entry(frame, width=50)
    gameserver_entry.grid(row=1, column=1, columnspan=2, pady=5)
    add_placeholder(gameserver_entry, "http://192.168.1.100:80")

    dlcserver_label = ttk.Label(frame, text="New DLC Server URL:")
    dlcserver_label.grid(row=2, column=0, sticky="w")

    dlcserver_entry = ttk.Entry(frame, width=50)
    dlcserver_entry.grid(row=2, column=1, columnspan=2, pady=5)
    add_placeholder(dlcserver_entry, "http://192.168.1.101:80")

    appname_label = ttk.Label(frame, text="App Display Name:")
    appname_label.grid(row=3, column=0, sticky="w")

    appname_entry = ttk.Entry(frame, width=50)
    appname_entry.grid(row=3, column=1, columnspan=2, pady=5)
    add_placeholder(appname_entry, "Tapped Out")

    version_label = ttk.Label(frame, text="App Version:")
    version_label.grid(row=4, column=0, sticky="w")

    version_entry = ttk.Entry(frame, width=50)
    version_entry.grid(row=4, column=1, columnspan=2,pady=5)
    add_placeholder(version_entry, "4.69.5")

    progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    progress_bar.grid(row=5, column=0, columnspan=3, pady=10, sticky="ew")

    run_button = ttk.Button(
        frame,
        text="Patch APK",
        command=lambda: run_apk_script(
            apk_entry.get().strip(), gameserver_entry.get().strip(), dlcserver_entry.get().strip(), appname_entry.get().strip(), version_entry.get().strip(), progress_bar
        ),
    )  # Changed to lambda to pass in variables
    run_button.grid(row=6, column=0, columnspan=3, pady=5)

    check_button = ttk.Button(
        frame, text="Check Dependencies", command=check_dependencies
    )
    check_button.grid(row=7, column=0, columnspan=3, pady=5)

    # Footer
    footer_frame = tk.Frame(root, bg="#2e2e2e")
    footer_frame.pack(side="bottom", fill="x")

    back_button = ttk.Button(
        footer_frame, text="Back", command=lambda: [root.destroy(), start_selection()]
    )
    back_button.pack(side="left", padx=10, pady=5)

    footer_label = tk.Label(
        footer_frame, text="Bodnjenie™ & Dractiums", bg="#2e2e2e", fg="#ffffff", anchor="e"
    )
    footer_label.pack(side="right", padx=10, pady=5)


#############################IPA PATCHER
def start_ipa_patcher():

    print("Starting IPA patcher")

    root = tk.Tk()
    root.title("TSTO Patcher")

    configure_style()

    frame = ttk.Frame(root, padding="10")
    frame.pack(fill="both", expand=True)

    # Main (frame)
    ipa_label = ttk.Label(frame, text="IPA File:")
    ipa_label.grid(row=0, column=0, sticky="w")

    ipa_entry = ttk.Entry(frame, width=50)
    ipa_entry.grid(row=0, column=1, padx=5)

    def browse_ipa_file():
        initialdir = Path.cwd()
        if Path("Original Files").exists() is True:
            initialdir = Path("Original Files")
        file_path = filedialog.askopenfilename(
            initialdir=initialdir, filetypes=[("IPA files", "*.ipa")]
        )
        ipa_entry.delete(0, tk.END)
        ipa_entry.insert(0, file_path)

    browse_button = ttk.Button(frame, text="Browse", command=browse_ipa_file)
    browse_button.grid(row=0, column=2, padx=5)

    gameserver_label = ttk.Label(frame, text="New Gameserver URL:")
    gameserver_label.grid(row=1, column=0, sticky="w")

    gameserver_entry = ttk.Entry(frame, width=50)
    gameserver_entry.grid(row=1, column=1, columnspan=2, pady=5)
    add_placeholder(gameserver_entry, "http://192.168.1.100:80")

    dlcserver_label = ttk.Label(frame, text="New DLC Server URL:")
    dlcserver_label.grid(row=2, column=0, sticky="w")

    dlcserver_entry = ttk.Entry(frame, width=50)
    dlcserver_entry.grid(row=2, column=1, columnspan=2, pady=5)
    add_placeholder(dlcserver_entry, "http://192.168.1.101:80")

    progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    progress_bar.grid(row=3, column=0, columnspan=3, pady=10, sticky="ew")

    run_button = ttk.Button(
        frame,
        text="Patch IPA",
        command=lambda: run_ipa_script(
            ipa_entry.get(), gameserver_entry.get(), dlcserver_entry.get()
        ),
    )
    run_button.grid(row=4, column=0, columnspan=3, pady=5)

    check_button = ttk.Button(
        frame, text="Check Dependencies", command=check_dependencies
    )
    check_button.grid(row=5, column=0, columnspan=3, pady=5)

    # Footer
    footer_frame = tk.Frame(root, bg="#2e2e2e")
    footer_frame.pack(side="bottom", fill="x")

    back_button = ttk.Button(
        footer_frame, text="Back", command=lambda: [root.destroy(), start_selection()]
    )
    back_button.pack(side="left", padx=10, pady=5)

    footer_label = tk.Label(
        footer_frame, text="Bodnjenie™ & Dractiums", bg="#2e2e2e", fg="#ffffff", anchor="e"
    )
    footer_label.pack(side="right", padx=10, pady=5)
