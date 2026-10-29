from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import tkinter as tk
except ImportError:
    tk = None

from r3s_rt.profile import Profile
from r3s_rt.storage import Storage


@unittest.skipIf(tk is None, "Tk is not installed")
class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            probe = tk.Tk()
            probe.withdraw()
            probe.destroy()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display unavailable: {error}")
        from r3s_rt.app import SettingsApp
        cls.app_class = SettingsApp

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.window = tk.Tk()
        self.window.withdraw()
        self.addCleanup(self.close_window)
        self.storage = Storage(Path(self.temporary.name) / "user-data")
        self.app = self.app_class(self.window, storage=self.storage)
        self.window.update_idletasks()

    def close_window(self):
        self.window.update_idletasks()
        self.window.destroy()

    def make_generated(self):
        path = Path(self.temporary.name) / "generated.rfb"
        path.write_bytes(b"test output")
        self.app.pending_output = path
        self.app.output_text.set(str(path))
        self.app.copy_button.configure(state="normal")
        return path

    def test_initialization_has_eight_keys_and_does_not_write_user_files(self):
        self.assertEqual(set(self.app.tiles), {"W", "A", "S", "D", "Q", "E", "LeftShift", "Space"})
        self.assertIsNone(self.app.stock_path)
        self.assertIsNone(self.app.pending_output)
        self.assertFalse(self.storage.directory.exists())
        self.assertEqual(str(self.app.build_button["state"]), "disabled")

    def test_key_selection_preserves_generated_output(self):
        path = self.make_generated()
        self.app.select_key("LeftShift")
        self.assertEqual(self.app.pending_output, path)
        self.assertEqual(self.app.key_title.get(), "Left Shift")

    def test_level_change_invalidates_output_and_only_changes_selected_key(self):
        self.make_generated()
        self.app.select_key("E")
        self.app.release_level.set("7")
        self.assertIsNone(self.app.pending_output)
        self.assertEqual(str(self.app.copy_button["state"]), "disabled")
        self.assertEqual(self.app.profile.keys["E"].release_level, 7)
        self.assertEqual(self.app.profile.keys["W"].release_level, 1)

    def test_disabled_key_keeps_levels_and_copy_to_all_copies_enabled_state(self):
        self.app.release_level.set("6")
        self.app.press_level.set("3")
        self.app.enabled.set(False)
        self.assertEqual(str(self.app.level_widgets[0]["state"]), "disabled")
        self.app.copy_to_all()
        for value in self.app.profile.keys.values():
            self.assertFalse(value.enabled)
            self.assertEqual((value.release_level, value.press_level), (6, 3))

    def test_loading_profile_invalidates_stale_output(self):
        self.make_generated()
        self.app.apply_profile(Profile.default().replace_key("Space", press_level=5))
        self.assertIsNone(self.app.pending_output)
        self.assertEqual(self.app.profile.keys["Space"].press_level, 5)

    def test_invalid_stock_clears_prior_source_and_output(self):
        self.make_generated()
        self.app.stock_path = Path(self.temporary.name) / "old.rfb"
        path = Path(self.temporary.name) / "bad.rfb"
        path.write_bytes(b"not original firmware")
        with self.assertRaises(ValueError):
            self.app.set_stock(path)
        self.assertIsNone(self.app.stock_path)
        self.assertIsNone(self.app.pending_output)
        self.assertEqual(str(self.app.build_button["state"]), "disabled")

    def test_valid_stock_then_generation_uses_current_profile_and_explicit_output(self):
        source = Path(self.temporary.name) / "input.rfb"
        source.write_bytes(b"mock original")
        output = Path(self.temporary.name) / "chosen-output.rfb"
        self.app.press_level.set("4")
        with patch("r3s_rt.app.firmware.validate_stock") as validate:
            self.app.set_stock(source)
        validate.assert_called_once_with(b"mock original")
        def write(stock, target, profile):
            self.assertEqual(stock, source.resolve())
            self.assertEqual(profile.keys["W"].press_level, 4)
            target.write_bytes(b"mock generated")
            return target
        with patch("r3s_rt.app.firmware.build_file", side_effect=write):
            result = self.app.generate_to(output)
        self.assertEqual(result, output.resolve())
        self.assertEqual(self.app.pending_output, output.resolve())
        self.assertEqual(source.read_bytes(), b"mock original")
        self.assertFalse(self.storage.directory.exists())

    def test_failed_generation_does_not_leave_stale_output(self):
        self.make_generated()
        self.app.stock_path = Path(self.temporary.name) / "input.rfb"
        with patch("r3s_rt.app.firmware.build_file", side_effect=ValueError("Rejected source")):
            with self.assertRaises(ValueError):
                self.app.generate_to(Path(self.temporary.name) / "output.rfb")
        self.assertIsNone(self.app.pending_output)

    def test_saved_presets_leave_generated_output_current(self):
        path = self.make_generated()
        self.app.preset_name.set("My settings")
        self.app.save_preset()
        self.assertEqual(self.app.pending_output, path)
        self.assertEqual(len(self.storage.presets()), 1)

    def test_fixed_footer_fits_at_minimum_window_size(self):
        self.window.geometry("880x650")
        self.window.deiconify()
        self.window.update()
        button = self.app.copy_button
        self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                             self.window.winfo_rooty() + self.window.winfo_height())
        self.window.withdraw()


if __name__ == "__main__":
    unittest.main()
