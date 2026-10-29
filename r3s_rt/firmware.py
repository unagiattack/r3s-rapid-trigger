"""Build a firmware file locally, using an exact user-supplied stock image.

There is no device communication or flashing code. Packaged native blocks are
our additions. The ADC compatibility words are obtained from the user's stock
image at build time; manufacturer instructions are not packaged in this project.
"""

import hashlib
from importlib import resources
import json
from pathlib import Path
import struct

from .profile import KEYS, Profile, RAW_AMOUNTS

STOCK_SHA256 = "c210e9b0447fa47047974a188f2b1e24b62b80dcc2443daa7d8f878823000da9"
STOCK_SIZE = 65568
DEFAULT_OUTPUT_SHA256 = "1a502cea7eba942c82cef4efaa89b4f3e9c025b6d1760bd69c9ef9f7276782ca"
FLASH_BASE = 0x08010000
PAYLOAD_END = 65540
NATIVE_START = 0x0801E394
FLASH_END = 0x08020000
CONFIG_ADDRESS = 0x0801F640
TABLE_ADDRESS = 0x0801FC10
SENSORS = (17, 30, 31, 32, 16, 18, 43, 60)
ASSET_SHA256 = {
    "native.json": "3d168b699e2f5527ccf14876ddf1692e2c4ab85f6da41ce5820be99095a06f2a",
    "adc_recipe.json": "b3bd600118046e8c4d4b01cf77c8821d39e6e3baf5acae2c21c2ef2f8a1093b9",
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def crc16(data):
    """CRC-16, reflected polynomial 0x8408, initial 0xffff, no final XOR."""
    value = 0xFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0x8408 if value & 1 else 0)
    return value


def validate_stock(data: bytes) -> None:
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("The stock firmware must be bytes read from a local file.")
    if len(data) != STOCK_SIZE:
        raise ValueError(f"Unsupported stock file size: expected {STOCK_SIZE} bytes.")
    if sha256(data) != STOCK_SHA256:
        raise ValueError("Unsupported stock firmware. Supply the original R3SC31 A0.11 file "
                         f"with SHA-256 {STOCK_SHA256}.")
    if crc16(data[4:PAYLOAD_END]) != struct.unpack_from("<H", data, 2)[0]:
        raise ValueError("The stock firmware's inner checksum is invalid.")
    if crc16(data[2:]) != struct.unpack_from("<H", data, 0)[0]:
        raise ValueError("The stock firmware's outer checksum is invalid.")


def encode_bl(address, destination):
    """Encode an ARM Thumb BL from addresses, without stock opcode anchors."""
    if address % 2 or destination % 2:
        raise ValueError("Thumb branch addresses must be even.")
    delta = destination - address - 4
    if not -(1 << 24) <= delta < (1 << 24):
        raise ValueError("Thumb branch destination is out of range.")
    immediate = delta & 0x1FFFFFF
    sign = (immediate >> 24) & 1
    i1, i2 = (immediate >> 23) & 1, (immediate >> 22) & 1
    first = 0xF000 | (sign << 10) | ((immediate >> 12) & 0x3FF)
    second = (0xD000 | (((~i1 ^ sign) & 1) << 13)
              | (((~i2 ^ sign) & 1) << 11) | ((immediate >> 1) & 0x7FF))
    return struct.pack("<HH", first, second)


def _asset(name):
    # These JSON resources contain our native additions and an address recipe.
    data = resources.files("r3s_rt").joinpath("data").joinpath(name).read_bytes()
    if sha256(data) != ASSET_SHA256.get(name):
        raise ValueError("Packaged native asset integrity check failed. Reinstall a trusted copy.")
    return json.loads(data.decode("utf-8"))


def _offset(address, size):
    offset = address - FLASH_BASE + 4
    if address < FLASH_BASE or address + size > FLASH_END:
        raise ValueError("A native write is outside the supported flash region.")
    return offset


