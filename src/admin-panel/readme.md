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
- **Sound** - a soundboard that plays into the game alongside your voice, and voice-activated push-to-talk
- **Actions** - keyboard shortcuts (recorded by pressing them), OS commands and Python scripts for controls to run
- **Activity** - every press, action, error and connection change
- **Integrations** - turn whole kinds of action on or off
- **Settings** - box connection, start with Windows, backup and restore, and the log

The button box's IP is found automatically - it's learned from the box's button presses, and the panel scans your network for the box when it can't reach it.

Requires Python 3 on Windows (the keyboard integration uses PyDirectInput), and Node.js to build the web UI.

## Joystick

Like Joystick Gremlin, the panel can give a joystick's hat and buttons new jobs while a configuration is active:

- **Hold keys** - holds keys for as long as the input is held, e.g. arrow keys for snap views
- **Run action** - runs any action when pressed or released

The **Buttons to keys** card is the quick way to give buttons keyboard keys: click a button's slot and press a key (or a combination like Ctrl+F). Buttons left on "In game" go straight to the game to bind there. The game still sees the buttons you give keys, so leave those unbound in game.

Joysticks are read through Windows' built-in joystick API, so no drivers (like vJoy) are needed. Mappings belong to a configuration, so they only apply while it's active, and the whole thing can be turned off on the Integrations page.

## Sound

The Sound page puts the panel between your microphone and the game:

```
mic ──► panel ──┬──► virtual cable ══► the game's microphone
sounds ─────────┘
           └──────► your headphones (sounds only, so you hear them too)
```

- **Soundboard** - drop in WAV, MP3, M4A, OGG or FLAC files (M4A and AAC are converted to FLAC when added) and click to play them. Each sound is also an action, so box and joystick buttons can play them, and there's a "Stop all sounds" action. Pressing a sound again can restart it, stop it or play another copy over it. Files are kept in `app/sounds/` (not included in backups)
- **Voice activation** - talk in game without holding push-to-talk yourself, in one of two ways:
  - **Press a key** - holds the game's push-to-talk key (K for Wardogs, or any key) while you talk and/or while a sound plays. Your voice can be delayed slightly so the key is already down when your first word reaches the game, and the key can be limited to when the game is the app in front, so it isn't typed into Discord
  - **Mic gate** - presses nothing: your voice only goes through to the game while you're talking, and the game is set to open mic. For games where simulated key presses are a worry
  
  Talking is anything louder than a threshold set against a live mic meter.
- **Devices** - your mic, where to send it (the virtual cable) and where to hear sounds, with a volume for each. **Hear what the game hears** plays the cable's output in your headphones, to check what's getting through

Sending sound into games needs a virtual audio cable: install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) (free), restart the panel, choose **CABLE Input** as "Send to game" and set the game's microphone to **CABLE Output**. Push-to-talk's key mode works without it, using your mic directly; the mic gate needs it. Push-to-talk and joystick mappings share held keys, so a joystick button mapped to the same key won't let go of it while you're talking.

## Presets

`presets/wardogs.json` is a ready-made setup for Wardogs helicopter flying: box bindings for snap views, camera, countermeasures, weapons, seats, voice chat, free look lock and more. Load it from Settings > Restore from file. Restoring replaces your current setup, which is backed up first.

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
| `GET /api/events` | Server-sent events: `status`, `press`, `activity`, `configuration`, `learned`, `changed`, `joystick`, `sound` |
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
| `GET /api/sound`, `PATCH /api/sound/settings` | Sound devices, settings, sounds and live state (also sent as `sound` events: mic level, talking, key held, sounds playing) |
| `POST /api/sound/clips` (multipart `files`), `PATCH/DELETE /api/sound/clips/<id>` | Add, edit and remove sounds |
| `POST /api/sound/clips/<id>/play`, `POST /api/sound/stop` | Play (or stop) a sound, stop all sounds |
| `POST /api/sound/listen` | `listening`: play what the game hears (the cable's output) in your headphones, or stop |
| `GET /api/sound/apps` | Apps with a window open, for limiting push-to-talk to the game |
| `POST /api/box/find`, `POST /api/box/display` | Scan the network for the box, preview a message on its screen |
| `POST/GET /api/learn` | Learn mode - the next control used on the box is reported instead of running its actions |
| `GET /api/export`, `POST /api/import` | Back up everything / restore from a backup (saves a backup to `app/backups/` first) |
