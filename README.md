# TSTO-Patchers
Game patchers for TSTO.

## How to use
1. Run tsto_patcher.py in CMD
```
python tsto_patcher.py
```
2. Select if you wish to patch an APK (Android) or IPA (IOS)
3. Click "Browse" and select your APK/IPA
4. Input your server URL **e.g. http://192.168.1.10:80**
5. Input your DLC URL **e.g. http://192.168.1.11:80/static/**
6. Click "Patch (APK/IPA)"
7. If there are any errors, click "Check Dependencies"
8. Your new file will be created:<br>
APK: FILENAME-patched.apk<br>
IPA: tsto-patched.ipa

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
