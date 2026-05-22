import os
import re
import sys
import shutil
import subprocess
import requests
from pathlib import Path
from tkinter import  messagebox
from modules.misc import expand_url, safe_rmtree
from modules.icon import replace_android_icons, sanitize_png_resources

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
        "https://ping1.tnt-ea.com": new_gameserver_url,
        "https://www.google.com": new_gameserver_url,
        "com.ea.game.simpsons4_row": f"com.ea.game.simpsons4_row.{new_appname.replace(' ', '_')}",
        "com/ea/game/simpsons4_row": f"com/ea/game/simpsons4_row/{new_appname.replace(' ', '_')}",
        "Tapped Out</string>": new_appname + "</string>",
        "Springfield</string>": new_appname + "</string>",
        "4.69.5": new_version
    }

    # The DLC CDN host is version-specific (4.25 uses jan2017-4-25-0-ztk6mia7,
    # 4.69 uses oct2018-4-35-0-uam5h44a, etc.), so match ANY tstodlc host
    # rather than one hard-coded string. Captures http(s) and the full
    # "/netstorage/gameasset/direct/simpsons/" base path.
    dlc_url_pattern = re.compile(
        r"https?://[A-Za-z0-9.-]+\.tstodlc\.eamobile\.com"
        r"/netstorage/gameasset/direct/simpsons/"
    )

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

                # DLC CDN host (regex - any version's tstodlc subdomain).
                dlc_hit = dlc_url_pattern.search(content)
                if dlc_hit:
                    log.append(
                        f"Replaced DLC URL '{dlc_hit.group(0)}' with "
                        f"'{new_dlcserver_url}' in {file_path}"
                    )
                    content = dlc_url_pattern.sub(new_dlcserver_url, content)
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
        # Return None (not the unchanged bytes) so the caller can tell the
        # patch failed and must NOT proceed to write version-specific offsets.
        return None

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


# IndexFileSig signature-check bypass patches, keyed by game version.
#
# Each offset is reverse-engineered against one specific libscorpio.so build.
# They are NOT portable: writing these bytes into a different version's
# library overwrites unrelated code and the app will crash on launch
# ("won't open"). Only apply a set when the APK's version matches a key
# here. Thanks to SpAnser for the original 4.69.x offsets.
# IndexFileSig offsets reverse-engineered against the 4.69.5 libscorpio
# builds. The 4.70.0 release ships the same native libraries (versionCode
# 695), so it reuses the identical offsets - this is what the patcher applied
# unconditionally before the bypass was version-gated, and 4.70.0 worked.
_SIG_BYPASS_469 = {
    "lib/armeabi-v7a/libscorpio-neon.so": (4666332, b"\xca\xfd\xff\xea"),  # 0x4733dc
    "lib/armeabi-v7a/libscorpio.so": (4663220, b"\xd2\xfd\xff\xea"),       # 0x4727b4
    "lib/arm64-v8a/libscorpio-neon.so": (7519612, b"\x9f\x00\x00\x14"),    # 0x72bd7c
    "lib/arm64-v8a/libscorpio.so": (7519464, b"\x9f\x00\x00\x14"),         # 0x72bce8
}
SIG_BYPASS_PATCHES = {
    "4.69.5": _SIG_BYPASS_469,
    "4.70.0": _SIG_BYPASS_469,
}


