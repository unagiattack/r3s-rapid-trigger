"""Command-line tests that never access a device or an original firmware image."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from r3s_rt.__main__ import main, make_parser


class CommandLineTests(unittest.TestCase):
    def test_build_requires_an_explicit_output(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            make_parser().parse_args(["build", "stock.rfb"])

    def test_inspection_failure_is_an_error_without_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.rfb"
            with contextlib.redirect_stderr(io.StringIO()) as output:
                result = main(["inspect", str(missing)])
            self.assertEqual(result, 1)
            self.assertIn("Error:", output.getvalue())
            self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
