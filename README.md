# Mouse Mover

A lightweight utility that nudges the cursor by a small randomized amount
at a configurable interval. It never clicks, types, scrolls, or interacts
with any application or presence indicator — it only moves the pointer.

Two versions are included:

| File | Platform | Description |
|---|---|---|
| `mouse_mover.py` | **macOS + Windows** | Command-line version with an interactive `start/pause/resume/stop/quit` prompt. |
| `mouse_mover_menubar.py` | **macOS only** | Menu-bar dropdown version (uses `rumps`, a macOS-only library). |

If you need this to run on both a Mac and a Windows machine, use
`mouse_mover.py` on both — the menu-bar version has no Windows equivalent.

## 1. Requirements

See `requirements.txt`:

```
pyautogui>=0.9.54
rumps>=0.4.0; sys_platform == "darwin"
```

`rumps` is marked macOS-only, so `pip install -r requirements.txt` works
unmodified on both platforms — it's simply skipped on Windows.

## 2. Installation

### macOS

```bash
cd /path/to/presentsir
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Accessibility permission (macOS only):** `pyautogui` moves the cursor via
macOS Accessibility APIs. The first time you run either script, macOS will
prompt you to grant **Accessibility** access to your terminal app (or to
`python3` itself). Grant it via:

**System Settings → Privacy & Security → Accessibility** → enable your
terminal app (Terminal, iTerm2, VS Code, etc.).

If you don't see a prompt and the cursor doesn't move, add the app
manually in that same Accessibility list and restart the terminal.

### Windows

```powershell
cd C:\path\to\presentsir
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No permission prompt is needed on Windows — cursor control works as soon
as the package is installed.

## 3. Running the CLI version (`mouse_mover.py`)

**macOS**
```bash
source .venv/bin/activate
python3 mouse_mover.py
```

**Windows**
```powershell
.venv\Scripts\activate
python mouse_mover.py
```

Either way, this opens an interactive prompt:

```
Mouse Mover

Commands:
  start   - Start moving the mouse
  pause   - Pause movement (program keeps running)
  resume  - Resume movement after a pause
  stop    - Stop movement (thread ends, can 'start' again)
  status  - Show current state
  help    - Show this message
  quit    - Stop movement and exit the program

mouse-mover> start
[mouse-mover] started (interval=60s, max_px=15)
```

Type `pause`, `resume`, `stop`, or `quit` at any time. `Ctrl+C` is handled
gracefully on both platforms — it stops the movement thread and exits
cleanly.

### Configuration

Edit the constants at the top of `mouse_mover.py` (same on both platforms):

```python
INTERVAL_SECONDS = 60       # time between movements
MAX_MOVEMENT_PIXELS = 15    # max +/- pixels per movement (X and Y)
```

Each movement:

1. Moves the cursor by a random `dx, dy` in `[-MAX_MOVEMENT_PIXELS, +MAX_MOVEMENT_PIXELS]`.
2. Clamps the result so the cursor never leaves the visible screen bounds.
3. Waits a random 0.2–1.0 seconds, then makes a smaller optional follow-up
   move (up to ±5 px) for a more natural-looking pattern.

## 4. Background execution (CLI version)

When launched with no interactive terminal/console attached, the script
detects there's no stdin to read commands from and **starts moving
immediately**, running until it's terminated. Both platforms rely on this
same auto-start behavior — only the launch/stop commands differ.

### macOS

Run it detached from the terminal with `nohup`:

```bash
nohup python3 mouse_mover.py >/dev/null 2>&1 &
```

Or with the venv's interpreter explicitly:

```bash
nohup /path/to/.venv/bin/python3 mouse_mover.py >/dev/null 2>&1 &
```

**Find it:**
```bash
ps aux | grep mouse_mover.py | grep -v grep
```
This prints a line with the process ID (PID) in the second column, e.g.:
```
yuvraj  12345  0.0  0.1  ...  python3 mouse_mover.py
```

**Stop it** (graceful shutdown, equivalent to `Ctrl+C`, runs cleanup):
```bash
kill -SIGINT 12345
# or
kill -SIGTERM 12345
# or, without noting the PID first
pkill -SIGINT -f mouse_mover.py
```
Avoid `kill -9` (SIGKILL) — it skips the cleanup handler.

### Windows

Run it with no visible console window using `pythonw` (the windowless
Python interpreter that ships alongside `python.exe`):

```powershell
Start-Process -FilePath ".venv\Scripts\pythonw.exe" -ArgumentList "mouse_mover.py"
```

Or keep a console window but run it detached:

```powershell
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "mouse_mover.py" -WindowStyle Hidden
```

**Find it:**
```powershell
Get-Process | Where-Object { $_.Path -like "*presentsir*" }
```
or check Task Manager for `python.exe` / `pythonw.exe`.

**Stop it** (graceful shutdown via Ctrl+C signal):
```powershell
Stop-Process -Id <PID>
```
or select it in Task Manager and choose **End Task**.

## 5. Menu-bar version (macOS only)

The menu-bar version gives you the same behavior with a GUI dropdown
instead of a terminal prompt. It only works on macOS.

```bash
source .venv/bin/activate
python3 mouse_mover_menubar.py
```

Menu layout:

```
🟢 / ⚪️ Mouse Mover           <- menu-bar icon, changes with state
────────────
Status: Active / Paused
Start / Pause                 <- toggles
────────────
Interval: 30 sec
Interval: 1 min
Interval: 2 min
────────────
Quit
```

- The menu-bar icon shows a green dot (🟢) while movement is active and a
  white dot (⚪️) while paused, so you can tell the state at a glance.
- Selecting an interval option puts a checkmark next to it and applies
  immediately (restarting the timer if movement is currently active).
- `Quit` stops the timer and exits the app cleanly.

To run it in the background as a standalone app-like process:

```bash
nohup python3 mouse_mover_menubar.py >/dev/null 2>&1 &
```

Find/stop it the same way as the CLI version:

```bash
ps aux | grep mouse_mover_menubar.py | grep -v grep
kill -SIGTERM <PID>
```

## 6. Safety notes

- Neither script clicks, types, scrolls, or targets any specific
  application, window, or presence indicator (Teams, Slack, etc.).
- Movement is always clamped to stay within the current screen's visible
  bounds (via `pyautogui.size()`).
- `pyautogui.FAILSAFE` stays enabled: if you manually drag the cursor into
  a screen corner, pyautogui raises a `FailSafeException`, which both
  scripts catch quietly and simply skip that movement cycle.