def _derive_adc_words(stock, recipe):
    """Read stock words locally and relocate only specified register fields.

    A delay-loop branch is copied at the same relative position within its
    seven-word block. Other copied words contain no PC-relative operand.
    No original firmware words or decoded manufacturer source are stored here.
    """
    result = []
    for row in recipe["words"]:
        address, source = int(row["address"], 16), int(row["source"], 16)
        mask, bits = row["clearMask"], row["setBits"]
        if not (0x0801FE00 <= address < 0x0801FE5E and address % 2 == 0):
            raise ValueError("Invalid ADC recipe destination.")
        if not (0x08016338 <= source < 0x080163AA and source % 2 == 0):
            raise ValueError("Invalid ADC recipe source.")
        if mask not in (0, 0x38, 0x700) or bits & ~mask:
            raise ValueError("Invalid ADC register transformation.")
        original, = struct.unpack_from("<H", stock, _offset(source, 2))
        result.append((address, struct.pack("<H", (original & ~mask) | bits)))
    return result


def _assemble_image(stock, profile, native, adc_recipe):
    """Internal assembly step; public entry point validates stock first."""
    result = bytearray(stock)
    occupied = set()

    def apply(address, data, *, native_write):
        offset = _offset(address, len(data))
        locations = set(range(address, address + len(data)))
        if occupied & locations:
            raise ValueError("Native writes overlap.")
        if native_write:
            if address < NATIVE_START:
                raise ValueError("An addition is outside the reserved native region.")
            if any(value != 0xFF for value in stock[offset:offset + len(data)]):
                raise ValueError("The native region is not empty in the supplied firmware.")
        occupied.update(locations)
        result[offset:offset + len(data)] = data

    for block in native["blocks"]:
        apply(int(block["address"], 16), bytes.fromhex(block["hex"]), native_write=True)
    for address, word in _derive_adc_words(stock, adc_recipe):
        apply(address, word, native_write=True)
    for hook in native["hooks"]:
        address = int(hook["address"], 16)
        destination = int(hook["destination"], 16)
        if address >= NATIVE_START or destination not in occupied:
            raise ValueError("Invalid native hook destination.")
        if hook["kind"] == "main-pointer" and address == 0x080100CC:
            data = struct.pack("<I", destination | 1)
        elif hook["kind"] == "bl":
            data = encode_bl(address, destination)
        else:
            raise ValueError("Unsupported native hook kind.")
        apply(address, data, native_write=False)

    # The shared fallback sensitivity follows W, matching the tested builder.
    w = profile.key("W")
    struct.pack_into("<HH", result, _offset(CONFIG_ADDRESS, 6) + 2,
                     RAW_AMOUNTS[w.release_level - 1], RAW_AMOUNTS[w.press_level - 1])
    for index, (key, sensor) in enumerate(zip(KEYS, SENSORS)):
        offset = _offset(TABLE_ADDRESS + index * 12, 12)
        if struct.unpack_from("<I", result, offset)[0] != sensor:
            raise ValueError("The native key table does not match the supported sensor map.")
        settings = profile.key(key)
        struct.pack_into("<HHI", result, offset + 4,
                         RAW_AMOUNTS[settings.release_level - 1],
                         RAW_AMOUNTS[settings.press_level - 1], int(settings.enabled))
    struct.pack_into("<H", result, 2, crc16(result[4:PAYLOAD_END]))
    struct.pack_into("<H", result, 0, crc16(result[2:]))
    if result[4:4 + 0xC0] != stock[4:4 + 0xC0] or result[PAYLOAD_END:] != stock[PAYLOAD_END:]:
        raise ValueError("The firmware vectors or trailer unexpectedly changed.")
    return bytes(result)


def build_firmware(stock: bytes, profile: Profile) -> bytes:
    if not isinstance(profile, Profile):
        raise ValueError("A validated Profile is required.")
    validate_stock(stock)
    return _assemble_image(stock, profile, _asset("native.json"), _asset("adc_recipe.json"))


def build_file(stock_path: Path, output_path: Path, profile: Profile) -> Path:
    """Create a new local file. Never overwrite stock or an existing output."""
    stock_path, output_path = Path(stock_path).resolve(), Path(output_path).resolve()
    if stock_path == output_path:
        raise ValueError("The output must be different from the stock firmware file.")
    if output_path.exists() or output_path.is_symlink():
        raise ValueError("The output already exists. Choose a new filename.")
    data = build_firmware(stock_path.read_bytes(), profile)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("xb") as output:
        output.write(data)
    return output_path
