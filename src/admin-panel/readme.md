# Admin Panel

## Running

Double-click `start.bat` (or the desktop shortcut). On first run it creates a virtual environment in `.venv` and installs `requirements.txt`; dependencies are reinstalled automatically whenever `requirements.txt` changes.

The panel then runs in the background with an icon in the system tray, and opens in Chrome (or your default browser) at http://localhost. Running `start.bat` again while it's already running just reopens the panel.

Tray menu:
- **Open panel** (or double-click the icon)
- **Start with Windows** - starts the panel in the tray when you log in, without opening the browser (also in Settings)
- **Open log** - output is written to `admin-panel.log`
- **Quit**

In the panel:
- **Panel** - a live view of the box. Click a control (or use it on the box with "Pick from the box") to see and change its bindings. The **Joystick** tab does the same for a joystick plugged into this PC
- **Configurations** - sets of bindings to switch between, each with an optional custom LCD screen
- **Actions** - keyboard shortcuts (recorded by pressing them), OS commands and Python scripts for controls to run
- **Activity** - every press, action, error and connection change
- **Integrations** - turn whole kinds of action on or off
- **Settings** - box connection, start with Windows, backup and restore, and the log

The button box's IP is found automatically - it's learned from the box's button presses, and the panel scans your network for the box when it can't reach it.

Requires Python 3 on Windows (the keyboard integration uses PyDirectInput), and Node.js to build the web UI.

## Joystick

Like Joystick Gremlin, the panel can give a joystick's hat and buttons new jobs while a configuration is active:

- **Look around** - moves the mouse while held, optionally holding a key like Alt (Wardogs' free look) so the view recentres when you let go. Speed, ramp-up, a stop distance and return-to-start are adjustable
- **Hold keys** - holds keys for as long as the input is held, e.g. arrow keys for snap views
- **Run action** - runs any action when pressed or released

Joysticks are read through Windows' built-in joystick API, so no drivers (like vJoy) are needed. Mappings belong to a configuration, so they only apply while it's active, and the whole thing can be turned off on the Integrations page.

## Presets

`presets/wardogs.json` is a ready-made setup for Wardogs helicopter flying: box bindings for snap views, camera, countermeasures, weapons, seats, voice chat, free look lock and more, plus free look on the joystick hat. Load it from Settings > Restore from file. Restoring replaces your current setup, which is backed up first.

## Web UI

The UI is a React app in `web/` (Vite, TypeScript, Tailwind and shadcn/ui), built into `app/static/web` and served by Flask. `start.bat` rebuilds it automatically when anything in `web/` has changed.

To work on it with hot reload, keep the panel running and start the dev server, which forwards API calls to it:

```
cd web
npm run dev
```

Then open http://localhost:5173/static/web/.

## Bindings

A binding maps a control on the box (`BTN_1`-`BTN_10`, `SWITCH_1`-`SWITCH_5`, `PROTECTED_1`-`PROTECTED_4`) turning `on` or `off` to an action. Bindings can have **modifiers** - other controls that must be on at the time. When several bindings match, only the ones with the most modifiers run, so flipping a switch can give buttons a second layer of actions. Several bindings on the same trigger all run, in order.

## JSON API

Used by the web UI. JSON with camelCase keys; errors return an HTTP error status with `{"error": "..."}`.

| | |
|---|---|
| `GET /api/status` | Box connection, active configuration, control states, current screen |
| `GET /api/controls` | The box's controls and where they sit on the panel |
| `GET /api/events` | Server-sent events: `status`, `press`, `activity`, `configuration`, `learned`, `changed` |
| `GET/POST /api/configurations` | List / create configurations |
| `GET/PATCH/DELETE /api/configurations/<id>` | A configuration with its bindings, edit (incl. custom `displayLines`), delete |
| `POST /api/configurations/<id>/activate` and `/duplicate` | Switch to / copy a configuration |
| `POST /api/configurations/<id>/bindings` | Add a binding: `control`, `event`, `actionId`, optional `name`, `modifiers`, `enabled` |
| `PATCH/DELETE /api/bindings/<id>` | Edit / remove a binding |
| `GET /api/integrations`, `PATCH /api/integrations/<id>` | List integrations (with action editor options), turn on/off |
| `GET/POST /api/actions`, `GET/PATCH/DELETE /api/actions/<id>` | Manage actions (configuration is validated per integration) |
| `POST /api/actions/<id>/test` | Run an action now |
| `GET/DELETE /api/activity` | Activity log (`limit`, `before`, `kind`), clear it |
| `GET/PATCH /api/settings` | Settings (`buttonBoxIp`, `startWithWindows`) |
| `POST /api/system/open-log` | Open the log file on this PC |
| `GET /api/joystick` | Connected joysticks and their live state (also sent as `joystick` events) |
| `POST /api/configurations/<id>/joystick-mappings`, `PATCH/DELETE /api/joystick-mappings/<id>` | Manage a configuration's joystick mappings |
| `POST /api/box/find`, `POST /api/box/display` | Scan the network for the box, preview a message on its screen |
| `POST/GET /api/learn` | Learn mode - the next control used on the box is reported instead of running its actions |
| `GET /api/export`, `POST /api/import` | Back up everything / restore from a backup (saves a backup to `app/backups/` first) |
