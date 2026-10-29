"""Export independently authored rows from a native assembler listing.

Manufacturer-derived .stock16 rows are always excluded. This tool never reads a
stock firmware file, an old firmware image, or an original-opcode patch ledger.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def parse_source(path):
    pc, rows, stock_words, labels = 0, {}, [], {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith(".org "):
            pc = int(line[5:], 0)
        elif line == ".align4":
            pc = (pc + 3) & ~3
        elif line.endswith(":"):
            name = line[:-1]
            if name in labels:
                raise ValueError("Duplicate native label.")
            labels[name] = pc
        elif line.startswith(".stock16 "):
            source, mask, bits = (int(part, 0) for part in line.split()[1:])
            stock_words.append({"address": f"0x{pc:08x}", "source": f"0x{source:08x}",
                                "clearMask": mask, "setBits": bits})
            pc += 2
        else:
            if line.startswith(".word "):
                width = 4
            elif re.match(r"^[24]\|", line):
                width = int(line[0])
            else:
                raise ValueError(f"Unsupported source directive: {line}")
            if pc in rows or not 0x0801E394 <= pc < pc + width <= 0x08020000:
                raise ValueError("Native source row overlaps or is out of bounds.")
            rows[pc] = width
            pc += width
    return rows, sorted(stock_words, key=lambda row: row["address"]), labels


def export(listing, output):
    source = ROOT / "native" / "rapid_trigger.asm"
    expected, words, labels = parse_source(source)
    recipe = json.loads((ROOT / "r3s_rt/data/adc_recipe.json").read_text(encoding="utf-8"))
    if recipe["words"] != words:
        raise ValueError("The packaged ADC recipe differs from the authored source directives.")
    excluded = {int(row["address"], 16) for row in words}
    rows = {}
    for line in listing.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{8}) \| ([0-9a-f]+) \| .+", line)
        if not match:
            raise ValueError("Invalid native listing row.")
        address, data = int(match[1], 16), bytes.fromhex(match[2])
        if address in excluded:
            continue
        if address not in expected or len(data) != expected[address] or address in rows:
            raise ValueError("The listing does not match the authored source row layout.")
        if address == labels["activation_header"]:
            if int.from_bytes(data, "little") not in (0, 1):
                raise ValueError("Unexpected activation header.")
            data = (1).to_bytes(4, "little")
        rows[address] = data
    if set(rows) != set(expected):
        raise ValueError("The listing is missing authored source rows.")
    # Preserve source order: it is stable even where .org moves backward.
    blocks = []
    for address in expected:
        data = rows[address]
        if blocks and int(blocks[-1]["address"], 16) + len(bytes.fromhex(blocks[-1]["hex"])) == address:
            blocks[-1]["hex"] += data.hex()
        else:
            blocks.append({"address": f"0x{address:08x}", "hex": data.hex()})
    hooks = json.loads((ROOT / "native/hooks.json").read_text(encoding="utf-8"))
    payload = {"schema": 1,
               "description": "Independently authored native additions only; manufacturer-derived ADC words are omitted and derived from user stock.",
               "blocks": blocks, "hooks": hooks,
               "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    output.parent.mkdir(parents=True, exist_ok=True)
    # Asset hashes must survive Git checkout on Windows and other platforms.
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    return len(blocks), len(words)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listing", required=True, type=Path, help="Authored native assembler listing")
    parser.add_argument("--output", type=Path, default=ROOT / "r3s_rt/data/native.json")
    args = parser.parse_args()
    blocks, excluded = export(args.listing, args.output)
    print(f"Exported {blocks} authored blocks; excluded {excluded} stock-derived words.")


if __name__ == "__main__":
    main()
