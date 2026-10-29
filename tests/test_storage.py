import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from r3s_rt.profile import Profile
from r3s_rt.storage import MAX_JSON_BYTES, Storage, read_json, user_data_directory


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.storage = Storage(Path(self.temporary.name) / "user-data")

    def test_read_only_initialization_creates_no_directories(self):
        self.assertEqual(self.storage.presets(), [])
        self.assertFalse(self.storage.directory.exists())

    def test_named_preset_round_trip_retains_all_keys(self):
        profile = Profile.default().replace_key("LeftShift", enabled=False, release_level=7, press_level=4)
        path = self.storage.save_preset("  Game settings  ", profile)
        self.assertEqual(Storage.load_profile(path), profile)
        self.assertEqual(self.storage.presets()[0][1]["name"], "Game settings")
        self.assertEqual(path.parent, self.storage.presets_directory)

    def test_repeated_names_do_not_overwrite_previous_preset(self):
        first = self.storage.save_preset("Game", Profile.default())
        second = self.storage.save_preset("Game", Profile.default().replace_key("Q", enabled=False))
        self.assertNotEqual(first, second)
        self.assertEqual(len(self.storage.presets()), 2)
        self.assertTrue(Storage.load_profile(first).keys["Q"].enabled)
        self.assertFalse(Storage.load_profile(second).keys["Q"].enabled)

    def test_names_never_become_paths_and_control_characters_are_rejected(self):
        path = self.storage.save_preset("../my/profile", Profile.default())
        self.assertEqual(path.parent, self.storage.presets_directory)
        for name in ("", "   ", "a" * 65, "name\n", "a\x00b", "a\x7fb"):
            with self.subTest(name=repr(name)), self.assertRaises(ValueError):
                self.storage.save_preset(name, Profile.default())

    def test_loads_plain_profile_as_well_as_preset(self):
        path = Path(self.temporary.name) / "profile.json"
        profile = Profile.default().replace_key("Space", press_level=6)
        path.write_text(json.dumps(profile.to_dict()), encoding="utf-8")
        self.assertEqual(Storage.load_profile(path), profile)

    def test_malformed_preset_does_not_hide_valid_presets(self):
        valid = self.storage.save_preset("Good", Profile.default())
        (valid.parent / "bad.json").write_text("not JSON", encoding="utf-8")
        (valid.parent / "wrong.json").write_text('{"schema":"wrong"}', encoding="utf-8")
        self.assertEqual([path for path, _ in self.storage.presets()], [valid])
        with self.assertRaises(ValueError):
            Storage.load_profile(valid.parent / "bad.json")

    def test_rejects_oversized_json_and_non_object(self):
        path = Path(self.temporary.name) / "invalid.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_json(path)
        path.write_bytes(b" " * (MAX_JSON_BYTES + 1))
        with self.assertRaises(ValueError):
            read_json(path)

    def test_event_record_is_saved_separately_without_source_assets(self):
        record = {"schema": "r3s-rt-foreground-events-v1", "events": [], "raw_measurement": False}
        path = self.storage.save_key_test(record)
        self.assertEqual(read_json(path), record)
        self.assertEqual(path.parent, self.storage.events_directory)
        self.assertEqual(list(self.storage.directory.rglob("*.rfb")), [])

    def test_windows_data_folder_uses_current_users_environment(self):
        with patch("r3s_rt.storage.sys.platform", "win32"), patch.dict("os.environ", {"LOCALAPPDATA": self.temporary.name}):
            self.assertEqual(user_data_directory(), Path(self.temporary.name) / "r3s-rapid-trigger")

    def test_full_eight_key_check_can_exceed_small_settings_file_limit(self):
        record = {"schema": "r3s-rt-foreground-events-v1", "events": [
            {"key": "LeftShift", "event": "down", "elapsed_ms": float(index)} for index in range(2500)]}
        path = self.storage.save_key_test(record)
        self.assertGreater(path.stat().st_size, MAX_JSON_BYTES)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), record)


if __name__ == "__main__":
    unittest.main()
