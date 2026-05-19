import os
import sys
import shutil
import subprocess
import requests
from pathlib import Path
from tkinter import  messagebox
from modules.misc import expand_url, safe_rmtree
from modules.icon import replace_android_icons

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


def run_streamed(cmd, status=print):
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            status(line)
    proc.wait()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


APKTOOL_JAR = "apktool_2.10.0.jar"
UBER_SIGNER_JAR = "uber-apk-signer-1.3.0.jar"
UBER_SIGNER_URL = (
    "https://github.com/patrickfav/uber-apk-signer/releases/download/"
    "v1.3.0/uber-apk-signer-1.3.0.jar"
)


def install_dependencies(status=print):
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

    # We rebuild with `java -jar apktool` and sign with uber-apk-signer
    # (zipalign + v1/v2/v3, needed for Android 11+/MuMu). No pip/SDK/venv -
    # those break behind strict AV/firewalls.
    if not os.path.isfile(APKTOOL_JAR):
        status("Downloading apktool...")
        download_file(
            "https://github.com/iBotPeaches/Apktool/releases/download/v2.10.0/apktool_2.10.0.jar",
            APKTOOL_JAR,
        )

    if not os.path.isfile(UBER_SIGNER_JAR):
        status("Downloading uber-apk-signer...")
        download_file(UBER_SIGNER_URL, UBER_SIGNER_JAR)


def download_file(url, dest):
    """Download a file from the specified URL to the destination path."""
    try:
        with requests.get(url, stream=True, timeout=30) as req:
            if req.status_code != 200:
                messagebox.showerror(
                    "Download Error",
                    f"Failed to download {url}. Status code = {req.status_code}",
                )
                sys.exit(1)
            with open(dest, "wb") as f:
                for chunk in req.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)

    except Exception as e:
        messagebox.showerror("Download Error", f"Failed to download {url}: {e}")
        sys.exit(1)


def decompile_app(input_filename):
    """Decompile the APK file."""
    subprocess.run(
        ["java", "-jar", "apktool_2.10.0.jar", "d", input_filename, "-o", "tappedout"],
        check=True,
    )

