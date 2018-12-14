# blender-nightly
Update to the latest Blender automatic (nightly) builds using this web-based installer (with multi-version support).

## Install
* Install Python--on Windows, "Add Python 3.x to PATH" option is recommended BEFORE clicking "Install Now". (install `python3` package on GNU+Linux systems; on Windows, download and install from [python.org](http://www.python.org))
* Download this program
* Open the downloaded file then Extract All, then view extracted files.

## Use
* Make sure you are connected to the internet
* Double-click update.pyw (on Windows, open With: "C:\Python??\pythonw.exe")
* The program should open a new small square Window, and immediately get the download links matching your platform (if the version, OS Name, and architecture flags are incorrect, you can correct them then click "Refresh")
* Click "Install" button for the version you want to install. The "Blender 2.8" desktop icon will be created or updated.

## Known Issues
* hangs on start on older versions of Python on Windows (Python 3.2.5, Python 2.7.10)

## Developer Notes

### poikilos work log
(2018-12-12)
* ~8hrs code in "initial commit" (actually 2nd, but first with code)
(2018-12-13)
* ~9.5hrs "first working version" commit
* ~1hr test and fix on Windows
