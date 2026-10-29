# Contributing

Issues, documentation corrections, and focused code changes are welcome. Keep public discussion and source text in English so findings are useful across regions. Clear examples and reproducible observations are more useful than polished prose.

## Keep firmware local

Do not commit or attach manufacturer firmware, generated `.rfb` files, the manufacturer updater, extracted manufacturer routines, disassembly, or firmware backups. Use your own lawfully obtained supported stock image for local verification. Keep that file and all generated firmware outside version control.

Do not remove the stock-file identity check to support another target. A new model or revision needs its own reviewed layout, code/RAM assumptions, configuration paths, input behavior, and recovery evidence.

## Reporting behavior

Include the project commit, operating system, Python version, keyboard model, stock-input hash, profile settings, global APC selection, and exact reproduction steps. Say whether you observed normal key events, Raw sensor values, or only a game-level effect. Record whether the issue followed boot, USB reconnect, sleep/wake, or a configuration change.

Do not include serial numbers, manufacturer firmware, or private filesystem paths. Redact screenshots and local logs before sharing them. The app does not read the installed firmware, so distinguish a known generated file from an independently confirmed installed version.

## Source changes

- Keep changes small and explain the user-visible effect.
- Preserve the stock path for disabled and unsupported keys.
- Preserve transactional owner checks, configuration-generation checks, and frame-validity checks.
- Treat input validation and patch-boundary checks as part of the builder's contract.
- Add meaningful regression coverage for a changed behavior or a reproduced fault.
- Use physical tests for claims about actual timing, noise, USB lifecycle behavior, or hardware recovery.
- State the source and license of any third-party code before adding it. Consulting a project and copying its implementation are different provenance claims.

Use the test commands documented by the repository's current development configuration. Tests that need a stock firmware image should accept a private local path and must not embed that image or print private data. Include the relevant results with a pull request; historical test counts are not a substitute for running the current checks.

## Native payload changes

The usual application workflow uses the supplied project-authored payload data. Native payload changes require the documented development toolchain and a fresh export of that data. Do not edit encoded payload bytes without an accompanying source change and reproducible verification.

An output that matches a known local artifact is useful evidence, but does not establish compatibility with another keyboard. Describe exactly which host tests and hardware checks you completed, and leave untested claims explicit.

## Licensing

Project-authored code is governed by [LICENSE](LICENSE). Follow [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for research references and third-party material. Manufacturer firmware is not licensed by this repository. Do not add material whose redistribution terms are unknown.
