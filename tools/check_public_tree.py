"""Check the publication allowlist for private material and English-only text."""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_SUFFIXES = {".rfb", ".bin", ".hex", ".elf", ".dll", ".exe", ".zip", ".pem", ".key", ".log"}
IGNORED_PARTS = {".git", "__pycache__", ".venv", "venv", "build", "dist"}
REVIEWED_IMAGES = {"docs/assets/settings.jpg"}
PRIVATE_PATH = re.compile(
    r"(?:[A-Za-z]:[\\/]Users[\\/][^\s\"']+|" + "/" + r"Users/[^/\s]+|" + "/" + r"home/[^/\s]+)"
)
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:authorization|access_token|api_key)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{24,}"),
]


def candidate_files():
    if (ROOT / ".git").exists():
        result = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, check=True)
        return [ROOT / name for name in result.stdout.decode("utf-8").split("\0") if name]
    return [path for path in ROOT.rglob("*") if path.is_file() and not set(path.relative_to(ROOT).parts) & IGNORED_PARTS]


def check(paths):
    errors = []
    for path in paths:
        name = path.relative_to(ROOT).as_posix()
        if name in REVIEWED_IMAGES:
            image = path.read_bytes()
            if len(image) > 1_000_000 or not image.startswith(b"\xff\xd8") or not image.endswith(b"\xff\xd9"):
                errors.append((name, "unexpected documentation image"))
            continue
        if path.suffix.lower() in BLOCKED_SUFFIXES or name.startswith(("private/", "inputs/", "output/", "settings/", "logs/")):
            errors.append((name, "private or binary artifact"))
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeError:
            errors.append((name, "non-text file"))
            continue
        if CJK.search(text):
            errors.append((name, "non-English text requiring review"))
        if PRIVATE_PATH.search(text):
            errors.append((name, "personal absolute path"))
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            errors.append((name, "possible credential; inspect locally without posting it"))
        if path.suffix == ".json":
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                errors.append((name, "invalid JSON"))
            else:
                if '"before"' in text:
                    errors.append((name, "original-opcode patch ledger field"))
    return errors


def main():
    files = candidate_files()
    errors = check(files)
    for name, reason in errors:
        print(f"REVIEW {name}: {reason}", file=sys.stderr)
    if errors:
        return 1
    print(f"Public-tree check passed for {len(files)} text files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
