#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import platform

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
repoDir = os.path.dirname(MODULE_DIR)
reposDir = os.path.dirname(repoDir)
tryHRepoDir = os.path.join(reposDir, "hierosoft")
if os.path.isfile(os.path.join(tryHRepoDir, "hierosoft", "__init__.py")):
    sys.path.append(tryHRepoDir)

if __name__ == "__main__":
    sys.path.insert(0, repoDir)  # find blendernightly if __file__ runs directly

from blendernightly.find_hierosoft import hierosoft

from hierosoft import (
    gui_tk,  # contains most code formerly below.
)

from hierosoft.gui_tk import (
    tk,
    get_tk,
    HierosoftUpdateFrame,
)



def main():
    # Copied from gui_tk.main:
    root = get_tk()
    '''
    try:
        root = tk.Tk()
    except tk.TclError as ex:
        echo0(str(ex))
        echo0()
        echo0("FATAL ERROR: Cannot use tkinter from terminal")
        return 1
    '''
    Darwin_arch = "x64"  # Blender-specific filename substring
    if platform.system() == "Darwin":
        if "arm64" in platform.platform():
            # such as "macOS-12.0.1-arm64-i386-64bit"
            # as seen at <https://stackoverflow.com/a/70253434/4541104>
            Darwin_arch = "arm64"  # Blender-specific filename substring

    options = {
        'title': "Blender Nightly",
        'version': "3.3.2",  # formerly parser.release_version
        # ^ formerly  "/download//blender-*"
        'platforms': {
            'Linux': "linux",
            'Windows': "windows",
            'Darwin': "macos",
        },
        'architectures': {
            'Linux': ["x86_64", "x64"],
            'Windows': "x64",
            'Darwin': Darwin_arch,  # ["x64", "arm64"],
        },
        'must_contain': "/blender-",
        'html_url': "https://builder.blender.org/download/",
        'bin_names': ["blender", "blender.exe"],
    }
    parent = root  # set to something else to put updater in a sub-frame
    app = HierosoftUpdateFrame(parent, root, options)
    # app.pack(side="top", fill="both", expand=True)
    root.after(500, app.start_refresh)
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main())
    # sys.argv = sys.argv[1:]
    # sys.argv.append("--title")
    # sys.argv.append("Blender Nightly Update")
    # sys.exit(gui_tk.main())
