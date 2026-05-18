import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
import modules.android as android_mod
import modules.ios as ios_mod
from modules.android import check_dependencies, run_apk_script
from modules.ios import run_ipa_script
from modules.config import load_profiles, save_profiles

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def default_source(ext):
    candidate = PROJECT_ROOT / "Original Files" / f"tsto_original.{ext}"
    return str(candidate) if candidate.exists() else ""


class _MainThreadMessageBox:
    def __init__(self, root):
        self._root = root

    def _call(self, fn, title, message):
        if threading.current_thread() is threading.main_thread():
            return fn(title, message)
        done = threading.Event()
        box = {}

        def run():
            try:
                box["result"] = fn(title, message)
            finally:
                done.set()

        self._root.after(0, run)
        done.wait()
        return box.get("result")

    def showinfo(self, title, message):
        return self._call(messagebox.showinfo, title, message)

    def showerror(self, title, message):
        return self._call(messagebox.showerror, title, message)

    def showwarning(self, title, message):
        return self._call(messagebox.showwarning, title, message)

    def askyesno(self, title, message):
        return self._call(messagebox.askyesno, title, message)


def run_patch_in_thread(root, run_button, progress_bar, status_var, worker):
    msg_queue = queue.Queue()

    def status_cb(message):
        print(message)
        msg_queue.put(message)

    proxy = _MainThreadMessageBox(root)
    android_mod.messagebox = proxy
    ios_mod.messagebox = proxy

    run_button.config(state="disabled")
    progress_bar.start()

    thread = threading.Thread(target=lambda: worker(status_cb), daemon=True)
    thread.start()

    def poll():
        while True:
            try:
                status_var.set(msg_queue.get_nowait())
            except queue.Empty:
                break
        if thread.is_alive():
            root.after(150, poll)
        else:
            progress_bar.stop()
            run_button.config(state="normal")

    root.after(150, poll)

ICON_PLACEHOLDER = "Optional - PNG/JPG to replace app icon"


def resolve_value(entry):
    value = entry.get().strip()
    placeholder = getattr(entry, "_placeholder", None)
    if not value or (placeholder is not None and value == placeholder):
        return ""
    return value


def resolve_icon(icon_entry):
    return resolve_value(icon_entry) or None


def set_entry(entry, value):
    entry.delete(0, tk.END)
    entry.configure(foreground="white")
    entry.insert(0, value)


def add_profile_selector(parent, root, entries):
    profiles = load_profiles()

    profile_frame = ttk.Frame(root, padding="10")
    profile_frame.pack(fill="x", before=parent)

    ttk.Label(profile_frame, text="Profile:").pack(side="left")

    profile_combo = ttk.Combobox(
        profile_frame, state="readonly", values=list(profiles.keys()), width=24
    )
    profile_combo.pack(side="left", padx=5)

    def apply_profile(_event=None):
        prof = profiles.get(profile_combo.get())
        if not prof:
            return
        for key, entry in entries.items():
            if prof.get(key):
                set_entry(entry, prof[key])

    def save_profile():
        name = simpledialog.askstring(
            "Save Profile",
            "Profile name (existing name overwrites it):",
            initialvalue=profile_combo.get(),
            parent=root,
        )
        if not name:
            return
        name = name.strip()
        if not name:
            return

        prof = {}
        for key, entry in entries.items():
            value = resolve_value(entry)
            if value:
                prof[key] = value

        if not prof:
            messagebox.showwarning(
                "Save Profile", "Nothing to save - fill in some fields first."
            )
            return

        profiles[name] = prof
        save_profiles(profiles)
        profile_combo["values"] = list(profiles.keys())
        profile_combo.set(name)
        messagebox.showinfo(
            "Save Profile",
            f"Profile '{name}' saved to profiles.json:\n\n"
            + "\n".join(f"{k}: {v}" for k, v in prof.items()),
        )

    profile_combo.bind("<<ComboboxSelected>>", apply_profile)
    ttk.Button(profile_frame, text="Save Profile", command=save_profile).pack(
        side="left", padx=5
    )
    return profile_combo


