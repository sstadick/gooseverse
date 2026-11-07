# Gooseverse

Read `.agents/skills/working-with-goose/SKILL.md` before changing Goose examples
or shared conventions. README.md is the public catalog and the source of the
programs executed by `python3 tests/examples.py`.

Keep package links and examples on moving branches. Do not add package version
pins, release tables that need synchronized bumps, submodules, or lockfiles here.
Each package owns its releases and reproducible dependency choices.

Only list public projects. Do not copy private automation reports, local machine
paths, credentials, or unpublished project information into this repository.

Run `python3 tests/examples.py` after changing the catalog's Goose examples.
The test uses temporary working directories because the I/O example writes a
file. Never replace an actual assertion with a check that a program merely ran.
