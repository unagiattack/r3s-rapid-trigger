"""English settings UI that generates files locally and never opens a USB device."""

from __future__ import annotations

import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import firmware
from .key_test import KeyTestWindow
from .profile import KEYS, Profile
from .storage import Storage

LEVELS = tuple(str(level) for level in range(1, 8))
DISPLAY_KEYS = {"LeftShift": "Left Shift", "Space": "Space"}


class SettingsApp:
    def __init__(self, window: tk.Tk, storage: Storage | None = None,
                 profile: Profile | None = None):
        self.window = window
        self.storage = storage or Storage()
        self.profile = profile or Profile.default()
        self.selected_key = "W"
        self.stock_path: Path | None = None
        self.stock_digest: str | None = None
        self.pending_output: Path | None = None
        self._syncing = False
        window.title("R3S Rapid Trigger — Settings")
        window.geometry("1080x780")
        window.minsize(880, 650)
        style = ttk.Style(window)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", padding=(9, 6))
        outer = ttk.Frame(window, padding=18)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)
        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(header, text="R3S Rapid Trigger", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="1. Select your original firmware   2. Adjust keys   3. Generate a firmware file").pack(
            anchor="w", pady=4)
        explanation = ttk.Label(header, text="File generation only. Settings take effect after you separately install the generated firmware.")
        explanation.pack(anchor="w", fill="x")
        explanation.bind("<Configure>", lambda event: explanation.configure(wraplength=max(200, event.width)))

        scroll = ttk.Frame(outer)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.columnconfigure(0, weight=1)
        scroll.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(scroll, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(scroll, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        content = ttk.Frame(self.canvas)
        panel = self.canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(panel, width=event.width))
        window.bind("<MouseWheel>", self.scroll)
        content.columnconfigure(1, weight=1)
        content.columnconfigure(2, weight=1)
        source = ttk.LabelFrame(content, text="Original firmware", padding=12)
        source.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        source.columnconfigure(1, weight=1)
        ttk.Button(source, text="Select original .rfb…", command=self.select_stock).grid(row=0, column=0, sticky="nw")
        self.source_text = tk.StringVar(value="No source selected. Requires the supported R3SC31 / A0.11 original firmware.")
        source_label = ttk.Label(source, textvariable=self.source_text, wraplength=600)
        source_label.grid(row=0, column=1, sticky="ew", padx=12)
        source_label.bind("<Configure>", lambda event: source_label.configure(wraplength=max(200, event.width)))

        presets = ttk.LabelFrame(content, text="Presets", padding=12)
        presets.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        self.preset_choice = ttk.Combobox(presets, state="readonly", width=23)
        self.preset_choice.pack(anchor="w", pady=(0, 8))
        self.preset_choice.bind("<<ComboboxSelected>>", self.choose_preset)
        self.preset_name = tk.StringVar(value="My game settings")
        ttk.Entry(presets, textvariable=self.preset_name, width=25).pack(anchor="w", pady=(0, 8))
        ttk.Button(presets, text="Save as new preset", command=self.save_preset).pack(anchor="w")
        ttk.Label(presets, text="Presets save settings only.\nPrevious presets are kept.", wraplength=200).pack(anchor="w", pady=8)
        ttk.Separator(presets).pack(fill="x", pady=8)
        ttk.Button(presets, text="Load settings JSON…", command=self.import_profile).pack(anchor="w", pady=4)
        ttk.Button(presets, text="Reset to all keys 1 / 1", command=self.reset_profile).pack(anchor="w", pady=4)
        ttk.Button(presets, text="Open foreground key check", command=self.open_key_test).pack(anchor="w", pady=4)
        ttk.Label(presets, text="Presets and key-check records are saved in your user data folder.",
                  wraplength=205).pack(anchor="w", pady=12)

        keyboard = ttk.LabelFrame(content, text="Select a key", padding=12)
        keyboard.grid(row=1, column=1, sticky="nsew", padx=(0, 12))
        grid = ttk.Frame(keyboard)
        grid.pack(anchor="n", pady=12)
        self.tiles: dict[str, tk.Button] = {}
        for key, row, column in (("Q", 0, 0), ("W", 0, 1), ("E", 0, 2),
                                 ("A", 1, 0), ("S", 1, 1), ("D", 1, 2),
                                 ("LeftShift", 2, 0), ("Space", 2, 1)):
            tile = tk.Button(grid, width=7, height=3, font=("Segoe UI", 10, "bold"),
                             relief="flat", command=lambda name=key: self.select_key(name))
            tile.grid(row=row, column=column, padx=3, pady=3)
            self.tiles[key] = tile
        self.key_summary = tk.StringVar()
        ttk.Label(keyboard, textvariable=self.key_summary, justify="left").pack(anchor="w", pady=8)

        editor = ttk.LabelFrame(content, text="Key settings", padding=12)
        editor.grid(row=1, column=2, sticky="nsew")
        self.key_title = tk.StringVar()
        ttk.Label(editor, textvariable=self.key_title, style="Heading.TLabel").pack(anchor="w")
        self.enabled = tk.BooleanVar()
        ttk.Checkbutton(editor, text="Enable rapid trigger", variable=self.enabled).pack(anchor="w", pady=12)
        self.release_level = tk.StringVar()
        self.press_level = tk.StringVar()
        self.level_widgets = []
        for title, description, variable in (
                ("Release level", "How far you lift to release an active key.", self.release_level),
                ("Re-press level", "How far you press again to reactivate it.", self.press_level)):
            ttk.Label(editor, text=title, style="Heading.TLabel").pack(anchor="w")
            ttk.Label(editor, text=description, wraplength=230).pack(anchor="w", pady=5)
            choice = ttk.Combobox(editor, textvariable=variable, state="readonly", values=LEVELS, width=15)
            choice.pack(anchor="w", pady=(0, 12))
            self.level_widgets.append(choice)
        ttk.Button(editor, text="Copy this key to all 8 keys", command=self.copy_to_all).pack(anchor="w", pady=4)
        ttk.Label(editor, text="1 = most sensitive; 7 = least sensitive.\nThese levels are not millimetres.\n\n"
                  "The first press uses the original actuation point. Later re-presses use these levels throughout the travel.\n\n"
                  "RT OFF uses the original actuation behavior. Near the released position, RT resets and re-arms after a stable rest.",
                  wraplength=250).pack(anchor="w", pady=8)
        for variable in (self.enabled, self.release_level, self.press_level):
            variable.trace_add("write", self.edit_key)

        footer = ttk.Frame(outer)
        footer.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure(1, weight=1)
        self.build_button = ttk.Button(footer, text="Generate firmware file…", command=self.generate, state="disabled")
        self.build_button.grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.status = tk.StringVar(value="Select the supported original firmware to begin. No device is connected by this app.")
        status_label = ttk.Label(footer, textvariable=self.status, wraplength=600)
        status_label.grid(row=0, column=1, sticky="ew", padx=12, pady=(0, 8))
        status_label.bind("<Configure>", lambda event: status_label.configure(wraplength=max(200, event.width)))
        self.output_text = tk.StringVar(value="No firmware has been generated for the current settings.")
        ttk.Entry(footer, textvariable=self.output_text, state="readonly").grid(row=1, column=0, columnspan=2, sticky="ew")
        self.copy_button = ttk.Button(footer, text="Copy generated file path", command=self.copy_output, state="disabled")
        self.copy_button.grid(row=2, column=0, sticky="w", pady=8)
        ttk.Label(footer, text="This app never flashes firmware or changes a connected keyboard.",
                  wraplength=750).grid(row=2, column=1, sticky="w", padx=12)
        self.refresh_presets()
        self.sync_editor()
        self.refresh_tiles()

    def scroll(self, event):
        if event.widget.winfo_class() in ("TCombobox", "Listbox"):
            return
        y = self.window.winfo_pointery()
        if self.canvas.winfo_rooty() <= y < self.canvas.winfo_rooty() + self.canvas.winfo_height() and event.delta:
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def sync_editor(self):
        self._syncing = True
        try:
            settings = self.profile.keys[self.selected_key]
            self.key_title.set(DISPLAY_KEYS.get(self.selected_key, self.selected_key))
            self.enabled.set(settings.enabled)
            self.release_level.set(str(settings.release_level))
            self.press_level.set(str(settings.press_level))
            for widget in self.level_widgets:
                widget.configure(state="readonly" if settings.enabled else "disabled")
        finally:
            self._syncing = False

    def refresh_tiles(self):
        rows = []
        for key in KEYS:
            settings = self.profile.keys[key]
            selected = key == self.selected_key
            name = DISPLAY_KEYS.get(key, key)
            state = "RT ON" if settings.enabled else "RT OFF"
            self.tiles[key].configure(text=f"{name}\n{state}",
                                      background="#2861c7" if selected else "#e1e7f2" if settings.enabled else "#eeeeee",
                                      foreground="white" if selected else "#253044")
            rows.append(f"{name}: {settings.release_level} / {settings.press_level}" if settings.enabled else f"{name}: RT OFF")
        self.key_summary.set("\n".join(rows))

    def select_key(self, key):
        if key not in KEYS:
            raise ValueError("This key is not supported.")
        self.selected_key = key
        self.sync_editor()
        self.refresh_tiles()

    def invalidate_output(self, message="Settings changed. Generate a new firmware file to use them."):
        self.pending_output = None
        self.output_text.set("No firmware has been generated for the current settings.")
        self.copy_button.configure(state="disabled")
        self.status.set(message)

    def edit_key(self, *_):
        if self._syncing:
            return
        self.profile = self.profile.replace_key(self.selected_key, enabled=self.enabled.get(),
                                               release_level=int(self.release_level.get()),
                                               press_level=int(self.press_level.get()))
        self.sync_editor()
        self.refresh_tiles()
        self.invalidate_output()

    def apply_profile(self, profile: Profile):
        self.profile = profile
        self.sync_editor()
        self.refresh_tiles()
        self.invalidate_output("Settings loaded. Generate a firmware file to use this profile.")

    def copy_to_all(self):
        self.apply_profile(self.profile.copy_key_to_all(self.selected_key))
        self.status.set("Copied this key's levels and RT ON/OFF state to all eight keys. Generate a new firmware file.")

    def reset_profile(self):
        self.apply_profile(Profile.default())

    def refresh_presets(self):
        self.presets = self.storage.presets()
        self.preset_choice["values"] = [record["name"] + " · " + path.stem[-6:] for path, record in self.presets]

    def save_preset(self):
        try:
            path = self.storage.save_preset(self.preset_name.get(), self.profile)
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not save preset", str(error), parent=self.window)
            return
        self.refresh_presets()
        self.preset_choice.current(next(index for index, (item, _) in enumerate(self.presets) if item == path))
        self.status.set("Preset saved. Saving settings does not apply them to a keyboard.")

    def choose_preset(self, _=None):
        index = self.preset_choice.current()
        if index < 0:
            return
        path, record = self.presets[index]
        try:
            self.apply_profile(self.storage.load_profile(path))
            self.preset_name.set(record["name"])
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not load preset", str(error), parent=self.window)

    def import_profile(self):
        name = filedialog.askopenfilename(parent=self.window, title="Load settings JSON",
                                          filetypes=[("JSON settings", "*.json")])
        if not name:
            return
        try:
            self.apply_profile(self.storage.load_profile(name))
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not load settings", str(error), parent=self.window)

    def set_stock(self, path: str | Path):
        """Validate the source immediately; build_file validates it again at generation."""
        self.stock_path = None
        self.stock_digest = None
        self.build_button.configure(state="disabled")
        self.source_text.set("No valid original firmware selected.")
        self.invalidate_output("Validating the selected original firmware…")
        data = Path(path).read_bytes()
        firmware.validate_stock(data)
        self.stock_path = Path(path).resolve()
        self.stock_digest = hashlib.sha256(data).hexdigest()
        self.source_text.set(f"Validated R3SC31 / A0.11\n{self.stock_path}\nSHA-256: {self.stock_digest}")
        self.build_button.configure(state="normal")
        self.status.set("Original firmware validated. Adjust keys, then generate a firmware file.")

    def select_stock(self):
        path = filedialog.askopenfilename(parent=self.window, title="Select your original R3SC31 / A0.11 firmware",
                                          filetypes=[("REALFORCE firmware", "*.rfb"), ("All files", "*")])
        if not path:
            return
        try:
            self.set_stock(path)
        except (OSError, ValueError) as error:
            self.status.set("The source was rejected. Select the supported original firmware.")
            messagebox.showerror("Original firmware rejected", str(error), parent=self.window)

    def generate_to(self, path: str | Path) -> Path:
        if self.stock_path is None:
            raise ValueError("Select the supported original firmware before generating a file.")
        self.invalidate_output("Generating a firmware file…")
        output = firmware.build_file(self.stock_path, Path(path), self.profile)
        self.pending_output = Path(output).resolve()
        self.output_text.set(str(self.pending_output))
        self.copy_button.configure(state="normal")
        self.status.set("File generated. Install it separately using the supported updater to apply these settings.")
        return self.pending_output

    def generate(self):
        name = filedialog.asksaveasfilename(parent=self.window, title="Save generated firmware as a new file",
                                           defaultextension=".rfb", initialfile="R3SC_A011_GAME8_RT.rfb",
                                           filetypes=[("REALFORCE firmware", "*.rfb")], confirmoverwrite=False)
        if not name:
            return
        self.build_button.configure(state="disabled")
        self.window.update_idletasks()
        try:
            self.generate_to(name)
        except (OSError, ValueError) as error:
            self.status.set("No new firmware was generated. Review the error and try again.")
            messagebox.showerror("Could not generate firmware", str(error), parent=self.window)
        finally:
            self.build_button.configure(state="normal" if self.stock_path else "disabled")

    def copy_output(self):
        if self.pending_output is None:
            return
        if not self.pending_output.is_file():
            self.invalidate_output("The generated file is missing. Generate it again.")
            return
        self.window.clipboard_clear()
        self.window.clipboard_append(str(self.pending_output))
        self.status.set("Generated file path copied. The keyboard has not been changed by this app.")

    def open_key_test(self):
        KeyTestWindow(self.window, self.storage)


def launch(profile_path: str | Path | None = None):
    profile = Storage.load_profile(profile_path) if profile_path is not None else Profile.default()
    try:
        window = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError("Could not open the settings window. Use a desktop session with working Tkinter.") from error
    SettingsApp(window, profile=profile)
    window.mainloop()


def launch_key_test():
    try:
        window = tk.Tk()
    except tk.TclError as error:
        raise RuntimeError("Could not open the key-check window. Use a desktop session with working Tkinter.") from error
    window.withdraw()
    checker = KeyTestWindow(window)
    checker.window.bind("<Destroy>", lambda event: window.destroy() if event.widget == checker.window else None)
    window.mainloop()
