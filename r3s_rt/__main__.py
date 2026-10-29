"""Command-line entry point for local inspection and firmware generation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from . import __version__


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="r3s-rt",
        description="Unofficial R3S Rapid Trigger tools. All operations are local; no device is flashed.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")
    gui = commands.add_parser("gui", help="Open the eight-key settings app")
    gui.add_argument("--profile", type=Path, help="Optional saved settings JSON")
    inspect = commands.add_parser("inspect", help="Check a user-supplied stock firmware file")
    inspect.add_argument("stock", type=Path)
    build = commands.add_parser("build", help="Generate a modified firmware file locally")
    build.add_argument("stock", type=Path)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--profile", type=Path, help="Settings JSON; defaults to all eight keys enabled at level 1/1")
    commands.add_parser("key-test", help="Open the finite foreground OS key-event test")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command in (None, "gui"):
            from .app import launch
            launch(profile_path=getattr(args, "profile", None))
        elif args.command == "inspect":
            from .firmware import validate_stock
            data = args.stock.read_bytes()
            validate_stock(data)
            print(json.dumps({"supported": True, "model": "R3SC31", "stockVersion": "A0.11", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "deviceAccess": False}, indent=2))
        elif args.command == "build":
            from .firmware import build_file
            from .profile import Profile
            profile = Profile.default()
            if args.profile:
                if args.profile.stat().st_size > 1_000_000:
                    raise ValueError("Settings file is too large.")
                from .storage import Storage
                profile = Storage.load_profile(args.profile)
            result = build_file(args.stock, args.output, profile)
            print(json.dumps({"output": str(result), "sha256": hashlib.sha256(result.read_bytes()).hexdigest(), "state": "file-created-not-flashed", "deviceAccess": False}, indent=2))
        elif args.command == "key-test":
            from .app import launch_key_test
            launch_key_test()
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except ImportError as error:
        print(f"Error: a required Python module is unavailable: {error}. The graphical app requires Tkinter.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
