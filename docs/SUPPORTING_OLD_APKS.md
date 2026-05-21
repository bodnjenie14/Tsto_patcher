# Supporting old TSTO clients (≈4.25) — Patcher changes

This documents every change made to the patcher (`modules/`) to support old
TSTO builds such as **4.25.0**, alongside the modern (~4.69) ones. Companion
doc: the server-side behaviour spec (`OLD_CLIENT_SERVER_SUPPORT.md` in the
gameserver repo).

---

## TL;DR — what the patcher now does for an old APK

1. Redirects the gameserver / DLC URLs (any version's CDN host, not just 4.69's).
2. Bypasses the DLC package signature check (`dlcpk::PackageSignatureIsValid`).
3. Redirects the **TNT auth hosts** (`auth.tnt-ea.com`, `nucleus.tnt-ea.com`)
   baked into `libscorpio.so` — this is what lets a pre-Nucleus client log in.
4. Never corrupts a `.so` it doesn't recognise (all binary patches are guarded).

---

## Hard constraint: URL length (read this first)

Some URLs are patched **in place** inside the app binary (`libscorpio.so` /
the iOS Mach-O). An in-place string can only be replaced with one **≤ its
original length** — the slot cannot grow.

The tightest slot is the TNT auth host **`https://auth.tnt-ea.com` — 23 bytes**.
So for old APKs the **gameserver URL must be ≤ 23 characters**:

| Server URL | Length | OK for old APK? |
|---|---|---|
| `http://192.168.0.162:8080` | 25 | ✗ too long |
| `http://192.168.0.162:80`   | 23 | ✓ (port 80) |
| `http://192.168.0.5:8080`   | 23 | ✓ (short IP, keep 8080) |
| `http://10.0.0.162:8080`    | 22 | ✓ |

→ Either run the gameserver on **port 80**, or give the server a short LAN IP
(`http://` + IP + `:port` ≤ 23). The GUI shows a note about this next to the
gameserver field. If the URL is too long the patcher logs a `[WARNING]` and
skips that redirect (it never corrupts the binary).

---

## Changes by file

### `modules/gui.py`
- **Profiles now save the APK/IPA file path.** The profile `entries` dicts
  gained an `apk` / `ipa` key, so selecting a profile restores which app file
  to patch (previously only URLs/name/icon/version were saved).
- **`save_profile` reloads `profiles.json` from disk before merging**, so
  saving a profile in one tab no longer clobbers a profile saved in the other.
- Added a grey note by the gameserver field stating the ≤23-char limit for
  older apps.

### `modules/android.py`
- **`patch_url` returns `None` when the DLC string is not found** (it used to
  return the unchanged buffer). This is critical: the caller used the return
  value as "patch succeeded", so the old behaviour made it run version-locked
  byte-patches on unrecognised binaries and **corrupt them**.
- **`replace_and_log_urls` matches the DLC CDN host by regex** —
  `https?://<anything>.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/`
  — instead of one hard-coded host. 4.25 uses `jan2017-...`, 4.69 uses
  `oct2018-...`; both (and any other version) now redirect.
- **`SIG_BYPASS_RECIPES` — content-located signature-bypass.** Rather than
  hard-coded file offsets, a recipe finds a code pattern and patches it. The
  4.25 recipe rewrites `dlcpk::PackageSignatureIsValid`'s ARM epilogue
  (`MOV R0,R4` → `MOV R0,#1`) so it always reports the DLC signature valid.
  Recipes only apply when they match **exactly once** and the bytes at the
  site equal the expected original — safe on any build, idempotent.
- **`SIG_BYPASS_PATCHES` — version-locked offset table** (kept for 4.69.x).
  `detect_apk_version()` reads `apktool.yml`; `apply_sig_bypass()` is
  bounds-checked so a wrong-version offset can never write past EOF.
- **`patch_tnt_hosts` — redirects the TNT auth hosts.** Finds
  `https://auth.tnt-ea.com` and `https://nucleus.tnt-ea.com` in each `.so` and
  overwrites them with the gameserver URL (NUL-padded, length-checked, skipped
  with a warning if the URL is too long).
- **`perform_binary_patching` rewritten** and now takes `new_gameserver_url`.
  Per `.so`: DLC URL patch → signature-bypass recipes → TNT host redirect →
  version-locked offsets. Unknown builds are left untouched, not corrupted.

### `modules/ios.py`
- The binary-patch loop is now **length-safe** — it skips a replacement (with
  a `[WARNING]`) instead of `replace()`-ing a longer string and shifting /
  corrupting the Mach-O.
- Added `auth.tnt-ea.com` / `nucleus.tnt-ea.com` to the iOS binary URL
  redirect list (parity with Android).

---

## How to patch an old (4.25) APK

1. Run the gameserver on **port 80** (or a short LAN IP) so the URL is ≤23 chars.
2. In the patcher, set the gameserver / DLC fields to e.g. `http://192.168.0.162:80`.
3. Patch. Step 4's log should show **both**:
   ```
   [SUCCESS] Redirected https://auth.tnt-ea.com -> http://192.168.0.162:80
   [SUCCESS] Redirected https://nucleus.tnt-ea.com -> http://192.168.0.162:80
   [SUCCESS] Applied 'dlcpk::PackageSignatureIsValid -> always valid (TSTO 4.25.x)'
   ```
4. Install. The remaining work (DLC index, version gate, anonymous auth) is
   server-side — see `OLD_CLIENT_SERVER_SUPPORT.md`.

## Notes / limitations
- 4.25 APKs are **32-bit only** (`armeabi-v7a`, no `arm64-v8a`) — fine on
  emulators (MuMu etc.), will not run on 64-bit-only Android 12+ devices.
- 4.25's DLC URL lives in `AndroidManifest.xml`, not the `.so` (unlike 4.69),
  so no `.so` DLC patch is expected for it — that is normal.
