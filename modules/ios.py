import os
import shutil
import plistlib
import zipfile
from pathlib import Path
from tkinter import messagebox
from modules.misc import expand_url, safe_rmtree
from modules.icon import replace_ios_icons

def run_ipa_script(ipa_file, server_url, dlc_url, bundle_id, appname, version, icon_path=None, status=print):
    # Remove previous extracted folder.
    status("Cleaning up previous extracted folder...")
    safe_rmtree("tsto_ipa_extracted")
    extracted_folder = Path("tsto_ipa_extracted")

    # Remove a / at the end of the server URL.
    if server_url.endswith("/"):
        server_url = server_url[:-1]

    # Add a / to the end of the DLC URL
    if not dlc_url.endswith("/"):
        dlc_url += "/"

    if not os.path.exists(ipa_file):
        messagebox.showerror("Error", f"The file {ipa_file} does not exist.")
        return


    # Avoid empty bundle identifier, app name and version.
 
    if bundle_id == "":
        bundle_id = "com.ea.simpsonssocial.inc2"
    
    if appname == "":
        appname = "Tapped Out"

    if version == "":
        version = "4.69.5"

    # Extract IPA
    status("Step 1/4: Extracting IPA...")
    with zipfile.ZipFile(ipa_file, "r") as zip_ref:
        zip_ref.extractall(extracted_folder)

    app_folder = Path(extracted_folder, "Payload", "Tapped Out.app")
    binary_path = Path(app_folder, "Tapped Out")

    try:
        # Replace the app icon if the user supplied one.
        if icon_path:
            if not os.path.exists(icon_path):
                messagebox.showerror("Error", f"Icon file {icon_path} does not exist.")
                return
            status("Replacing app icon...")
            replace_ios_icons(app_folder, icon_path)

        status("Step 2/4: Updating Info.plist (bundle id, name, version, URLs)...")
        # Read + update InfoPlist.strings
        for plist_path in Path(app_folder).glob("*/InfoPlist.strings"):
            with open(plist_path, "rb") as plist_file:
                plist_data = plistlib.load(plist_file)
                plist_data["CFBundleDisplayName"] = appname
                plist_data["CFBundleName"] = appname

            with open(plist_path, "wb") as string_file:
                plistlib.dump(plist_data,  string_file)

        # Read + update Info.plist
        plist_path = Path(app_folder, "Info.plist")

        with open(plist_path, "rb") as plist_file:
            plist_data = plistlib.load(plist_file)

        # Include ios fix into Info.plist to force the game to use http only.
        # Credits to @Rudeboy and @BodNJenie for finding this fix!
        # Add NSAppTransportSecurity settings at the top level
        plist_data["NSAppTransportSecurity"] = {"NSAllowsArbitraryLoads": True}

        # Set Bundle identifier, bundle display name and version.
        #
        plist_data["CFBundleIdentifier"] = bundle_id

        plist_data["CFBundleDisplayName"] = appname
        plist_data["CFBundleName"] = appname
 
        plist_data["CFBundleShortVersionString"] = version
        plist_data["CFBundleVersion"] = version

        # The home-screen icon comes from Assets.car via CFBundleIconName.
        # We can't rebuild Assets.car on Windows, so drop CFBundleIconName to
        # make iOS fall back to the loose CFBundleIconFiles PNGs we replaced.
        if icon_path:
            for key in ("CFBundleIcons", "CFBundleIcons~ipad"):
                icons = plist_data.get(key)
                if isinstance(icons, dict):
                    primary = icons.get("CFBundlePrimaryIcon")
                    if isinstance(primary, dict):
                        primary.pop("CFBundleIconName", None)
                        files = list(primary.get("CFBundleIconFiles") or [])
                        for n in ("AppIcon60x60", "AppIcon76x76"):
                            if n not in files:
                                files.append(n)
                        primary["CFBundleIconFiles"] = files
            plist_data.pop("CFBundleIconName", None)

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

        # Edit the binary file. auth.tnt-ea.com / nucleus.tnt-ea.com are the
        # pre-Nucleus (~4.25) auth hosts - redirecting them to the gameserver
        # is what lets old iOS clients log in (parity with the Android patch).
        old_urls = [
            "http://oct2018-4-35-0-uam5h44a.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/",
            "https://syn-dir.sn.eamobile.com",
            "https://ping1.tnt-ea.com",
            "https://auth.tnt-ea.com",
            "https://nucleus.tnt-ea.com",
        ]
        new_urls = [
            new_dlc_url,
            new_server_url,
            "https://google.com",
            new_server_url,
            new_server_url,
        ]

        status("Step 3/4: Binary-patching the app (URLs + signature bypass)...")
        with open(binary_path, "rb") as file:
            content = bytearray(file.read())

        # Replace URLs in the binary. This is an in-place patch, so the
        # replacement must be NO LONGER than the original slot - a longer
        # string would shift the Mach-O and corrupt it. The shortest slot
        # here is 'https://auth.tnt-ea.com' (23 chars), so for older apps the
        # gameserver URL must be <= 23 chars (e.g. http://192.168.0.5:80).
        for old_url, new_url in zip(old_urls, new_urls):
            old_url_bytes = old_url.encode()
            if old_url_bytes not in content:
                continue

            old_length = len(old_url)
            new_url = expand_url(new_url, old_length)

            if len(new_url) > old_length:
                print(
                    f"[WARNING] Cannot redirect {old_url}: '{new_url}' is "
                    f"{len(new_url) - old_length} byte(s) too long for its "
                    f"{old_length}-byte slot. Use a shorter gameserver URL "
                    f"(<= {old_length} chars, e.g. server on port 80)."
                )
                continue

            content = content.replace(old_url_bytes, new_url.encode())
            print(f"[SUCCESS] Redirected {old_url} -> {new_url}")

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
        status("Step 4/4: Repackaging IPA...")
        updated_ipa = f"{appname.replace(' ', '_')}.ipa"
        with zipfile.ZipFile(updated_ipa, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(extracted_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, extracted_folder))

        print(f"Patched IPA saved as {updated_ipa}")
        status(f"Done. Patched IPA created: {updated_ipa}")
        messagebox.showinfo("Success", f"Patched IPA created: {updated_ipa}")

    except FileNotFoundError:
        messagebox.showerror("Error", "Required files not found.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
