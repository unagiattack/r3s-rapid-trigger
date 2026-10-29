"""Portable profile validation; no original firmware is needed."""

import unittest

from r3s_rt.profile import KEYS, KeySettings, Profile


class ProfileTests(unittest.TestCase):
    def test_default_and_round_trip(self):
        profile = Profile.default()
        self.assertEqual(tuple(profile.keys), KEYS)
        self.assertTrue(all(value == KeySettings(True, 1, 1) for value in profile.keys.values()))
        self.assertEqual(Profile.from_dict(profile.to_dict()), profile)

    def test_individual_changes_are_immutable(self):
        original = Profile.default()
        changed = original.replace_key("Q", enabled=False, release_level=7, press_level=3)
        self.assertEqual(original.key("Q"), KeySettings())
        self.assertEqual(changed.key("Q"), KeySettings(False, 7, 3))
        self.assertEqual(changed.key("W"), original.key("W"))
        with self.assertRaises(TypeError):
            changed.keys["W"] = KeySettings()

    def test_copy_includes_enabled_and_both_sensitivities(self):
        profile = Profile.default().replace_key("LeftShift", False, 2, 6).copy_key_to_all("LeftShift")
        self.assertTrue(all(value == KeySettings(False, 2, 6) for value in profile.keys.values()))

    def test_levels_and_booleans_are_strict(self):
        for value in (True, False, 0, 8, 1.0, "1", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                KeySettings(True, value, 1)
        for value in (0, 1, "true", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                KeySettings(value, 1, 1)

    def test_unknown_or_missing_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            Profile.default().replace_key("R")
        for mutation in ("missing", "unknown", "extra-field"):
            record = Profile.default().to_dict()
            if mutation == "missing":
                del record["keys"]["Space"]
            elif mutation == "unknown":
                record["keys"]["R"] = record["keys"].pop("Q")
            else:
                record["keys"]["W"]["sensor"] = 999
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                Profile.from_dict(record)

    def test_import_frozen_game8_settings(self):
        record = {"schema": "r3sc-game8-rt-profile-v1", "keyGroup": "GAME8", "apcCompatible": True,
                  "perKey": {key: {"enabled": index % 2 == 0, "releaseLevel": 2, "pressLevel": 5}
                             for index, key in enumerate(KEYS)}}
        profile = Profile.from_dict(record)
        self.assertEqual(profile.key("W"), KeySettings(True, 2, 5))
        self.assertEqual(profile.key("A"), KeySettings(False, 2, 5))
        self.assertNotIn("sensor", profile.to_dict()["keys"]["W"])

    def test_legacy_invalid_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            Profile.from_dict({"schema": "r3sc-game8-rt-profile-v1", "keyGroup": "GAME8", "apcCompatible": False})


if __name__ == "__main__":
    unittest.main()
