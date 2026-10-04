# Admin Panel

## Running

Double-click `start.bat` (or the desktop shortcut). On first run it creates a virtual environment in `.venv` and installs `requirements.txt`; dependencies are reinstalled automatically whenever `requirements.txt` changes.

The panel then runs in the background with an icon in the system tray, and opens in Chrome (or your default browser) at http://localhost. Running `start.bat` again while it's already running just reopens the panel.

Tray menu:
- **Open panel** (or double-click the icon)
- **Start with Windows** - starts the panel in the tray when you log in, without opening the browser
- **Open log** - output is written to `admin-panel.log`
- **Quit**

The button box's IP is found automatically - it's learned from the box's button presses, and the panel scans your network for the box when it can't reach it.

Requires Python 3 on Windows (the keyboard integration uses PyDirectInput).

## Credits

Admin Dashboard Template: https://github.com/pro-dev-ph/bootstrap-simple-admin-template
