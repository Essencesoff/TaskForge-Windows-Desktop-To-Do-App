# TaskForge — Windows Desktop To-Do App

A real, offline-first Windows desktop productivity app built with **Python + PySide6 (Qt)**
and a local **SQLite** database. No browser, no server, no account, no internet required.

---

## 1. Requirements

- Windows 10 or 11, 64-bit
- Python 3.10–3.12 (from [python.org](https://www.python.org/downloads/) — check
  "Add python.exe to PATH" during install)

## 2. Installation

Open **Command Prompt** in the project folder and run:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Running in development mode

With the virtual environment active:

```bat
python -m app.main
```

The app window should open directly — dashboard, sidebar navigation, everything live
against a local SQLite database.

## 4. Building the `.exe`

Just run the provided build script from the project root:

```bat
build.bat
```

This will:
1. Create/reuse a `venv` virtual environment
2. Install all dependencies (including PyInstaller)
3. Package the app into `dist\ToDoApp\ToDoApp.exe`

To run it: open `dist\ToDoApp\` and double-click `ToDoApp.exe`. You can copy that whole
folder to any Windows 10/11 64-bit PC and run it there — no Python installation needed
on the target machine.

> If you'd rather have a single `.exe` file (slower startup, but one file to share),
> edit `build.bat` and add `--onefile` to the `pyinstaller` line.

## 5. Where the database is stored

TaskForge stores its data in your per-user AppData folder, **never next to the .exe**
(so it won't hit permission problems and survives app updates/reinstalls):

```
%APPDATA%\TaskForge\taskforge.db
```

Log file (for troubleshooting unexpected errors):

```
%APPDATA%\TaskForge\app.log
```

## 6. How backups work

- **Settings → Data → Create Backup** copies the current database into
  `%APPDATA%\TaskForge\backups\backup_<timestamp>.db`. The 10 most recent backups are
  kept automatically.
- **Settings → Data → Restore Latest Backup** replaces the live database with the most
  recent backup (a confirmation is required first).
- **Export JSON / Export CSV** let you save a portable copy of your tasks anywhere you
  choose (USB drive, cloud folder, etc.) — separate from the automatic backup system.
- **Import JSON** merges a previously exported JSON file back in (existing data is kept;
  matching categories are merged by name).

## 7. How to reset the application

Two options:

- **Soft reset (keep the app installed):** Settings → Data → **Clear All Data**. This
  wipes tasks, goals, habits and stats but keeps your settings and categories.
- **Full reset:** close the app and delete the whole `%APPDATA%\TaskForge` folder. The
  next launch recreates a fresh database with the default categories.

## 8. Keyboard shortcuts

| Shortcut   | Action                       |
|------------|-------------------------------|
| `Ctrl+N`   | Quick-add a new task          |
| `Ctrl+F`   | Jump to Tasks and focus search|
| `Ctrl+K`   | Quick-add (command menu)      |
| `Ctrl+,`   | Open Settings                 |
| `Ctrl+Z`   | Undo the last delete/complete |
| `Esc`      | Close the current dialog      |
| `Enter`    | Confirm a dialog / quick-add  |

(Also viewable in-app under **Shortcuts** in the sidebar.)

## 9. Troubleshooting

**The app won't start / crashes immediately**
Check `%APPDATA%\TaskForge\app.log` for the error. Most issues are a corrupted database —
try Settings → Data → Restore Latest Backup, or rename/delete `taskforge.db` to let the
app recreate an empty one (you'll need to re-import from a JSON export or backup).

**Notifications aren't showing**
Make sure Windows notifications are allowed for the app in
*Settings → System → Notifications*, and that **Settings → Notifications → Enable
notifications** is turned on inside TaskForge itself. Reminders are only checked while
the app process is running (it can be minimized to the system tray — it doesn't need to
be visible).

**`pip install` fails on PySide6**
Make sure you're on 64-bit Python 3.10–3.12 and that `pip` itself is up to date
(`python -m pip install --upgrade pip`).

**Antivirus flags the built .exe**
This is common with freshly PyInstaller-built executables that aren't code-signed. It's
a false positive from the packaging pattern, not the app's behavior — you can inspect
the source in `app/` yourself since nothing here calls out to the network.

**I want the app to launch automatically on startup**
Toggle **Settings → Windows Integration → Launch on Windows startup**. This writes a
registry entry under `HKEY_CURRENT_USER\...\Run` — no admin rights needed, and toggling
it off removes the entry again.

---

## Project structure

```
app/
├── main.py              # entry point
├── database/             # SQLite connection + schema
├── models/                # plain dataclasses (Task, Category, Goal, Subtask)
├── services/               # business logic: tasks, categories, goals, stats,
│                            # smart planner, reminders, backups, settings
├── ui/                    # pages: dashboard, tasks, calendar, statistics,
│                            # goals, pomodoro, planner, categories, trash,
│                            # shortcuts, settings, main_window (shell/nav/tray)
├── widgets/                # reusable widgets: task card, bar chart
├── dialogs/                 # task editor, quick add, category/goal editors
├── utils/                  # theming (QSS), small helpers
├── config/                # constants, default categories, data-dir resolution
└── tests/                # smoke tests (see below)
```

## Notes on scope

This is a complete, working local application: every button performs its real action
against the SQLite database (no placeholders). A few pragmatic choices worth knowing
about since they affect how "premium" certain visuals are:

- Charts (Statistics page) are drawn with a small dependency-free `QPainter` bar chart
  rather than a third-party charting library, to keep the dependency footprint (and
  build size) small. It's fully functional, just intentionally minimal.
- The Smart Planner is a transparent local heuristic (priority + deadline proximity +
  estimated duration), not a machine-learning model — this matches the "must work
  locally, no external API" requirement exactly.
- The system tray keeps the process (and therefore reminders) alive when the window is
  closed; use **Quit** from the tray icon's right-click menu to actually exit.
  
