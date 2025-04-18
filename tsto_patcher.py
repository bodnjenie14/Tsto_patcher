import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import sys
import shutil
import zipfile
import plistlib

# pip install request
import requests

# is_windows = platform.system().lower() == "windows"


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
        footer_frame, text="Bodnjenie™", bg="#2e2e2e", fg="#ffffff", anchor="e"
    )
    footer_label.pack(side="right", padx=10, pady=5)

    selection_root.mainloop()


#############################APK PATCHER
def start_apk_patcher():
    global apk_entry, gameserver_entry, dlcserver_entry, progress_bar

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

    progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    progress_bar.grid(row=3, column=0, columnspan=3, pady=10, sticky="ew")

    run_button = ttk.Button(
        frame,
        text="Patch APK",
        command=lambda: run_apk_script(
            apk_entry.get(), gameserver_entry.get(), dlcserver_entry.get()
        ),
    )  # Changed to lambda to pass in variables
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
        footer_frame, text="Bodnjenie™", bg="#2e2e2e", fg="#ffffff", anchor="e"
    )
    footer_label.pack(side="right", padx=10, pady=5)


def download_file(url, dest):
    """Download a file from the specified URL to the destination path."""
    try:
        req = requests.get(url)
        if req.status_code != 200:
            messagebox.showerror(
                "Download Error",
                f"Failed to download {url}. Status code = {req.status_code}",
            )
            sys.exit(1)
        with open(dest, "wb") as f:
            f.write(req.content)

    except Exception as e:
        messagebox.showerror("Download Error", f"Failed to download {url}: {e}")
        sys.exit(1)


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []

    if not shutil.which("java"):
        missing.append("Java (OpenJDK)")
    if not shutil.which("python3") and not shutil.which("python"):
        missing.append("Python3")

    if missing:
        # Inform the user about missing dependencies
        response = messagebox.askyesno(
            "Missing Dependencies",
            "The following dependencies are missing:\n"
            + "\n".join(missing)
            + "\n\nWould you like to attempt to install them now?",
        )
        if response:  # If the user clicks "Yes"
            try:
                install_dependencies()
                messagebox.showinfo(
                    "Dependencies Installed",
                    "Dependencies have been installed successfully.",
                )
            except Exception as e:
                messagebox.showerror(
                    "Installation Error", f"Failed to install dependencies: {e}"
                )
        else:
            messagebox.showwarning(
                "Dependencies Required",
                "Please install the missing dependencies to proceed.",
            )
    else:
        messagebox.showinfo("Dependencies", "All dependencies are installed.")


def install_dependencies():
    """Install all necessary dependencies for the APK patching process."""
    # Check for Python (should already be running with Python)
    if not shutil.which("python3") and not shutil.which("python"):
        messagebox.showerror(
            "Dependency Error",
            "Python is not installed. Please install it and re-run the application.",
        )
        sys.exit(1)

    # Install OpenJDK
    if not shutil.which("java"):
        if sys.platform == "win32":
            messagebox.showinfo(
                "Dependency Info",
                "Please install OpenJDK 11+ manually and ensure it's in your PATH.",
            )
            sys.exit(1)
        else:
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", "openjdk-11-jre"], check=True
            )

    # Download apktool
    apktool_jar = "apktool_2.10.0.jar"
    apktool_script = "apktool"
    if not os.path.isfile(apktool_jar):
        download_file(
            "https://github.com/iBotPeaches/Apktool/releases/download/v2.10.0/apktool_2.10.0.jar",
            apktool_jar,
        )
    if not shutil.which(apktool_script):
        wrapper_url = (
            "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool"
            if sys.platform != "win32"
            else "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/windows/apktool.bat"
        )
        wrapper_dest = apktool_script if sys.platform != "win32" else "apktool.bat"
        download_file(wrapper_url, wrapper_dest)
        os.chmod(wrapper_dest, 0o755)

    # Download Android SDK tools
    sdk_tools_url = (
        "https://dl.google.com/android/repository/commandlinetools-win-9477386_latest.zip"
        if sys.platform == "win32"
        else "https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip"
    )
    sdk_tools_zip = "cmdline-tools.zip"
    sdk_tools_dir = "android-sdk"
    if not os.path.isdir(sdk_tools_dir):
        download_file(sdk_tools_url, sdk_tools_zip)
        shutil.unpack_archive(sdk_tools_zip, sdk_tools_dir)
        os.remove(sdk_tools_zip)

    # Install platform tools
    platform_tools_url = (
        "https://dl.google.com/android/repository/platform-tools_r34.0.4-windows.zip"
        if sys.platform == "win32"
        else "https://dl.google.com/android/repository/platform-tools_r34.0.4-linux.zip"
    )
    platform_tools_zip = "platform-tools.zip"
    platform_tools_dir = "platform-tools"
    if not os.path.isdir(platform_tools_dir):
        download_file(platform_tools_url, platform_tools_zip)
        shutil.unpack_archive(platform_tools_zip, platform_tools_dir)
        os.remove(platform_tools_zip)

    # Create and activate a Python virtual environment
    pip_path = "venv\\Scripts\\pip" if sys.platform == "win32" else "venv/bin/pip"
    if not os.path.isdir("venv"):
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

    # Install Python dependencies
    # subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)  # might need admin role; skip by default

    subprocess.run([pip_path, "install", "buildapp"], check=True)
    buildapp_fetch_tools = (
        "venv\\Scripts\\buildapp_fetch_tools"
        if sys.platform == "win32"
        else "venv/bin/buildapp_fetch_tools"
    )
    subprocess.run([buildapp_fetch_tools], check=True)


