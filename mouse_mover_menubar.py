#!/usr/bin/env python3
"""
Mouse Mover - macOS menu-bar utility.

Moves the cursor by a small random amount at a configurable interval,
controlled entirely from a menu-bar dropdown. Requires the 'rumps' package
(macOS only). Does not click, type, scroll, or interact with any application.
"""

import random
import threading

import pyautogui
import rumps

MAX_MOVEMENT_PIXELS = 15
MOVE_DURATION = 0.2

INTERVAL_OPTIONS = [
    ("Interval: 30 sec", 30),
    ("Interval: 1 min", 60),
    ("Interval: 2 min", 120),
]

ICON_ACTIVE = "\U0001F7E2"   # green circle
ICON_PAUSED = "⚪️"  # white circle

pyautogui.FAILSAFE = True


class MouseMoverApp(rumps.App):
    def __init__(self):
        super().__init__(name="Mouse Mover", title=f"{ICON_PAUSED} Mouse Mover", quit_button=None)
        self.interval = 60
        self.active = False
        self._lock = threading.Lock()

        self.status_item = rumps.MenuItem("Status: Paused")
        self.toggle_item = rumps.MenuItem("Start", callback=self.toggle_active)

        self.interval_items = {}
        interval_menu = []
        for label, seconds in INTERVAL_OPTIONS:
            item = rumps.MenuItem(label, callback=self.set_interval)
            item.seconds = seconds
            item.state = 1 if seconds == self.interval else 0
            self.interval_items[label] = item
            interval_menu.append(item)

        self.menu = [
            self.status_item,
            None,
            self.toggle_item,
            None,
            *interval_menu,
            None,
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]

        self.timer = rumps.Timer(self.tick, self.interval)

    # ---- menu callbacks -------------------------------------------------
    def toggle_active(self, sender):
        with self._lock:
            self.active = not self.active
            if self.active:
                self.timer.interval = self.interval
                self.timer.start()
                sender.title = "Pause"
                self.status_item.title = "Status: Active"
                self.title = f"{ICON_ACTIVE} Mouse Mover"
            else:
                self.timer.stop()
                sender.title = "Start"
                self.status_item.title = "Status: Paused"
                self.title = f"{ICON_PAUSED} Mouse Mover"

    def set_interval(self, sender):
        for item in self.interval_items.values():
            item.state = 0
        sender.state = 1
        self.interval = sender.seconds
        if self.active:
            self.timer.stop()
            self.timer.interval = self.interval
            self.timer.start()

    def quit_app(self, _sender):
        self.timer.stop()
        rumps.quit_application()

    # ---- movement ---------------------------------------------------------
    def tick(self, _timer):
        try:
            self._move_once()
        except pyautogui.FailSafeException:
            pass

    @staticmethod
    def _clamped(x, y, dx, dy):
        screen_w, screen_h = pyautogui.size()
        new_x = min(max(x + dx, 0), screen_w - 1)
        new_y = min(max(y + dy, 0), screen_h - 1)
        return new_x, new_y

    def _move_once(self):
        x, y = pyautogui.position()
        dx = random.randint(-MAX_MOVEMENT_PIXELS, MAX_MOVEMENT_PIXELS)
        dy = random.randint(-MAX_MOVEMENT_PIXELS, MAX_MOVEMENT_PIXELS)
        new_x, new_y = self._clamped(x, y, dx, dy)
        pyautogui.moveTo(new_x, new_y, duration=MOVE_DURATION)


if __name__ == "__main__":
    MouseMoverApp().run()
