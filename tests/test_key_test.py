import unittest

from r3s_rt.key_test import KeyEventSession


class KeyEventTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.session = KeyEventSession(lambda: self.now)

    def test_records_all_eight_keys_without_right_shift(self):
        self.session.begin()
        for key in ("w", "a", "s", "d", "q", "e", "Shift_L", "space"):
            self.assertTrue(self.session.event("down", key))
            self.assertTrue(self.session.event("up", key))
        self.assertFalse(self.session.event("down", "Shift_R"))
        self.assertEqual(len(self.session.events), 16)
        self.assertEqual(self.session.issues, [])

    def test_ignores_auto_repeat_but_keeps_repress_after_release(self):
        self.session.begin()
        for kind in ("down", "down", "down", "up", "down", "up"):
            self.session.event(kind, "w")
        self.assertEqual([event["event"] for event in self.session.events], ["down", "up", "down", "up"])

    def test_begin_rejects_keys_already_held_and_running_session(self):
        with self.assertRaises(ValueError):
            self.session.begin(already_down=True)
        self.session.begin()
        with self.assertRaises(ValueError):
            self.session.begin()

    def test_capture_has_finite_duration(self):
        self.session.begin()
        self.now = 19.9
        self.assertTrue(self.session.event("down", "w"))
        self.now = 20.0
        self.assertFalse(self.session.event("up", "w"))
        self.assertFalse(self.session.active)
        self.assertEqual(self.session.reason, "time limit")
        self.assertEqual(len(self.session.events), 1)
        self.assertTrue(self.session.issues)

    def test_focus_loss_stops_capture_and_marks_incomplete_events(self):
        self.session.begin()
        self.session.event("down", "Space")
        record = self.session.finish("focus lost")
        self.assertFalse(self.session.event("up", "Space"))
        self.assertEqual(record["reason"], "focus lost")
        self.assertIn("Space", record["held_keys"])
        self.assertEqual(len(record["issues"]), 2)
        self.assertFalse(record["raw_measurement"])
        self.assertFalse(record["device_identified"])

    def test_duplicate_finish_keeps_original_reason_and_duration(self):
        self.session.begin()
        self.now = 5
        first = self.session.finish("user stop")
        self.now = 15
        second = self.session.finish("window close")
        self.assertEqual(first["reason"], second["reason"])
        self.assertEqual(first["elapsed_seconds"], second["elapsed_seconds"])

    def test_unmatched_release_is_reported_and_not_counted_as_valid(self):
        self.session.begin()
        self.assertFalse(self.session.event("up", "q"))
        self.assertEqual(len(self.session.events), 0)
        self.assertEqual(len(self.session.issues), 1)

    def test_new_session_clears_previous_events(self):
        self.session.begin()
        self.session.event("down", "w")
        self.session.finish()
        self.session.begin()
        self.assertEqual(self.session.events, [])
        self.assertEqual(self.session.held, set())
        self.assertEqual(self.session.issues, [])

    def test_invalid_durations_and_event_kinds_are_rejected(self):
        for duration in (0, -1, float("inf"), float("nan")):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                KeyEventSession(duration=duration)
        with self.assertRaises(ValueError):
            self.session.event("click", "w")


if __name__ == "__main__":
    unittest.main()
