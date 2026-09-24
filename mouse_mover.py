#!/usr/bin/env python3
"""
Mouse Mover - keeps the cursor gently moving at randomized intervals.

Runs on macOS (Apple Silicon compatible). Uses pyautogui for cursor
control. Does not click, type, scroll, or interact with any application.
"""

import random
import signal
import sys
import threading
import time

import pyautogui

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
INTERVAL_SECONDS = 60             # time between primary movements
MAX_MOVEMENT_PIXELS = 15          # max +/- pixels for the primary movement
SECONDARY_MOVE_MIN_DELAY = 0.2    # seconds before the optional follow-up move
SECONDARY_MOVE_MAX_DELAY = 1.0    # seconds before the optional follow-up move
SECONDARY_MOVE_MAX_PIXELS = 5     # smaller follow-up movement
MOVE_DURATION = 0.2               # seconds pyautogui takes to glide the cursor

pyautogui.FAILSAFE = True  # keep pyautogui's corner-abort safety on


class MouseMover:
    def __init__(self, interval=INTERVAL_SECONDS, max_pixels=MAX_MOVEMENT_PIXELS):
        self.interval = interval
        self.max_pixels = max_pixels

        self._thread = None
        self._running = threading.Event()  # set = actively moving, clear = paused
        self._stop = threading.Event()      # set = terminate the loop entirely
        self._lock = threading.Lock()
        self.state = "idle"  # idle -> running -> paused -> stopped

    # ---- movement -----------------------------------------------------
    @staticmethod
    def _clamped(x, y, dx, dy):
        screen_w, screen_h = pyautogui.size()
        new_x = min(max(x + dx, 0), screen_w - 1)
        new_y = min(max(y + dy, 0), screen_h - 1)
        return new_x, new_y

    def _move_once(self):
        x, y = pyautogui.position()
        dx = random.randint(-self.max_pixels, self.max_pixels)
        dy = random.randint(-self.max_pixels, self.max_pixels)
        new_x, new_y = self._clamped(x, y, dx, dy)
        pyautogui.moveTo(new_x, new_y, duration=MOVE_DURATION)

        # optional small follow-up movement for a more natural pattern
        time.sleep(random.uniform(SECONDARY_MOVE_MIN_DELAY, SECONDARY_MOVE_MAX_DELAY))
        if self._stop.is_set() or not self._running.is_set():
            return
        x, y = pyautogui.position()
        dx2 = random.randint(-SECONDARY_MOVE_MAX_PIXELS, SECONDARY_MOVE_MAX_PIXELS)
        dy2 = random.randint(-SECONDARY_MOVE_MAX_PIXELS, SECONDARY_MOVE_MAX_PIXELS)
        new_x2, new_y2 = self._clamped(x, y, dx2, dy2)
        pyautogui.moveTo(new_x2, new_y2, duration=MOVE_DURATION)

    def _wait_interval(self):
        # sleep in small slices so pause/stop react quickly
        remaining = self.interval
        slice_len = 0.25
        while remaining > 0 and not self._stop.is_set() and self._running.is_set():
            time.sleep(min(slice_len, remaining))
            remaining -= slice_len

    def _loop(self):
        while not self._stop.is_set():
            if not self._running.wait(timeout=0.25):
                continue
            if self._stop.is_set():
                break
            try:
                self._move_once()
            except pyautogui.FailSafeException:
                # user yanked the mouse to a screen corner; back off quietly
                pass
            self._wait_interval()

    # ---- controls -------------------------------------------------------
    def start(self):
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._stop.clear()
                self._thread = threading.Thread(target=self._loop, daemon=True)
                self._thread.start()
            self._running.set()
            self.state = "running"
        print(f"[mouse-mover] started (interval={self.interval}s, max_px={self.max_pixels})")

    def pause(self):
        with self._lock:
            if self.state == "running":
                self._running.clear()
                self.state = "paused"
                print("[mouse-mover] paused")
            else:
                print("[mouse-mover] not running, nothing to pause")

    def resume(self):
        with self._lock:
            if self.state == "paused":
                self._running.set()
                self.state = "running"
                print("[mouse-mover] resumed")
            else:
                print("[mouse-mover] not paused, use 'start' instead")

    def stop(self):
        with self._lock:
            self._running.clear()
            self._stop.set()
            self.state = "stopped"
        if self._thread is not None:
            self._thread.join(timeout=2)
        print("[mouse-mover] stopped")

    def quit(self):
        self.stop()


HELP_TEXT = """
Commands:
  start   - Start moving the mouse
  pause   - Pause movement (program keeps running)
  resume  - Resume movement after a pause
  stop    - Stop movement (thread ends, can 'start' again)
  status  - Show current state
  help    - Show this message
  quit    - Stop movement and exit the program
"""


def run_interactive(mover):
    print("Mouse Mover")
    print(HELP_TEXT)
    while True:
        try:
            cmd = input("mouse-mover> ").strip().lower()
        except EOFError:
            break

        if cmd == "start":
            mover.start()
        elif cmd == "pause":
            mover.pause()
        elif cmd == "resume":
            mover.resume()
        elif cmd == "stop":
            mover.stop()
        elif cmd == "status":
            print(f"[mouse-mover] state={mover.state}")
        elif cmd in ("help", "?"):
            print(HELP_TEXT)
        elif cmd in ("quit", "exit", "q"):
            mover.quit()
            break
        elif cmd == "":
            continue
        else:
            print(f"Unknown command: {cmd!r}. Type 'help' for options.")


def run_headless(mover):
    # No interactive stdin (e.g. launched via nohup ... &): start immediately
    # and idle until a signal terminates the process.
    mover.start()
    while True:
        time.sleep(3600)


def main():
    mover = MouseMover()

    def handle_sigint(signum, frame):
        print("\n[mouse-mover] received Ctrl+C, shutting down...")
        mover.quit()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    if sys.stdin.isatty():
        run_interactive(mover)
    else:
        run_headless(mover)


if __name__ == "__main__":
    main()
