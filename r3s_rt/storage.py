"""User-owned settings and event records, separate from the installation folder."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

from .profile import Profile

MAX_JSON_BYTES = 128 * 1024
MAX_EVENT_JSON_BYTES = 8 * 1024 * 1024


def user_data_directory() -> Path:
    """Return the normal per-user data folder without creating it."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "r3s-rapid-trigger"


def read_json(path: str | Path) -> dict:
    path = Path(path)
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("The settings file is too large (maximum 128 KiB).")
    with path.open("r", encoding="utf-8-sig") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("The settings file must contain a JSON object.")
    return value


class Storage:
    """Store JSON only. Firmware inputs and outputs stay at user-selected paths."""

    def __init__(self, directory: str | Path | None = None):
        self.directory = Path(directory) if directory is not None else user_data_directory()

    @property
    def presets_directory(self) -> Path:
        return self.directory / "presets"

    @property
    def events_directory(self) -> Path:
        return self.directory / "key-tests"

    def _write_new(self, folder: Path, record: dict, maximum_bytes: int = MAX_JSON_BYTES) -> Path:
        text = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        if len(text.encode("utf-8")) > maximum_bytes:
            raise ValueError("The record is too large to save.")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (str(uuid4()) + ".json")
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        return path

    def save_preset(self, name: str, profile: Profile) -> Path:
        if not isinstance(name, str) or any(ord(char) < 32 or ord(char) == 127 for char in name):
            raise ValueError("Use a preset name of 1 to 64 characters without control characters.")
        name = name.strip()
        if not 1 <= len(name) <= 64:
            raise ValueError("Use a preset name of 1 to 64 characters without control characters.")
        return self._write_new(self.presets_directory, {
            "schema": "r3s-rt-preset-v1",
            "name": name,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "profile": profile.to_dict(),
        })

    @staticmethod
    def load_profile(path: str | Path) -> Profile:
        record = read_json(path)
        if record.get("schema") == "r3s-rt-preset-v1":
            record = record.get("profile")
            if not isinstance(record, dict):
                raise ValueError("The preset does not contain a settings object.")
        return Profile.from_dict(record)

    def presets(self) -> list[tuple[Path, dict]]:
        """List valid saved presets; a damaged file never hides other presets."""
        result = []
        for path in self.presets_directory.glob("*.json"):
            try:
                record = read_json(path)
                if record.get("schema") != "r3s-rt-preset-v1":
                    continue
                if not isinstance(record.get("name"), str):
                    continue
                Profile.from_dict(record["profile"])
                datetime.fromisoformat(record["created_utc"])
                result.append((path, record))
            except (OSError, ValueError, KeyError, TypeError):
                continue
        return sorted(result, key=lambda item: item[1]["created_utc"], reverse=True)

    def save_key_test(self, record: dict) -> Path:
        return self._write_new(self.events_directory, record, MAX_EVENT_JSON_BYTES)
