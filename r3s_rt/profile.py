"""Immutable, portable settings for the eight supported keys.

Sensitivity levels are Raw-count movement thresholds, not millimeters.
"""

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Mapping

KEYS = ("W", "A", "S", "D", "Q", "E", "LeftShift", "Space")
RAW_AMOUNTS = (48, 72, 120, 160, 240, 320, 480)
SCHEMA = "r3s-rapid-trigger-profile-v1"


@dataclass(frozen=True)
class KeySettings:
    enabled: bool = True
    release_level: int = 1
    press_level: int = 1

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError("Enabled must be true or false.")
        for name, value in (("Release", self.release_level), ("Press", self.press_level)):
            if type(value) is not int or not 1 <= value <= 7:
                raise ValueError(f"{name} sensitivity must be an integer from 1 to 7.")


@dataclass(frozen=True, init=False)
class Profile:
    """A complete settings snapshot. Methods return a new snapshot."""

    _settings: tuple[KeySettings, ...]

    def __init__(self, keys: Mapping[str, KeySettings] | None = None):
        if keys is None:
            values = (KeySettings(),) * len(KEYS)
        else:
            if not isinstance(keys, Mapping) or set(keys) != set(KEYS):
                raise ValueError("A profile must contain exactly the eight supported keys.")
            values = tuple(keys[key] for key in KEYS)
            if any(not isinstance(value, KeySettings) for value in values):
                raise ValueError("Each key must have KeySettings values.")
        object.__setattr__(self, "_settings", values)

    @classmethod
    def default(cls):
        return cls()

    @property
    def keys(self):
        return MappingProxyType(dict(zip(KEYS, self._settings)))

    def key(self, name):
        if name not in KEYS:
            raise ValueError(f"Unsupported key: {name!r}.")
        return self._settings[KEYS.index(name)]

    def replace_key(self, key, enabled=None, release_level=None, press_level=None):
        previous = self.key(key)
        changes = {}
        if enabled is not None:
            changes["enabled"] = enabled
        if release_level is not None:
            changes["release_level"] = release_level
        if press_level is not None:
            changes["press_level"] = press_level
        values = dict(self.keys)
        values[key] = replace(previous, **changes)
        return Profile(values)

    def copy_key_to_all(self, key):
        settings = self.key(key)
        return Profile({name: settings for name in KEYS})

    def to_dict(self):
        return {
            "schema": SCHEMA,
            "keys": {
                key: {"enabled": value.enabled, "release_level": value.release_level,
                      "press_level": value.press_level}
                for key, value in self.keys.items()
            },
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("The profile must be a JSON object.")
        if data.get("schema") == "r3sc-game8-rt-profile-v1":
            return cls._from_legacy(data)
        if set(data) != {"schema", "keys"} or data.get("schema") != SCHEMA:
            raise ValueError("Unsupported profile schema.")
        entries = data["keys"]
        if not isinstance(entries, dict) or set(entries) != set(KEYS):
            raise ValueError("The profile must contain exactly the eight supported keys.")
        keys = {}
        for key in KEYS:
            entry = entries[key]
            if not isinstance(entry, dict) or set(entry) != {"enabled", "release_level", "press_level"}:
                raise ValueError(f"Invalid settings for {key}.")
            keys[key] = KeySettings(**entry)
        return cls(keys)

    @classmethod
    def _from_legacy(cls, data):
        """Import a frozen GAME8 profile without trusting derived Raw metadata."""
        if data.get("keyGroup") != "GAME8" or data.get("apcCompatible") is not True:
            raise ValueError("Only APC-compatible GAME8 profiles can be imported.")
        entries = data.get("perKey")
        if not isinstance(entries, dict) or set(entries) != set(KEYS):
            raise ValueError("The legacy profile must contain all eight supported keys.")
        keys = {}
        for key in KEYS:
            entry = entries[key]
            if not isinstance(entry, dict):
                raise ValueError(f"Invalid legacy settings for {key}.")
            keys[key] = KeySettings(entry.get("enabled"), entry.get("releaseLevel"), entry.get("pressLevel"))
        return cls(keys)
