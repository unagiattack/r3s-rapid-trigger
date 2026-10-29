# Native implementation and stock boundary

`rapid_trigger.asm` contains the project's eight-key Raw-count RT implementation,
transaction staging, setting-change guards, scanner adapters, and diagnostics.
These are the project's authored additions. The source uses a small assembly
listing format: `.org`, `.align4`, `.word`, labels, and `width|instruction` rows.
Its addresses describe the one supported stock firmware; they are not portable
to arbitrary R3-series firmware or hardware.

The original development workspace contained an ADC compatibility routine whose
MMIO sequence and delay loop were derived from manufacturer code. That routine's
decoded manufacturer instructions and opcodes are **not distributed** here.
Instead, 21 rows use `.stock16 source_address clear_mask set_bits`. At local build
time, the Python engine reads each word from the user's exact stock file and
changes only the stated register fields. The delay loop is copied with its
relative branch offset preserved. The surrounding bounded-polling wrapper,
failure return, and successful-sample tag are authored here.

`r3s_rt/data/native.json` contains compiled bytes for the authored rows only.
`r3s_rt/data/adc_recipe.json` contains addresses and register masks, with no stock
instruction bytes. `hooks.json` lists hook addresses and authored destinations;
it contains no original opcode anchors or reverse-patch ledger.

The build accepts only stock SHA-256
`c210e9b0447fa47047974a188f2b1e24b62b80dcc2443daa7d8f878823000da9`.
With default settings, this local derivation reproduces the previously tested
eight-key output byte for byte, SHA-256
`1a502cea7eba942c82cef4efaa89b4f3e9c025b6d1760bd69c9ef9f7276782ca`.
No stock or generated firmware file is included in the repository.

The project's license covers its authored material. Manufacturer code supplied
locally remains outside that license. Local derivation is a technical packaging
boundary, not a claim that every manufacturer's license permits modifications
or redistribution. TopreRT was consulted as a reference during research; its
helper implementation was not adopted in this accepted native implementation.

## Optional native rebuild

The installed application uses the packaged authored bytes and needs only the
Python standard library. Native development additionally requires Ghidra's ARM
Thumb assembler and Java. Use `AssembleNative.java` as a Ghidra post-script in an
isolated, zero-filled binary program covering `0x0801e000..0x08020000`, processor
`ARM:LE:32:Cortex`. Pass the absolute source path and an output directory as the
two script arguments. The script reserves `.stock16` addresses without emitting
or reading manufacturer instructions. It produces `native-listing.txt`.

Then run:

```console
python tools/export_native.py --listing /path/to/native-listing.txt
python -m unittest discover -s tests
```

The exporter validates source row addresses and widths, omits every `.stock16`
word, and records the source hash. The runtime also pins both packaged JSON
asset hashes in `r3s_rt/firmware.py`; after an intentional native change, review
and update those hashes before running the tests. It cannot assemble or distribute a complete
firmware image. Review native changes and perform appropriate device testing
before relying on a rebuilt implementation.
