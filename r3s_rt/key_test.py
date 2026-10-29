"""Finite foreground key-event checks; no hooks, USB access, or raw sensor reads."""

from __future__ import annotations

from datetime import datetime, timezone
import math
import time

from .storage import Storage

KEYSYMS = {
    "w": "W", "a": "A", "s": "S", "d": "D", "q": "Q", "e": "E",
    "shift_l": "LeftShift", "space": "Space",
}


class KeyEventSession:
    """Deduplicate OS auto-repeat and retain incomplete-event evidence."""

    def __init__(self, clock=time.monotonic, duration: float = 20.0):
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("The event-check duration must be positive and finite.")
        self.clock = clock
        self.duration = duration
        self.started = None
        self.ended = None
        self.active = False
        self.held: set[str] = set()
        self.events: list[dict] = []
        self.issues: list[str] = []
        self.reason = "not started"

    def begin(self, already_down: bool = False) -> None:
        if self.active:
            raise ValueError("A key check is already running.")
        if already_down:
            raise ValueError("Release all eight target keys before starting.")
        self.started = self.clock()
        self.ended = None
        self.active = True
        self.held.clear()
        self.events.clear()
        self.issues.clear()
        self.reason = "running"

    def event(self, kind: str, keysym: str) -> bool:
        if kind not in ("down", "up"):
            raise ValueError("The event kind must be 'down' or 'up'.")
        if not self.active:
            return False
        if self.clock() - self.started >= self.duration:
            self.finish("time limit")
            return False
        key = KEYSYMS.get(keysym.lower())
        if key is None:
            return False
        if kind == "down":
            if key in self.held:
                return False
            self.held.add(key)
        else:
            if key not in self.held:
                self.issues.append(f"{key}: release without an observed press.")
                return False
            self.held.remove(key)
        self.events.append({"key": key, "event": kind,
                            "elapsed_ms": round((self.clock() - self.started) * 1000, 3)})
        return True

    def finish(self, reason: str = "user stop") -> dict:
        if self.active:
            self.ended = self.clock()
            self.active = False
            self.reason = reason
            if reason == "focus lost":
                self.issues.append("The check window lost focus; later events were not recorded.")
            if self.held:
                self.issues.append("Keys held at the end: " + ", ".join(sorted(self.held)) + ".")
        return self.snapshot()

    def snapshot(self) -> dict:
        return {
            "schema": "r3s-rt-foreground-events-v1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "reason": self.reason,
            "duration_limit_seconds": self.duration,
            "elapsed_seconds": None if self.started is None else round(
                ((self.ended if self.ended is not None else self.clock()) - self.started), 3),
            "events": list(self.events),
            "held_keys": sorted(self.held),
            "issues": list(self.issues),
            "raw_measurement": False,
            "device_identified": False,
        }


def target_keys_held() -> bool:
    """Check existing Windows key state without opening a keyboard device."""
    import sys
    if sys.platform != "win32":
        return False
    import ctypes
    codes = [ord(char) for char in "WASDQE"] + [0xA0, 0x20]
    return any(ctypes.windll.user32.GetAsyncKeyState(code) & 0x8000 for code in codes)


class KeyTestWindow:
    def __init__(self, parent: tk.Misc, storage: Storage | None = None):
        import tkinter as tk
        from tkinter import ttk

        self.window = tk.Toplevel(parent)
        self.window.title("R3S RT — Foreground key check")
        self.window.geometry("720x530")
        self.window.minsize(620, 460)
        self.storage = storage or Storage()
        self.session = KeyEventSession()
        self.saved = True
        self.timer = None
        frame = ttk.Frame(self.window, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Check W / A / S / D / Q / E / Left Shift / Space",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Release all eight keys, start, then press, lift slightly, and press again.\n"
                  "Keep this window focused. The check stops after 20 seconds and saves automatically.\n"
                  "OS events can come from any keyboard. This does not measure raw travel or prove RT.",
                  wraplength=670).pack(anchor="w", pady=12)
        actions = ttk.Frame(frame)
        actions.pack(anchor="w", pady=8)
        self.start_button = ttk.Button(actions, text="Start 20-second check", command=self.begin)
        self.start_button.pack(side="left")
        ttk.Button(actions, text="Stop and save", command=lambda: self.finish("user stop")).pack(
            side="left", padx=8)
        self.status = tk.StringVar(value="Ready. No events are recorded until you start.")
        ttk.Label(frame, textvariable=self.status, wraplength=670).pack(anchor="w", pady=8)
        self.log = tk.Text(frame, height=13, state="disabled", wrap="none")
        self.log.pack(fill="both", expand=True)
        self.window.bind("<KeyPress>", lambda event: self.key("down", event))
        self.window.bind("<KeyRelease>", lambda event: self.key("up", event))
        self.window.bind("<FocusOut>", lambda _: self.window.after_idle(self.check_focus))
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.tick()

    def begin(self):
        try:
            self.session.begin(target_keys_held())
        except ValueError as error:
            self.status.set(str(error))
            return
        self.saved = False
        self.start_button.configure(state="disabled")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.status.set("Recording foreground OS events for up to 20 seconds.")
        self.window.focus_set()

    def key(self, kind, event):
        if self.session.event(kind, event.keysym):
            item = self.session.events[-1]
            self.log.configure(state="normal")
            self.log.insert("end", f"{item['elapsed_ms']:9.1f} ms   {item['key']:<10} {kind}\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        if self.session.started is not None and not self.session.active and not self.saved:
            self.finish(self.session.reason)

    def finish(self, reason):
        if self.session.started is None or self.saved:
            return
        record = self.session.finish(reason)
        try:
            path = self.storage.save_key_test(record)
        except (OSError, ValueError) as error:
            self.status.set(f"Could not save: {error}. Use Stop and save to retry.")
            return
        self.saved = True
        self.start_button.configure(state="normal")
        suffix = " Incomplete events were detected; review the JSON record." if record["issues"] else ""
        self.status.set(f"Saved {len(record['events'])} events to {path}.{suffix}")

    def check_focus(self):
        if not self.window.winfo_exists():
            return
        widget = self.window.focus_get()
        if self.session.active and (widget is None or widget.winfo_toplevel() != self.window):
            self.finish("focus lost")

    def tick(self):
        if self.session.active and self.session.clock() - self.session.started >= self.session.duration:
            self.finish("time limit")
        self.timer = self.window.after(100, self.tick)

    def close(self):
        self.finish("window close")
        if not self.saved:
            return
        if self.timer is not None:
            self.window.after_cancel(self.timer)
        self.window.destroy()