def decompile_app(input_filename):
    """Decompile the APK file."""
    subprocess.run(
        ["java", "-jar", "apktool_2.10.0.jar", "d", input_filename, "-o", "tappedout"],
        check=True,
    )


def replace_and_log_urls(
    new_gameserver_url, new_dlcserver_url, new_url, buffer_size, string_size
):
    """
    Replace server URLs in the decompiled APK and log only the replacements.

    This primarily modifies text-based files (.smali, .xml, .txt).
    It does NOT handle binary .so patching.
    """
    replacements = {
        "https://prod.simpsons-ea.com": new_gameserver_url,
        "https://syn-dir.sn.eamobile.com": new_gameserver_url,  # Director uses same as gameserver
    }

    log = []  # Store logs of replacements

    for root, _, files in os.walk("./tappedout/"):
        for file in files:
            file_path = os.path.join(root, file)

            # Only process text-like files
            if file_path.endswith((".xml", ".smali", ".txt")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception as e:
                    print(f"Failed to read file: {file_path}, Error: {e}")
                    continue

                modified = False
                for original, replacement in replacements.items():
                    if original in content:
                        log.append(
                            f"Replaced '{original}' with '{replacement}' in {file_path}"
                        )
                        content = content.replace(original, replacement)
                        modified = True

                if modified:
                    try:
                        with open(
                            file_path, "w", encoding="utf-8", errors="ignore"
                        ) as f:
                            f.write(content)
                    except Exception as e:
                        print(f"Failed to write to file: {file_path}, Error: {e}")

    # Print the log to console (and you could optionally save it somewhere)
    print("\n".join(log))


def patch_url(file_bytes: bytearray, new_url: str) -> bytearray:
    """
    Replace the known DLC URL string in the .so file with 'new_url',
    **forcing** it to end with '/static/' and keeping the exact same byte-length
    as the original string.

    - If the new URL is shorter, fill leftover space with './' pairs (and a '/' if there's one leftover byte).
    - If it's longer, either truncate it or raise an error (see the code comment).
    """

    # The original DLC URL in the .so
    original_bytes = b"http://oct2018-4-35-0-uam5h44a.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/"
    offset = file_bytes.find(original_bytes)
    if offset < 0:
        print("[!] Could not find the DLC URL in this file. Skipping patch.")
        return None

    # The original URL length (often 88 bytes)
    original_len = len(original_bytes)

    # 1) Force the new URL to end with '/static/'
    #    - Strip any trailing slash, then add '/static/'
    #    - e.g. "http://example.com" => "http://example.com/static/"
    #    - e.g. "http://example.com/" => "http://example.com/static/"
    new_url = new_url

    print("NEW URL: " + new_url)
    # 2) Convert to bytes
    new_url_bytes = bytearray(new_url, "utf-8")
    new_len = len(new_url_bytes)

    # 3) If new URL is longer than original, truncate or raise an error
    if new_len > original_len:
        # Option A: Truncate
        new_url_bytes = new_url_bytes[:original_len]

        # Option B: Raise an error instead (comment out the truncate above if you prefer):
        # raise ValueError(
        #     f"New URL is {new_len - original_len} bytes too long "
        #     f"(max {original_len}). Try a shorter URL."
        # )

    # 4) If new URL is shorter, fill leftover space with './'
    leftover = original_len - len(new_url_bytes)
    if leftover > 0:
        # Add as many './' pairs as will fit
        pairs_to_add = leftover // 2
        new_url_bytes.extend(b'./' * pairs_to_add)

        # If there's one leftover byte, add a single slash
        if leftover % 2 == 1:
            new_url_bytes.append(ord('/'))

    # 5) Overwrite the original string in the file
    for i in range(original_len):
        file_bytes[offset + i] = new_url_bytes[i]

    # (Optional) Null-terminate if you want. Usually not needed if the original ended with '/'
    # file_bytes[offset + original_len - 1] = 0

    # Just for logging:
    final_url = new_url_bytes.decode("utf-8", errors="ignore")
    print(f"[+] Patched DLC URL to: {final_url}")
    return file_bytes


def perform_binary_patching(decompiled_path, new_dlcserver_url):
    """
    Perform direct binary patching on the .so files by overwriting the DLC URL.
    This approach does NOT rely on radare2. It locates the known original
    DLC string and replaces it with the user-provided new_dlcserver_url.
    """

    # List out all the known scorpio .so variants
    so_files = [
        "lib/armeabi-v7a/libscorpio.so",
        "lib/armeabi-v7a/libscorpio-neon.so",
        "lib/arm64-v8a/libscorpio.so",
        "lib/arm64-v8a/libscorpio-neon.so",
    ]

    for rel_path in so_files:
        file_path = os.path.join(decompiled_path, rel_path)
        if not os.path.isfile(file_path):
            print(f"[INFO] File not found: {file_path}. Skipping.")
            continue

        print(f"[INFO] Found {rel_path}, attempting patch ...")

        try:
            with open(file_path, "rb") as src:
                data = bytearray(src.read())

            patched_data = patch_url(data, new_dlcserver_url)
            if patched_data:
                with open(file_path, "wb") as dst:
                    dst.write(patched_data)
                    print(f"[SUCCESS] Patched {rel_path}.")

                    # Patch to bypass IndexFileSig. Thanks to SpAnser!
                    if "lib/armeabi-v7a/libscorpio-neon.so" in rel_path:
                        print(
                            "Bypass IndexFileSig in lib/armeabi-v7a/libscorpio-neon.so"
                        )
                        dst.seek(4666332)  # 0x4733dc offset
                        dst.write(b"\xca\xfd\xff\xea")  # bypass sig check

                    elif "lib/armeabi-v7a/libscorpio.so" in rel_path:
                        print("Bypass IndexFileSig in lib/armeabi-v7a/libscorpio.so")
                        dst.seek(4663220)  # 0x4727b4 offset
                        dst.write(b"\xd2\xfd\xff\xea")  # bypass sig check

                    elif "lib/arm64-v8a/libscorpio-neon.so" in rel_path:
                        print("Bypass IndexFileSig in lib/arm64-v8a/libscorpio-neon.so")
                        dst.seek(7519612)  # 0x72bd7c offset
                        dst.write(b"\x9f\x00\x00\x14")  # bypass sig check

                    elif "lib/arm64-v8a/libscorpio.so" in rel_path:
                        print("Bypass IndexFileSig in lib/arm64-v8a/libscorpio.so")
                        dst.seek(7519464)  # 0x72bce8 offset
                        dst.write(b"\x9f\x00\x00\x14")  # bypass sig check

            else:
                print(
                    f"[WARNING] Could not patch {rel_path}. The original DLC string was not found."
                )

        except Exception as e:
            print(f"[ERROR] Could not patch {file_path}: {e}")


def recompile_app(input_filename):
    """Recompile the patched APK."""
    buildapp_path = (
        "venv\\Scripts\\buildapp" if sys.platform == "win32" else "venv/bin/buildapp"
    )
    output_filename = (
        f"{os.path.splitext(os.path.basename(input_filename))[0]}-patched.apk"
    )
    subprocess.run(
        [buildapp_path, "-d", "tappedout", "-o", output_filename], check=True
    )
    return output_filename


def process_apk(input_filename, new_gameserver_url, new_dlcserver_url):
    try:
        progress_bar.start()

        os.environ["SOURCE_OUTPUT"] = "./tappedout"
        os.environ["APK_FILE"] = input_filename
        os.environ["DLC_URL"] = new_dlcserver_url
        os.environ["GAMESERVER_URL"] = new_gameserver_url
        os.environ["DIRECTOR_URL"] = new_gameserver_url

        # 1) Install dependencies
        install_dependencies()

        # 2) Decompile the APK
        decompile_app(input_filename)

        # 3) Replace text-based references (gameserver, director, etc.):
        new_url = new_dlcserver_url
        buffer_size = hex(len(new_url) + 1)
        string_size = hex(len(new_url))
        replace_and_log_urls(
            new_gameserver_url, new_dlcserver_url, new_url, buffer_size, string_size
        )

        # 4) Perform direct binary patching on .so files for the DLC URL
        perform_binary_patching("./tappedout", new_dlcserver_url)

        # 5) Recompile the patched APK
        output_filename = recompile_app(input_filename)

        messagebox.showinfo("Success", f"Patched APK created: {output_filename}")
    except FileNotFoundError as e:
        messagebox.showerror("Dependency Error", str(e))
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        progress_bar.stop()


def browse_apk_file():
    initialdir = Path.cwd()
    if Path("Original Files").exists() is True:
        initialdir = Path("Original Files")
    file_path = filedialog.askopenfilename(initialdir=initialdir, filetypes=[("APK files", "*.apk")])
    apk_entry.delete(0, tk.END)
    apk_entry.insert(0, file_path)


def run_apk_script(apk_file, gameserver_url, dlc_url):
    # Add a / to the end of the DLC URL
    if not dlc_url.endswith("/"):
        dlc_url += "/"

    # Check all inputs
    if not apk_file or not gameserver_url or not dlc_url:
        messagebox.showerror("Error", "All fields are required!")
        return

    # Run the process
    try:
        process_apk(apk_file, gameserver_url, dlc_url)
    except Exception as e:
        messagebox.showerror("Error", "An unexpected error has occured: " + str(e))


#############################IPA PATCHER
def start_ipa_patcher():
    global ipa_entry, gameserver_entry, dlcserver_entry

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
        footer_frame, text="Bodnjenie™", bg="#2e2e2e", fg="#ffffff", anchor="e"
    )
    footer_label.pack(side="right", padx=10, pady=5)


