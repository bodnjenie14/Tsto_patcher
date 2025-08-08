import os
import shutil
import plistlib
import zipfile
from pathlib import Path
from tkinter import messagebox
from modules.misc import expand_url

def run_ipa_script(ipa_file, server_url, dlc_url, appname, version):
    # Remove previous extracted folder.
    extracted_folder = Path("tsto_ipa_extracted")
    if extracted_folder.exists() is True:
        shutil.rmtree(extracted_folder)

    # Remove a / at the end of the server URL.
    if server_url.endswith("/"):
        server_url = server_url[:-1]

    # Add a / to the end of the DLC URL
    if not dlc_url.endswith("/"):
        dlc_url += "/"

    if not os.path.exists(ipa_file):
        messagebox.showerror("Error", f"The file {ipa_file} does not exist.")
        return


    # Avoid empty app name.
    if appname == "":
        appname = "Tapped Out"

    if version == "":
        version = "4.69.5"

    # Extract IPA
    with zipfile.ZipFile(ipa_file, "r") as zip_ref:
        zip_ref.extractall(extracted_folder)

    app_folder = os.path.join(extracted_folder, "Payload", "Tapped Out.app")
    plist_path = os.path.join(app_folder, "Info.plist")
    binary_path = os.path.join(app_folder, "Tapped Out")

    try:
        # Read + update Info.plist
        with open(plist_path, "rb") as plist_file:
            plist_data = plistlib.load(plist_file)

        # Include ios fix into Info.plist to force the game to use http only.
        # Credits to @Rudeboy and @BodNJenie for finding this fix!
        # Add NSAppTransportSecurity settings at the top level
        plist_data["NSAppTransportSecurity"] = {"NSAllowsArbitraryLoads": True}

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
            # Store the the DLC URL.
            plist_data["DLCLocation"] = dlc_url

            new_dlc_url = dlc_url

            old_dlc_url = "http://oct2018-4-35-0-uam5h44a.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/"
            old_length = len(old_dlc_url)
            new_length = len(new_dlc_url)

            if new_length > old_length:
                raise ValueError("New DLCLocation URL is too long. Keep it short.")

            new_dlc_url = expand_url(new_dlc_url, old_length)

        else:
            print("Key 'DLCLocation' not found.")

        # Save updated Info.plist
        with open(plist_path, "wb") as plist_file:
            plistlib.dump(plist_data, plist_file)

        print(f"Updated {plist_path} successfully.")
        print(f"New MayhemServerURL: {new_server_url}")
        print(f"New DLCLocation: {dlc_url}")

        # Edit the binary file
        old_urls = [
            "http://oct2018-4-35-0-uam5h44a.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/",
            "https://syn-dir.sn.eamobile.com",
            "https://ping1.tnt-ea.com",
        ]
        new_urls = [new_dlc_url, new_server_url, "https://google.com"]

        with open(binary_path, "rb") as file:
            content = bytearray(file.read())

        # Replace URLs in the binary
        for old_url, new_url in zip(old_urls, new_urls):
            old_length = len(old_url)
            new_length = len(new_url)

            new_url = expand_url(new_url, old_length)

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

        # Replace
        replace_and_log_urls(
            extracted_folder, appname, version
        )

        # Package the IPA
        updated_ipa = f"{appname.replace(' ', '_')}.ipa"
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


def replace_and_log_urls(
    extracted_folder, new_appname, new_version
):
    """
    Replace server URLs in the decompiled APK and log only the replacements.

    This primarily modifies text-based files (.smali, .xml, .txt, .yml).
    It does NOT handle binary .so patching.
    """

    replacements = {
        "Tapped Out</string>": new_appname + "</string>",
        "Springfield</string>": new_appname + "</string>",
        "4.69.5": new_version
    }

    log = []  # Store logs of replacements

    for root, _, files in os.walk(Path(extracted_folder, "Payload", "Tapped Out.app")):
        for file in files:
            file_path = os.path.join(root, file)

            # Only process text-like files
            if file_path.endswith((".xml", ".strings", ".plist")):
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
