import os
import struct
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

ANDROID_ICON_NAMES = {
    "ic_launcher.png",
    "ic_launcher_round.png",
    "ic_launcher_foreground.png",
    "ic_launcher_background.png",
}

IOS_ICON_PREFIXES = ("Icon", "AppIcon")

# Files iOS falls back to (via CFBundleIconFiles AppIcon60x60 / AppIcon76x76)
# once CFBundleIconName is removed so the Assets.car icon is bypassed.
IOS_CANONICAL_ICONS = {
    "AppIcon60x60@2x.png": 120,
    "AppIcon60x60@3x.png": 180,
    "AppIcon76x76~ipad.png": 76,
    "AppIcon76x76@2x~ipad.png": 152,
    "AppIcon83.5x83.5@2x~ipad.png": 167,
}


def _png_size(path):
    with open(path, "rb") as f:
        header = f.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def _render(source_img, size):
    target = max(1, int(size))
    ratio = min(target / source_img.width, target / source_img.height)
    new_size = (
        max(1, round(source_img.width * ratio)),
        max(1, round(source_img.height * ratio)),
    )
    img = source_img.resize(new_size, Image.LANCZOS)
    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    offset = ((target - img.width) // 2, (target - img.height) // 2)
    canvas.paste(img, offset, img if img.mode == "RGBA" else None)
    return canvas


def replace_android_icons(decompiled_path, source_path):
    if not PIL_AVAILABLE:
        raise RuntimeError(
            "Pillow is required for icon replacement. Install it with: pip install Pillow"
        )

    res_dir = Path(decompiled_path, "res")
    if not res_dir.is_dir():
        print(f"res directory not found in {decompiled_path}. Skipping icon.")
        return

    with Image.open(source_path) as src:
        src = src.convert("RGBA")

        replaced = 0
        for root, _, files in os.walk(res_dir):
            for file in files:
                if file in ANDROID_ICON_NAMES:
                    file_path = Path(root, file)
                    size = _png_size(file_path)
                    target = size[0] if size else 192
                    _render(src, target).save(file_path, "PNG")
                    replaced += 1
                    print(f"Replaced {file_path} ({target}x{target})")

    print(f"Replaced {replaced} Android launcher icons.")


def replace_ios_icons(app_folder, source_path):
    if not PIL_AVAILABLE:
        raise RuntimeError(
            "Pillow is required for icon replacement. Install it with: pip install Pillow"
        )

    app_folder = Path(app_folder)
    if not app_folder.is_dir():
        print(f"App folder not found: {app_folder}. Skipping icon.")
        return

    with Image.open(source_path) as src:
        src = src.convert("RGBA")

        replaced = 0
        for file in app_folder.iterdir():
            if (
                file.is_file()
                and file.suffix.lower() == ".png"
                and file.name.startswith(IOS_ICON_PREFIXES)
            ):
                size = _png_size(file)
                target = size[0] if size else 180
                _render(src, target).save(file, "PNG")
                replaced += 1
                print(f"Replaced {file.name} ({target}x{target})")

        # The springboard icon lives in Assets.car (CFBundleIconName: AppIcon).
        # ios.py strips CFBundleIconName so iOS falls back to these loose
        # CFBundleIconFiles - make sure they exist at the right sizes.
        for name, dim in IOS_CANONICAL_ICONS.items():
            _render(src, dim).save(app_folder / name, "PNG")
            replaced += 1
            print(f"Wrote {name} ({dim}x{dim})")

    print(f"Replaced {replaced} iOS app icons.")
