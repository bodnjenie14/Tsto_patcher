from modules.gui import start_selection
from modules.misc import safe_rmtree

###############STARTUP

start_selection()

# Delete previous directories
safe_rmtree("tappedout")
safe_rmtree("venv")
safe_rmtree("tsto_ipa_extracted")

# coded by @bodnjenie and @dractiums
# credit to @tjac for patching logic
# credit to @alekpm for ipa logic