def run_ipa_script(ipa_file, server_url, dlc_url):

    # Add a / to the end of the DLC URL
    if not dlc_url.endswith("/"):
        dlc_url += "/"

    extracted_folder = "tsto_ipa_extracted"
    updated_ipa = "tsto-patched.ipa"

    if not os.path.exists(ipa_file):
        messagebox.showerror("Error", f"The file {ipa_file} does not exist.")
        return

    # Extract IPA
    with zipfile.ZipFile(ipa_file, "r") as zip_ref:
        zip_ref.extractall(extracted_folder)

    app_folder = os.path.join(extracted_folder, "Payload", "Tapped Out.app")
    plist_path = os.path.join(app_folder, "Info.plist")
    binary_path = os.path.join(app_folder, "Tapped Out")

    try:
        # Include ios fix into Info.plist to force the game to use http only.
        # Credits to @Rudeboy for finding this fix!
        iosfix = "<key>NSAppTransportSecurity</key><dict><key>NSAllowsArbitraryLoads</key><true/></dict>"
        with open(plist_path, "r") as f:
            contents = f.readlines()

        contents.insert(4, iosfix)
        with open(plist_path, "w") as f:
            f.writelines(contents)

        # Read + update Info.plist
        with open(plist_path, "rb") as plist_file:
            plist_data = plistlib.load(plist_file)

        new_server_url = ""
        if "MayhemServerURL" in plist_data:
            new_server_url = server_url.rstrip("/")

            old_server_url = plist_data["MayhemServerURL"]

            if len(new_server_url) > len(old_server_url):
                raise ValueError("New MayhemServerURL is too long. Keep it short.")

            plist_data["MayhemServerURL"] = new_server_url
        else:
            print("Key 'MayhemServerURL' not found.")

        new_dlc_url = ""
        if "DLCLocation" in plist_data:
            new_dlc_url = dlc_url

            old_dlc_url = "https://oct2018-4-35-0-uam5h44a.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/"
            old_length = len(old_dlc_url)
            new_length = len(new_dlc_url)

            if new_length > old_length:
                raise ValueError("New DLCLocation URL is too long. Keep it short.")

            # If shorter, fill leftover space with `./` pairs (like `patch_url` does)
            leftover = old_length - new_length

            if leftover > 0:
                pairs_to_add = leftover // 2  # Each `./` takes 2 bytes
                new_dlc_url += './' * pairs_to_add

                # If there's one leftover byte, add a single `/`
                if leftover % 2 == 1:
                    new_dlc_url += '/'

            # Now, store the correctly padded DLC URL
            plist_data["DLCLocation"] = new_dlc_url
        else:
            print("Key 'DLCLocation' not found.")

        # Save updated Info.plist
        with open(plist_path, "wb") as plist_file:
            plistlib.dump(plist_data, plist_file)

        print(f"Updated {plist_path} successfully.")
        print(f"New MayhemServerURL: {new_server_url}")
        print(f"New DLCLocation: {new_dlc_url}")

        # Edit the binary file
        old_urls = [
            "http://oct2018-4-35-0-uam5h44a.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/",
            "https://syn-dir.sn.eamobile.com",
        ]
        new_urls = [new_dlc_url, new_server_url]

        with open(binary_path, "rb") as file:
            content = bytearray(file.read())

        # Replace URLs in the binary
        for old_url, new_url in zip(old_urls, new_urls):
            old_length = len(old_url)
            new_length = len(new_url)

            # If new URL is shorter, pad with `/` until it reaches exact length
            if new_length < old_length:
                new_url = new_url.ljust(old_length, "/")

            # If new URL is longer, truncate it to match the exact length
            elif new_length > old_length:
                new_url = new_url[:old_length]  # Cut off excess characters

            # Encode and replace
            old_url_bytes = old_url.encode()
            new_url_bytes = new_url.encode()

            content = content.replace(old_url_bytes, new_url_bytes)

        # Save edited binary
        with open(binary_path, "wb") as file:
            file.write(content)

        # Ignore IndexFileSig. Thanks SpAnser!
        with open(binary_path, "rb+") as file:
            print("Bypass IndexFileSig on IOS!")
            file.seek(9623264)
            file.write(b"\x01\x00\x00\x14")

        print(f"Updated {binary_path} successfully.")

        # Package the IPA
        with zipfile.ZipFile(updated_ipa, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(extracted_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, extracted_folder))

        print(f"Patched IPA saved as {updated_ipa}")
        messagebox.showinfo("Success", f"Patched IPA created: {updated_ipa}")

    except FileNotFoundError:
        messagebox.showerror("Error", "Required files not found.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


def browse_ipa_file():
    initialdir = Path.cwd()
    if Path("Original Files").exists() is True:
        initialdir = Path("Original Files")
    file_path = filedialog.askopenfilename(initialdir=initialdir, filetypes=[("IPA files", "*.ipa")])
    ipa_entry.delete(0, tk.END)
    ipa_entry.insert(0, file_path)


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
        text="@BodNJenie\n" "@tjac\n" "@AlekPM",
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
        text="@rudeboy\n" "@jjay121212\n" "@Popo\n" "@avariss\n" "@jani",
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


###############STARTUP

tappedout = Path("tappedout")
venv = Path("venv")
ipa = Path("tsto_ipa_extracted")
# Delete previous directories
if tappedout.exists() is True:
    shutil.rmtree(tappedout)
if venv.exists() is True:
    shutil.rmtree(venv)

start_selection()

# Delete previous directories
if tappedout.exists() is True:
    shutil.rmtree(tappedout)
if venv.exists() is True:
    shutil.rmtree(venv)
if ipa.exists() is True:
    shutil.rmtree(ipa)

# coded by @bodnjenie
# credit to @tjac for patching logic
# credit to @alekpm for ipa logic
