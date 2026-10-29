# Third-party notices and research references

## Topre and REALFORCE

Topre and REALFORCE names identify the manufacturer and the tested compatibility target. This is an independent project and is not affiliated with or endorsed by them.

Original manufacturer firmware, modified firmware images, the official updater, and local firmware backups are not part of this repository. Users supply their own lawfully obtained, exact supported stock image. The project's license does not grant rights to manufacturer firmware or trademarks.

The builder reconstructs a device-specific compatibility routine locally from the user's stock input. The extracted manufacturer routine and its disassembly are not distributed as project source or payload data. Local reconstruction does not establish permission for further redistribution or resolve every firmware-license question.

## TopreRT

[TopreRT by rocketman2654](https://github.com/rocketman2654/TopreRT) was consulted during research. Its repository is licensed under AGPL-3.0; consult the upstream project for its current license and notices.

The public build does not redistribute the extracted 168-byte compatibility helper examined during development. A research reference does not itself make all independently written code a derivative work, and this notice is not a substitute for provenance review. Any future copied or adapted TopreRT code must be identified and handled under the applicable upstream terms before inclusion.

## Ghidra

[Ghidra](https://github.com/NationalSecurityAgency/ghidra) is an external development tool used to assemble and inspect the native payload. It is not bundled with the application and is not required for normal use of the supplied payload data. Its own license and third-party notices apply to that tool.

## Python and Tk

The host tools run on a separately installed Python interpreter and use the Python standard library, including Tk for the GUI. This repository does not bundle Python or Tcl/Tk. Those installations carry their respective licenses and notices.

## Project code

The MIT license in [LICENSE](LICENSE) applies to project-authored additions and tools. It does not cover a generated firmware image as a whole. No license statement in this repository authorizes redistribution of an original or generated manufacturer firmware image, and local generation does not establish permission under the manufacturer's firmware terms.