def detect_apk_version(decompiled_path):
    """Read versionName from the apktool.yml produced by decompilation.

    Returns the raw version string (e.g. '4.69.5.1234') or None if it
    cannot be determined.
    """
    yml_path = os.path.join(decompiled_path, "apktool.yml")
    if not os.path.isfile(yml_path):
        return None
    try:
        with open(yml_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("versionName:"):
                    return stripped.split(":", 1)[1].strip().strip("'\"")
    except OSError as e:
        print(f"[WARN] Could not read apktool.yml: {e}")
    return None


def lookup_sig_bypass(version):
    """Return the bypass-patch table for the detected version, or None.

    Matches by prefix so build suffixes (e.g. '4.69.5.1234') still resolve
    to the '4.69.5' entry.
    """
    if not version:
        return None
    for key, patches in SIG_BYPASS_PATCHES.items():
        if version == key or version.startswith(key + "."):
            return patches
    return None


def apply_sig_bypass(file_path, rel_path, offset, expected_len, patch_bytes):
    """Write the IndexFileSig bypass bytes at a fixed offset, safely.

    Refuses to write if the offset would fall outside the file, which
    would corrupt the library."""
    file_size = os.path.getsize(file_path)
    if offset + len(patch_bytes) > file_size:
        print(
            f"[WARNING] Bypass offset {offset} is past the end of {rel_path} "
            f"({file_size} bytes). Skipping to avoid corruption."
        )
        return
    with open(file_path, "r+b") as f:
        f.seek(offset)
        f.write(patch_bytes)
    print(f"[SUCCESS] Bypassed IndexFileSig in {rel_path}.")


# Signature-based DLC signature-check bypass.
#
# Unlike SIG_BYPASS_PATCHES (fixed offsets, version-locked), each recipe here
# locates a code pattern by content, so it works regardless of where the code
# sits in the file - portable across .so variants and minor version changes.
# A recipe is only applied when it matches EXACTLY ONCE and the bytes at the
# patch site equal `expect`, so it can never corrupt an unrelated build.
#
# 4.25.x recipe - dlcpk::PackageSignatureIsValid (ARM). Its epilogue is:
#   LDR R2,[SP,#0x34]; MOV R0,R4; LDR R3,[R6]; CMP R2,R3;
#   BNE <stack_chk_fail>; ADD SP,SP,#0x3C; POP {R4-R11,PC}
# The function returns R4 (1 only if DSA_verify succeeded). Rewriting
# `MOV R0,R4` -> `MOV R0,#1` makes it always report the signature as valid.
# The BNE branch bytes are address-relative, so they are wildcarded.
SIG_BYPASS_RECIPES = [
    {
        "name": "dlcpk::PackageSignatureIsValid -> always valid (TSTO 4.25.x)",
        "pattern": re.compile(
            b"\x34\x20\x9d\xe5\x04\x00\xa0\xe1\x00\x30\x96\xe5\x03\x00\x52\xe1"
            b"..."  # BNE branch offset (address-relative) - wildcard
            b"\x1a\x3c\xd0\x8d\xe2\xf0\x8f\xbd\xe8",
            re.DOTALL,
        ),
        "patch_at": 4,                    # MOV R0,R4 within the match
        "expect": b"\x04\x00\xa0\xe1",     # MOV R0, R4
        "replace": b"\x01\x00\xa0\xe3",    # MOV R0, #1
    },
]


def apply_sig_bypass_recipes(data, rel_path):
    """Apply every matching signature-bypass recipe to `data` (a bytearray).

    Returns True if any recipe was applied. A recipe is skipped (with a
    message) unless it matches exactly once and the patch site holds the
    expected original bytes - this is what makes it safe on any build.
    """
    changed = False
    for recipe in SIG_BYPASS_RECIPES:
        hits = [m.start() for m in recipe["pattern"].finditer(bytes(data))]
        if not hits:
            continue
        if len(hits) > 1:
            print(
                f"[WARNING] Recipe '{recipe['name']}' matched {len(hits)} "
                f"times in {rel_path}; skipping (ambiguous)."
            )
            continue
        site = hits[0] + recipe["patch_at"]
        current = bytes(data[site:site + len(recipe["expect"])])
        if current != recipe["expect"]:
            print(
                f"[WARNING] Recipe '{recipe['name']}' site in {rel_path} "
                f"holds {current.hex()}, expected {recipe['expect'].hex()}; "
                f"skipping (already patched or wrong build)."
            )
            continue
        data[site:site + len(recipe["replace"])] = recipe["replace"]
        changed = True
        print(
            f"[SUCCESS] Applied '{recipe['name']}' in {rel_path} "
            f"at offset {hex(site)}."
        )
    return changed


# 4.25-era TNT auth hosts baked into libscorpio.so. A pre-Nucleus (~4.25)
# client runs its whole login handshake against these EA hosts; redirecting
# them to the private gameserver is what lets such clients authenticate.
TNT_AUTH_HOSTS = (b"https://auth.tnt-ea.com", b"https://nucleus.tnt-ea.com")


def patch_tnt_hosts(file_bytes, new_gameserver_url):
    """Redirect the hardcoded TNT auth hosts in a .so to the gameserver URL.

    Patched in place: the replacement is written over the original string and
    the rest of the slot NUL-filled. The slot cannot grow, so a gameserver URL
    longer than the original host string is reported and skipped rather than
    corrupting the binary (e.g. 'https://auth.tnt-ea.com' is only 23 bytes -
    needs a server URL that short, such as http://<ip>:80).
    """
    repl = new_gameserver_url.rstrip("/").encode("utf-8")
    changed = False
    for host in TNT_AUTH_HOSTS:
        offset = file_bytes.find(host)
        if offset < 0:
            continue
        if len(repl) > len(host):
            print(
                f"[WARNING] Cannot redirect {host.decode()}: gameserver URL "
                f"'{new_gameserver_url}' is {len(repl) - len(host)} byte(s) too "
                f"long for its {len(host)}-byte slot. Use a shorter server URL "
                f"(run the gameserver on port 80 so the URL fits)."
            )
            continue
        for i in range(len(host)):
            file_bytes[offset + i] = repl[i] if i < len(repl) else 0
        changed = True
        print(f"[SUCCESS] Redirected {host.decode()} -> {new_gameserver_url}")
    return changed


def perform_binary_patching(decompiled_path, new_dlcserver_url, new_gameserver_url):
    """
    Perform direct binary patching on the .so files: overwrite the DLC URL,
    redirect the TNT auth hosts to the gameserver, apply version-locked
    IndexFileSig offsets when the version is known, and apply content-located
    signature-bypass recipes (version-independent). Unknown builds are left
    unpatched rather than corrupted.
    """

    # List out all the known scorpio .so variants
    so_files = [
        "lib/armeabi-v7a/libscorpio.so",
        "lib/armeabi-v7a/libscorpio-neon.so",
        "lib/arm64-v8a/libscorpio.so",
        "lib/arm64-v8a/libscorpio-neon.so",
    ]

    version = detect_apk_version(decompiled_path)
    bypass_table = lookup_sig_bypass(version)
    if bypass_table is None:
        print(
            f"[INFO] APK version '{version}' has no version-locked "
            f"IndexFileSig offsets; relying on the content-located "
            f"signature-bypass recipes instead."
        )

    for rel_path in so_files:
        file_path = os.path.join(decompiled_path, rel_path)
        if not os.path.isfile(file_path):
            print(f"[INFO] File not found: {file_path}. Skipping.")
            continue

        print(f"[INFO] Found {rel_path}, attempting patch ...")

        try:
            with open(file_path, "rb") as src:
                data = bytearray(src.read())
            modified = False

            # 1) DLC URL string patch. patch_url() mutates `data` in place
            #    and returns it when the string is found, else None.
            if patch_url(data, new_dlcserver_url) is not None:
                modified = True
                print(f"[SUCCESS] Patched DLC URL in {rel_path}.")
            else:
                print(
                    f"[INFO] DLC string not found in {rel_path}; left "
                    f"unchanged (normal for versions whose DLC URL is "
                    f"server-supplied, e.g. 4.25.x)."
                )

            # 2) Signature-check bypass via content-located recipes
            #    (version-independent, safe on any build).
            if apply_sig_bypass_recipes(data, rel_path):
                modified = True

            # 2b) Redirect 4.25-era TNT auth hosts to the gameserver so
            #     pre-Nucleus clients can complete their login handshake.
            if patch_tnt_hosts(data, new_gameserver_url):
                modified = True

            # 3) Write back the changes from steps 1-2 in one pass.
            if modified:
                with open(file_path, "wb") as dst:
                    dst.write(data)

            # 4) IndexFileSig bypass via version-locked offsets, for builds
            #    covered by SIG_BYPASS_PATCHES (e.g. 4.69.x).
            if bypass_table and rel_path in bypass_table:
                offset, patch_bytes = bypass_table[rel_path]
                apply_sig_bypass(
                    file_path, rel_path, offset, len(patch_bytes), patch_bytes
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
        status("Step 4/5: Binary-patching .so libraries (DLC URL + TNT auth + signature bypass)...")
        perform_binary_patching("./tappedout", new_dlcserver_url, new_gameserver_url)

        # 4b) Replace the app icon if the user supplied one.
        if icon_path:
            status("Replacing app icon...")
            replace_android_icons("./tappedout", icon_path)

        # 4c) Repair any resources that are named *.png but aren't real PNGs
        # (EA ships some assets as PSD files) - aapt2 would fail to compile them.
        status("Sanitizing PNG resources...")
        sanitize_png_resources("./tappedout")

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

