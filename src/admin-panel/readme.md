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

Requires Python 3 on Windows (the keyboard integration uses PyDirectInput), and Node.js to build the web UI.

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
| `GET/PATCH /api/settings` | Settings (`buttonBoxIp`) |
| `POST /api/box/find`, `POST /api/box/display` | Scan the network for the box, preview a message on its screen |
| `POST/GET /api/learn` | Learn mode - the next control used on the box is reported instead of running its actions |
| `GET /api/export`, `POST /api/import` | Back up everything / restore from a backup (saves a backup to `app/backups/` first) |

## Credits

Admin Dashboard Template: https://github.com/pro-dev-ph/bootstrap-simple-admin-template
