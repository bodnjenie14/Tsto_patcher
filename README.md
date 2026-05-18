# TSTO-Patchers
Game patchers for TSTO.

## Requirements
* **Python 3** (run the patcher)
* **A JDK** (Java) on your PATH - used for `java`/`keytool`/`jarsigner` when
  patching APKs. `apktool_2.10.0.jar` is bundled.
* **Pillow** (optional, only for the app-icon feature): `pip install Pillow`

No virtualenv, no Android SDK and no `buildapp`/pip downloads are needed - the
APK is rebuilt with the bundled apktool and signed with the JDK's own
`jarsigner`, so it works behind strict firewalls/antivirus.

## How to use
1. Run tsto_patcher.py in CMD
```
python tsto_patcher.py
```
2. Select if you wish to patch an APK (Android) or IPA (IOS)
3. The bundled `Original Files/tsto_original.apk` (or `.ipa`) is filled in
   automatically. Click "Browse" if you want a different file
4. *(Optional)* Pick a **Profile** from the dropdown to auto-fill the saved
   fields (see [Profiles](#profiles) below)
5. Input your server URL **e.g. http://192.168.1.10:80**
6. Input your DLC URL **e.g. http://192.168.1.11:80/static/**
7. *(Optional)* Click "Browse" next to **App Icon** to pick a PNG/JPG that
   replaces the launcher icon (works for both APK and IPA). Leave it blank to
   keep the original icon. Requires Pillow: `pip install Pillow`
8. Click "Patch (APK/IPA)". The progress bar and the status line under it
   show each step live (also printed to the console)
9. If there are any errors, click "Check Dependencies"
10. Your new file is created next to the patcher, named after the app display
   name (spaces become underscores):<br>
APK: `Bods_Tapped_Out.apk` (rebuilt with apktool and signed)<br>
IPA: `Bods_Tapped_Out.ipa`

## Profiles
Profiles save the form fields so you can apply them with one click. Pick a
profile from the **Profile** dropdown to fill the fields; fill the form and
click **Save Profile** to store the current values (it asks for a name -
keeping the same name overwrites that profile). Works on both the APK and IPA
screens.

A profile can hold any of: `gameserver`, `dlc`, `appname`, `version`,
`bundleid` (IPA only) and `icon` (a path to an image file). Only the keys you
filled in are saved, and selecting a profile only overwrites the fields it has.

Profiles live in `profiles.json` next to the patcher. It's created on first
run with two defaults and can also be edited by hand:

```json
{
  "profiles": {
    "Bods": {
      "gameserver": "http://192.168.0.162:8080",
      "dlc": "http://192.168.0.162:8080/static"
    },
    "Beta": {
      "gameserver": "https://test.pjtsto.com/",
      "dlc": "https://cdn.projectspringfield.com/static/"
    }
  }
}
```

## Command line (headless)
For automation or when you want full console output without the GUI.

Use a saved profile (shortest form - `--file` defaults to the bundled
`Original Files/tsto_original.apk`/`.ipa`):

```
python run_cli.py apk --profile Bods
python run_cli.py ipa --profile Beta
```

Or pass everything explicitly (any flag overrides the profile):

```
python run_cli.py apk --file "Original Files/tsto_original.apk" \
    --gameserver http://192.168.0.162:8080 --dlc http://192.168.0.162:8080/static \
    --appname "Bods Tapped Out" --version 4.70.0 --icon path/to/icon.png
```

`--profile`, `--file`, `--appname`, `--version`, `--icon` (and `--bundleid`
for IPA) are optional; `--gameserver` and `--dlc` must come from either the
flags or the profile.

## V4

**Changes:**
* App icon replacement for both APK and IPA - optional image picked in the GUI
  is resized into every icon slot (needs Pillow)
* Profiles: `profiles.json` presets (ships with `Bods` and `Beta`), a
  **Profile** dropdown and a **Save Profile** button that stores the current
  fields (gameserver, dlc, appname, version, bundleid, icon)
* APK rebuild no longer uses a virtualenv / `buildapp` / Android SDK / pip -
  it rebuilds with the bundled apktool and signs with the JDK's `jarsigner`
  (works behind strict firewalls/antivirus that block PyPI)
* Patching runs on a background thread so the window no longer freezes; a
  status line shows each step live and everything is printed to the console
* The bundled `Original Files` APK/IPA is auto-filled (resolved relative to
  the patcher, so it stays portable)
* Headless `run_cli.py` for command-line use, including `--profile`
* Sturdier cleanup that doesn't crash on locked/read-only files, and timeouts
  on all downloads so nothing hangs forever
* Fixed the APK/IPA windows never starting their event loop

## V3 - 10/02/2025
[V3](https://github.com/AlekMunroe/TSTO-Patchers/releases/tag/V3)

**Changes:**
* Removed system check for windows
* Added placeholders for the input urls
* Updated the IPA URLs to follow the same byte length rules as the APK URLs


## V2 - 10/02/2025
[V2](https://github.com/AlekMunroe/TSTO-Patchers/releases/tag/V2)

This is a modified version of [Bodjenie's](https://github.com/bodnjenie14/Patch-Apk) patcher.
This version supports both IPA (IOS) and APK (Android) files.

This is a merge of both patchers from [V1](https://github.com/AlekMunroe/TSTO-Patchers/releases/tag/V1).

**Notes**
* This patcher only supports Windows. Support for MacOS and Linux **Coming soon!**


## V1 - 09/02/2025
[V1](https://github.com/AlekMunroe/TSTO-Patchers/releases/tag/V1)

Game patchers for both IPA (IOS) and APK (Android) files.
These are two seperate patchers both in their own dedicated folders.

### Android
The Android patcher was built by [Bodnjenie](https://github.com/bodnjenie14/)

**Notes**
* The Android game patcher only supports Windows. Support for MacOS and Linux **Coming soon!**

### IOS
The IOS patcher supports an tsto.ipa file which must be located in the same directory as the IPA_Gae_Patcher.py file.

**Notes**
* The IOS game patcher does not have a GUI. This will be added in the **Next release**.
