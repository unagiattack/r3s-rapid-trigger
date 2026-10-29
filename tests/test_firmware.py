"""Engine tests use invented bytes, never a distributed stock firmware image."""

from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import Mock, patch

from r3s_rt import firmware as fw
from r3s_rt.profile import KEYS, Profile, RAW_AMOUNTS


def synthetic_stock():
    data = bytearray([0xFF] * fw.STOCK_SIZE)
    data[4:196] = bytes(range(192))
    data[fw.PAYLOAD_END:] = b"Synthetic test trailer only!".ljust(28, b".")
    # Invented words exercise local copying and register bitfield transforms.
    for index, row in enumerate(fw._asset("adc_recipe.json")["words"]):
        struct.pack_into("<H", data, int(row["source"], 16) - fw.FLASH_BASE + 4, 0x8100 + index)
    struct.pack_into("<H", data, 2, fw.crc16(data[4:fw.PAYLOAD_END]))
    struct.pack_into("<H", data, 0, fw.crc16(data[2:]))
    return bytes(data)


class FirmwareTests(unittest.TestCase):
    def setUp(self):
        self.stock = synthetic_stock()
        self.native = fw._asset("native.json")
        self.recipe = fw._asset("adc_recipe.json")

    def build_synthetic(self, profile=None):
        return fw._assemble_image(self.stock, profile or Profile.default(), self.native, self.recipe)

    def test_crc_known_check_value(self):
        self.assertEqual(fw.crc16(b"123456789"), 0x6F91)

    def test_changed_packaged_assets_are_rejected(self):
        resource = Mock()
        resource.joinpath.return_value.joinpath.return_value.read_bytes.return_value = b'{"schema": 1}'
        with patch.object(fw.resources, "files", return_value=resource):
            for name in ("native.json", "adc_recipe.json"):
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "integrity check"):
                    fw._asset(name)

    def test_asset_line_endings_and_source_hash_are_portable(self):
        for name in ("native.json", "adc_recipe.json"):
            data = fw.resources.files("r3s_rt").joinpath("data").joinpath(name).read_bytes()
            self.assertNotIn(b"\r\n", data, name)
        source = Path(__file__).resolve().parents[1] / "native" / "rapid_trigger.asm"
        data = source.read_bytes()
        self.assertNotIn(b"\r\n", data)
        self.assertEqual(self.native["sourceSha256"], fw.sha256(data))

    def test_exact_stock_gate_rejects_synthetic_or_changed_files(self):
        with self.assertRaisesRegex(ValueError, "Unsupported stock firmware"):
            fw.validate_stock(self.stock)
        with self.assertRaisesRegex(ValueError, "size"):
            fw.validate_stock(b"short")

    def test_both_stock_checksums_are_checked_after_source_hash(self):
        with patch.object(fw, "STOCK_SHA256", fw.sha256(self.stock)):
            self.assertIsNone(fw.validate_stock(self.stock))
        corrupted = bytearray(self.stock)
        corrupted[300] ^= 1
        with patch.object(fw, "STOCK_SHA256", fw.sha256(corrupted)):
            with self.assertRaisesRegex(ValueError, "inner checksum"):
                fw.validate_stock(corrupted)
        corrupted = bytearray(self.stock)
        corrupted[-1] ^= 1
        with patch.object(fw, "STOCK_SHA256", fw.sha256(corrupted)):
            with self.assertRaisesRegex(ValueError, "outer checksum"):
                fw.validate_stock(corrupted)

    def test_local_adc_words_come_from_the_supplied_stock(self):
        image = self.build_synthetic()
        for row in self.recipe["words"]:
            original, = struct.unpack_from("<H", self.stock, int(row["source"], 16) - fw.FLASH_BASE + 4)
            actual, = struct.unpack_from("<H", image, int(row["address"], 16) - fw.FLASH_BASE + 4)
            self.assertEqual(actual, (original & ~row["clearMask"]) | row["setBits"])
        own_locations = {address for block in self.native["blocks"]
                         for address in range(int(block["address"], 16), int(block["address"], 16) + len(bytes.fromhex(block["hex"])))}
        self.assertTrue(all(int(row["address"], 16) not in own_locations for row in self.recipe["words"]))
        self.assertEqual(len(self.recipe["words"]), 21)

    def test_native_boundaries_vectors_trailer_and_checksums(self):
        image = self.build_synthetic()
        self.assertEqual(len(image), len(self.stock))
        self.assertEqual(image[4:196], self.stock[4:196])
        self.assertEqual(image[fw.PAYLOAD_END:], self.stock[fw.PAYLOAD_END:])
        self.assertEqual(fw.crc16(image[4:fw.PAYLOAD_END]), struct.unpack_from("<H", image, 2)[0])
        self.assertEqual(fw.crc16(image[2:]), struct.unpack_from("<H", image, 0)[0])
        writes = set(range(4))
        for block in self.native["blocks"]:
            offset = int(block["address"], 16) - fw.FLASH_BASE + 4
            writes.update(range(offset, offset + len(bytes.fromhex(block["hex"]))))
        for row in self.recipe["words"]:
            offset = int(row["address"], 16) - fw.FLASH_BASE + 4
            writes.update(range(offset, offset + 2))
        for hook in self.native["hooks"]:
            offset = int(hook["address"], 16) - fw.FLASH_BASE + 4
            writes.update(range(offset, offset + 4))
        self.assertTrue(all(a == b or index in writes for index, (a, b) in enumerate(zip(image, self.stock))))
        self.assertEqual(len(self.native["hooks"]), 50)

    def test_independent_keys_all_levels_and_enabled_flags(self):
        for level in range(1, 8):
            profile = Profile.default()
            for index, key in enumerate(KEYS):
                profile = profile.replace_key(key, enabled=index % 2 == 0, release_level=level, press_level=8 - level)
            image = self.build_synthetic(profile)
            for index, sensor in enumerate(fw.SENSORS):
                offset = fw.TABLE_ADDRESS - fw.FLASH_BASE + 4 + index * 12
                self.assertEqual(struct.unpack_from("<IHHI", image, offset),
                                 (sensor, RAW_AMOUNTS[level - 1], RAW_AMOUNTS[7 - level], int(index % 2 == 0)))

    def test_reserved_region_must_be_empty(self):
        changed = bytearray(self.stock)
        changed[fw.NATIVE_START - fw.FLASH_BASE + 4 + 0x6C] = 0
        with self.assertRaisesRegex(ValueError, "not empty"):
            fw._assemble_image(bytes(changed), Profile.default(), self.native, self.recipe)

    def test_branch_encodings_round_trip(self):
        for address, target in ((0x080157C8, 0x0801FC80), (0x0801FE88, 0x0801FE00),
                                (0x08010000, 0x07010004), (0x08010000, 0x09010002)):
            first, second = struct.unpack("<HH", fw.encode_bl(address, target))
            sign = (first >> 10) & 1
            i1, i2 = (~((second >> 13) ^ sign)) & 1, (~((second >> 11) ^ sign)) & 1
            delta = (sign << 24) | (i1 << 23) | (i2 << 22) | ((first & 1023) << 12) | ((second & 2047) << 1)
            if sign:
                delta -= 1 << 25
            self.assertEqual(address + 4 + delta, target)
        with self.assertRaises(ValueError):
            fw.encode_bl(0x08010001, 0x08020000)

    def test_build_file_preserves_stock_and_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            stock, output = Path(folder) / "stock.bin", Path(folder) / "output.bin"
            stock.write_bytes(self.stock)
            with self.assertRaisesRegex(ValueError, "different"):
                fw.build_file(stock, stock, Profile.default())
            output.write_bytes(b"keep")
            with self.assertRaisesRegex(ValueError, "already exists"):
                fw.build_file(stock, output, Profile.default())
            output.unlink()
            with patch.object(fw, "STOCK_SHA256", fw.sha256(self.stock)):
                self.assertEqual(fw.build_file(stock, output, Profile.default()), output.resolve())
            self.assertEqual(stock.read_bytes(), self.stock)
            self.assertEqual(output.read_bytes(), self.build_synthetic())


if __name__ == "__main__":
    unittest.main()