def replace_and_log_urls(
    new_gameserver_url, new_dlcserver_url, new_appname, new_version
):
    """
    Replace server URLs in the decompiled APK and log only the replacements.

    This primarily modifies text-based files (.smali, .xml, .txt, .yml).
    It does NOT handle binary .so patching.
    """

    replacements = {
        "https://prod.simpsons-ea.com": new_gameserver_url,
        "https://syn-dir.sn.eamobile.com": new_gameserver_url,  # Director uses same as gameserver.
        "https://oct2018-4-35-0-uam5h44a.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/": new_dlcserver_url,  # Update dlc server url.
        "https://ping1.tnt-ea.com": new_gameserver_url,
        "https://www.google.com": new_gameserver_url,
        "com.ea.game.simpsons4_row": f"com.ea.game.simpsons4_row.{new_appname.replace(' ', '_')}",
        "com/ea/game/simpsons4_row": f"com/ea/game/simpsons4_row/{new_appname.replace(' ', '_')}",
        "Tapped Out</string>": new_appname + "</string>",
        "Springfield</string>": new_appname + "</string>",
        "4.69.5": new_version
    }

    log = []  # Store logs of replacements

    for root, _, files in os.walk("./tappedout/"):
        for file in files:
            file_path = os.path.join(root, file)

            # Only process text-like files
            if file_path.endswith((".xml", ".smali", ".txt", ".yml")):
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
    as the original string. DLC URL is always expanded with a default port number if one is not specified.

    - If the new URL is shorter, append leading zeros to port number.
    - If it's longer, either truncate it or raise an error (see the code comment).
    """

    # The original DLC URL in the .so
    original_bytes = b"http://oct2018-4-35-0-uam5h44a.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/"
    offset = file_bytes.find(original_bytes)
    if offset < 0:
        print("[!] Could not find the DLC URL in this file. Skipping patch.")
        return file_bytes

    # The original URL length (often 88 bytes)
    original_len = len(original_bytes)

    # 1) Force the new URL to end with '/static/'
    #    - Strip any trailing slash, then add '/static/'
    #    - e.g. "http://example.com" => "http://example.com/static/"
    #    - e.g. "http://example.com/" => "http://example.com/static/"
    new_url = expand_url(new_url, original_len)

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


def recompile_app(input_filename, new_appname, status=print):
    """Rebuild the patched APK with apktool, then zipalign + sign it with
    uber-apk-signer (v1/v2/v3 - required for Android 11+/MuMu)."""

    # Produce unique apk.
    base_package_path = Path("tappedout", "smali", "com", "ea", "game", "simpsons4_row")
    files = list(base_package_path.iterdir())
    target = Path(base_package_path, new_appname.replace(" ", "_"))
    target.mkdir()

    for file in files:
        os.rename(file, Path(target, file.name))

    safe_name = new_appname.replace(" ", "_")
    output_filename = f"{safe_name}.apk"
    if os.path.isfile(output_filename):
        os.remove(output_filename)

    status("Building APK with apktool...")
    run_streamed(
        ["java", "-jar", APKTOOL_JAR, "b", "tappedout", "-o", output_filename],
        status,
    )

    # zipalign + v1/v2/v3 sign with a built-in debug key, in place.
    status("Zipaligning and signing APK (v1/v2/v3)...")
    run_streamed(
        [
            "java", "-jar", UBER_SIGNER_JAR,
            "--apks", output_filename,
            "--overwrite",
            "--allowResign",
        ],
        status,
    )
    return output_filename


def process_apk(input_filename, new_gameserver_url, new_dlcserver_url, new_appname, new_version, progress_bar, icon_path=None, status=print):
    try:
        progress_bar.start()

        os.environ["SOURCE_OUTPUT"] = "./tappedout"
        os.environ["APK_FILE"] = input_filename
        os.environ["DLC_URL"] = new_dlcserver_url
        os.environ["GAMESERVER_URL"] = new_gameserver_url
        os.environ["DIRECTOR_URL"] = new_gameserver_url

        # 1) Install dependencies
        status("Step 1/5: Checking dependencies (apktool + JDK)...")
        install_dependencies(status)

        # 2) Decompile the APK
        status("Step 2/5: Decompiling APK with apktool...")
        decompile_app(input_filename)

        # 3) Replace text-based references (gameserver, director, etc.):
        status("Step 3/5: Replacing gameserver/DLC URLs and app name...")
        replace_and_log_urls(
            new_gameserver_url, new_dlcserver_url, new_appname, new_version
        )

        # 4) Perform direct binary patching on .so files for the DLC URL
        status("Step 4/5: Binary-patching .so libraries (DLC URL + signature bypass)...")
        perform_binary_patching("./tappedout", new_dlcserver_url)

        # 4b) Replace the app icon if the user supplied one.
        if icon_path:
            status("Replacing app icon...")
            replace_android_icons("./tappedout", icon_path)

        # 5) Recompile the patched APK
        status("Step 5/5: Rebuilding and signing APK (apktool)... this is the slow part, please wait.")
        output_filename = recompile_app(input_filename, new_appname, status)

        status(f"Done. Patched APK created: {output_filename}")
        messagebox.showinfo("Success", f"Patched APK created: {output_filename}")
    except FileNotFoundError as e:
        status(f"Failed: {e}")
        messagebox.showerror("Dependency Error", str(e))
    except subprocess.CalledProcessError as e:
        status(f"Failed: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")
        progress_bar.stop()


def run_apk_script(apk_file, gameserver_url, dlc_url, appname, version, progress_bar, icon_path=None, status=print):
    # Delete previous directories.
    status("Cleaning up previous build folders...")
    safe_rmtree("tappedout")
    safe_rmtree("venv")


    # Remove a / at the end of the gameserver URL
    if gameserver_url.endswith("/"):
        gameserver_url = gameserver_url[:-1]

    # Add a / to the end of the DLC URL
    if not dlc_url.endswith("/"):
        dlc_url += "/"

    # Check all inputs
    if not apk_file or not gameserver_url or not dlc_url:
        messagebox.showerror("Error", "All fields are required!")
        return

    # Avoid empty app name.
    if appname == "":
        appname = "Tapped Out"

    if version == "":
        version = "4.69.5"

    # Validate the optional custom icon.
    if icon_path and not os.path.exists(icon_path):
        messagebox.showerror("Error", f"Icon file {icon_path} does not exist.")
        return

    # Run the process
    try:
        process_apk(apk_file, gameserver_url, dlc_url, appname, version, progress_bar, icon_path, status)
    except Exception as e:
        status(f"Failed: {e}")
        messagebox.showerror("Error", "An unexpected error has occured: " + str(e))

