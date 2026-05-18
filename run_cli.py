import argparse
import os
import tkinter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


class _ConsoleMessageBox:
    @staticmethod
    def showinfo(title, message):
        print(f"[INFO] {title}: {message}")

    @staticmethod
    def showerror(title, message):
        print(f"[ERROR] {title}: {message}")

    @staticmethod
    def showwarning(title, message):
        print(f"[WARN] {title}: {message}")

    @staticmethod
    def askyesno(title, message):
        print(f"[ASK] {title}: {message} -> YES")
        return True


tkinter.messagebox = _ConsoleMessageBox

import modules.android as android
import modules.ios as ios
from modules.config import load_profiles

android.messagebox = _ConsoleMessageBox
ios.messagebox = _ConsoleMessageBox


class _ConsoleProgressBar:
    def start(self, *args):
        print("Progress started")

    def stop(self, *args):
        print("Progress stopped")


def default_source(ext):
    candidate = PROJECT_ROOT / "Original Files" / f"tsto_original.{ext}"
    return str(candidate) if candidate.exists() else None


def merge(arg_value, profile, key):
    if arg_value:
        return arg_value
    return profile.get(key, "")


def main():
    parser = argparse.ArgumentParser(description="TSTO patcher (CLI)")
    sub = parser.add_subparsers(dest="platform", required=True)

    apk = sub.add_parser("apk")
    apk.add_argument("--profile")
    apk.add_argument("--file")
    apk.add_argument("--gameserver")
    apk.add_argument("--dlc")
    apk.add_argument("--appname", default="")
    apk.add_argument("--version", default="")
    apk.add_argument("--icon")

    ipa = sub.add_parser("ipa")
    ipa.add_argument("--profile")
    ipa.add_argument("--file")
    ipa.add_argument("--gameserver")
    ipa.add_argument("--dlc")
    ipa.add_argument("--bundleid", default="")
    ipa.add_argument("--appname", default="")
    ipa.add_argument("--version", default="")
    ipa.add_argument("--icon")

    args = parser.parse_args()

    profile = {}
    if args.profile:
        profiles = load_profiles()
        if args.profile not in profiles:
            parser.error(
                f"Profile '{args.profile}' not found. Available: "
                + ", ".join(profiles) if profiles else "(none)"
            )
        profile = profiles[args.profile]

    ext = args.platform
    source = args.file or default_source(ext)
    gameserver = merge(args.gameserver, profile, "gameserver")
    dlc = merge(args.dlc, profile, "dlc")
    appname = merge(args.appname, profile, "appname")
    version = merge(args.version, profile, "version")
    icon = args.icon or profile.get("icon") or None

    if not source or not os.path.exists(source):
        parser.error(f"Source file not found: {source!r} (use --file)")
    if not gameserver or not dlc:
        parser.error("--gameserver and --dlc are required (directly or via --profile)")

    if args.platform == "apk":
        android.run_apk_script(
            source, gameserver, dlc, appname, version,
            _ConsoleProgressBar(), icon,
        )
    else:
        bundleid = merge(args.bundleid, profile, "bundleid")
        ios.run_ipa_script(
            source, gameserver, dlc, bundleid, appname, version, icon,
        )


if __name__ == "__main__":
    main()
