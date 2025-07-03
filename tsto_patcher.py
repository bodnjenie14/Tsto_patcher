from pathlib import Path
import shutil
from modules.gui import start_selection

###############STARTUP

start_selection()

# Delete previous directories
tappedout = Path("tappedout")
venv = Path("venv")
ipa = Path("tsto_ipa_extracted")
if tappedout.exists() is True:
    shutil.rmtree(tappedout)
if venv.exists() is True:
    shutil.rmtree(venv)
if ipa.exists() is True:
    shutil.rmtree(ipa)

# coded by @bodnjenie and @dractiums
# credit to @tjac for patching logic
# credit to @alekpm for ipa logic