def add_placeholder(entry, placeholder):
    # Create a placeholder behavior
    entry._placeholder = placeholder
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
    style.configure(
        "TCombobox",
        fieldbackground="#4a4a4a",
        background="#4a4a4a",
        foreground="#ffffff",
        arrowcolor="#ffffff",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", "#4a4a4a")],
        foreground=[("readonly", "#ffffff")],
    )
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
    apk_entry.insert(0, default_source("apk"))

    def browse_apk_file():
        initialdir = PROJECT_ROOT / "Original Files"
        if not initialdir.exists():
            initialdir = Path.cwd()
        file_path = filedialog.askopenfilename(
            initialdir=initialdir, filetypes=[("APK files", "*.apk")]
        )
        if file_path:
            apk_entry.delete(0, tk.END)
            apk_entry.insert(0, file_path)

    browse_button = ttk.Button(frame, text="Browse", command=browse_apk_file)
    browse_button.grid(row=0, column=2, padx=5)

    gameserver_label = ttk.Label(frame, text="New Gameserver URL:")
    gameserver_label.grid(row=1, column=0, sticky="w")

    gameserver_entry = ttk.Entry(frame, width=50)
    gameserver_entry.grid(row=1, column=1, columnspan=2, pady=5)
    add_placeholder(gameserver_entry, "http://192.168.1.100:8080")

    dlcserver_label = ttk.Label(frame, text="New DLC Server URL:")
    dlcserver_label.grid(row=2, column=0, sticky="w")

    dlcserver_entry = ttk.Entry(frame, width=50)
    dlcserver_entry.grid(row=2, column=1, columnspan=2, pady=5)
    add_placeholder(dlcserver_entry, "http://192.168.1.101:8080/static/")

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

    icon_label = ttk.Label(frame, text="App Icon:")
    icon_label.grid(row=5, column=0, sticky="w")

    icon_entry = ttk.Entry(frame, width=50)
    icon_entry.grid(row=5, column=1, padx=5)
    add_placeholder(icon_entry, ICON_PLACEHOLDER)

    def browse_icon_file():
        file_path = filedialog.askopenfilename(
            initialdir=Path.cwd(),
            filetypes=[("Image files", "*.png *.jpg *.jpeg")],
        )
        if file_path:
            icon_entry.delete(0, tk.END)
            icon_entry.configure(foreground="white")
            icon_entry.insert(0, file_path)

    icon_browse_button = ttk.Button(frame, text="Browse", command=browse_icon_file)
    icon_browse_button.grid(row=5, column=2, padx=5)

    add_profile_selector(
        frame,
        root,
        {
            "gameserver": gameserver_entry,
            "dlc": dlcserver_entry,
            "appname": appname_entry,
            "version": version_entry,
            "icon": icon_entry,
        },
    )

    progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="indeterminate")
    progress_bar.grid(row=6, column=0, columnspan=3, pady=10, sticky="ew")

    status_var = tk.StringVar(value="Idle")
    status_label = ttk.Label(
        frame, textvariable=status_var, wraplength=440, justify="left"
    )
    status_label.grid(row=7, column=0, columnspan=3, sticky="w")

    def start_apk_patch():
        run_patch_in_thread(
            root,
            run_button,
            progress_bar,
            status_var,
            lambda status_cb: run_apk_script(
                apk_entry.get().strip(),
                gameserver_entry.get().strip(),
                dlcserver_entry.get().strip(),
                appname_entry.get().strip(),
                version_entry.get().strip(),
                progress_bar,
                resolve_icon(icon_entry),
                status_cb,
            ),
        )

    run_button = ttk.Button(frame, text="Patch APK", command=start_apk_patch)
    run_button.grid(row=8, column=0, columnspan=3, pady=5)

    check_button = ttk.Button(
        frame, text="Check Dependencies", command=check_dependencies
    )
    check_button.grid(row=9, column=0, columnspan=3, pady=5)

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

    root.mainloop()


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
    ipa_entry.insert(0, default_source("ipa"))

    def browse_ipa_file():
        initialdir = PROJECT_ROOT / "Original Files"
        if not initialdir.exists():
            initialdir = Path.cwd()
        file_path = filedialog.askopenfilename(
            initialdir=initialdir, filetypes=[("IPA files", "*.ipa")]
        )
        if file_path:
            ipa_entry.delete(0, tk.END)
            ipa_entry.insert(0, file_path)

    browse_button = ttk.Button(frame, text="Browse", command=browse_ipa_file)
    browse_button.grid(row=0, column=2, padx=5)

    gameserver_label = ttk.Label(frame, text="New Gameserver URL:")
    gameserver_label.grid(row=1, column=0, sticky="w")

    gameserver_entry = ttk.Entry(frame, width=50)
    gameserver_entry.grid(row=1, column=1, columnspan=2, pady=5)
    add_placeholder(gameserver_entry, "http://192.168.1.100:8080")

    dlcserver_label = ttk.Label(frame, text="New DLC Server URL:")
    dlcserver_label.grid(row=2, column=0, sticky="w")

    dlcserver_entry = ttk.Entry(frame, width=50)
    dlcserver_entry.grid(row=2, column=1, columnspan=2, pady=5)
    add_placeholder(dlcserver_entry, "http://192.168.1.101:8080/static/")

    bundleid_label = ttk.Label(frame, text="Bundle Identifier:")
    bundleid_label.grid(row=3, column=0, sticky="w")

    bundleid_entry = ttk.Entry(frame, width=50)
    bundleid_entry.grid(row=3, column=1, columnspan=2, pady=5)
    add_placeholder(bundleid_entry, "com.ea.simpsonssocial.inc2")

    appname_label = ttk.Label(frame, text="App Display Name:")
    appname_label.grid(row=4, column=0, sticky="w")

    appname_entry = ttk.Entry(frame, width=50)
    appname_entry.grid(row=4, column=1, columnspan=2, pady=5)
    add_placeholder(appname_entry, "Tapped Out")

    version_label = ttk.Label(frame, text="App Version:")
    version_label.grid(row=5, column=0, sticky="w")

    version_entry = ttk.Entry(frame, width=50)
    version_entry.grid(row=5, column=1, columnspan=2,pady=5)
    add_placeholder(version_entry, "4.69.5")

    icon_label = ttk.Label(frame, text="App Icon:")
    icon_label.grid(row=6, column=0, sticky="w")

    icon_entry = ttk.Entry(frame, width=50)
    icon_entry.grid(row=6, column=1, padx=5)
    add_placeholder(icon_entry, ICON_PLACEHOLDER)

    def browse_icon_file():
        file_path = filedialog.askopenfilename(
            initialdir=Path.cwd(),
            filetypes=[("Image files", "*.png *.jpg *.jpeg")],
        )
        if file_path:
            icon_entry.delete(0, tk.END)
            icon_entry.configure(foreground="white")
            icon_entry.insert(0, file_path)

    icon_browse_button = ttk.Button(frame, text="Browse", command=browse_icon_file)
    icon_browse_button.grid(row=6, column=2, padx=5)

    add_profile_selector(
        frame,
        root,
        {
            "gameserver": gameserver_entry,
            "dlc": dlcserver_entry,
            "bundleid": bundleid_entry,
            "appname": appname_entry,
            "version": version_entry,
            "icon": icon_entry,
        },
    )

    progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="indeterminate")
    progress_bar.grid(row=7, column=0, columnspan=3, pady=10, sticky="ew")

    status_var = tk.StringVar(value="Idle")
    status_label = ttk.Label(
        frame, textvariable=status_var, wraplength=440, justify="left"
    )
    status_label.grid(row=8, column=0, columnspan=3, sticky="w")

    def start_ipa_patch():
        run_patch_in_thread(
            root,
            run_button,
            progress_bar,
            status_var,
            lambda status_cb: run_ipa_script(
                ipa_entry.get().strip(),
                gameserver_entry.get().strip(),
                dlcserver_entry.get().strip(),
                bundleid_entry.get().strip(),
                appname_entry.get().strip(),
                version_entry.get().strip(),
                resolve_icon(icon_entry),
                status_cb,
            ),
        )

    run_button = ttk.Button(frame, text="Patch IPA", command=start_ipa_patch)
    run_button.grid(row=9, column=0, columnspan=3, pady=5)

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

    root.mainloop()
