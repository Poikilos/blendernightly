# blender-nightly
Update to the latest Blender automatic (nightly) builds using this web-based installer (with multi-version support).
![screenshot](https://raw.githubusercontent.com/poikilos/blendernightly/master/screenshot.png)

## Install
* Install Python--on Windows, "Add Python 3.x to PATH" option is recommended BEFORE clicking "Install Now". (install `python3` package on GNU+Linux systems; on Windows, download and install from [python.org](http://www.python.org))
* Download this program (at [github.com/poikilos/blendernightly](https://github.com/poikilos/blendernightly), "Clone or download," "Download ZIP"
* Open the downloaded file then Extract All, then view extracted files.

## Use
* Make sure you are connected to the internet
* Double-click update.pyw (on Windows, open With: "C:\Python??\pythonw.exe")
* The program should open a small square Window, and immediately show buttons for download links matching your platform (if the version, OS Name, and architecture flags are incorrect, you can correct them then click "Refresh")
* Click "Install" button to download & install the version you want to install. The "Blender 2.80" (or with other version number) desktop icon will be created or updated to that version (old versions will remain in Downloads/blendernightly/versions in your user profile).
* To see more versions: leave any/all entry boxes blank then hit Refresh.
* Advanced use: Set entry boxes as shown below, then hit Refresh.
  * Blender version (`2.79` or `2.80`)
  * operating system (`win32`, `win64`, `linux`, or `OSX`)
  * architecture (`win64`, `win32`, `x86_64` *[OSX or Linux]*, `i686` *[32-bit Linux]*)

## Known Issues
* hangs on start on older versions of Python on Windows (Python 3.2.5, Python 2.7.10)
* macOS icon support added but not tested

## Developer Notes

### poikilos work log
(2018-12-12)
* ~8hrs code in "initial commit" (actually 2nd, but first with code)
(2018-12-13)
* ~9.5hrs "first working version" commit
* ~1.5hrs test and fix on Windows
