# W23 replay gaps (M1's reproduction findings 1, 2, 5, 6): short design

**Status:** approved by M2 on 2026-11-22.

**Intent.** M1's independent W23 reproduction (PR #159) succeeded only after she worked out commands that the
bundle's `replay.md` should have given her. A reproducer must be able to verify and replay a bundle from its
`replay.md` alone, on Windows cmd or a Linux shell (FT009, claim G7).

**Goals:** (1) the commands use the bundle's real path from the FlakeTrace folder; (2) step 1 names a FlakeTrace
that can run them; (6) `--project` comes from the manifest's subject; (5) the OS row does not call the same Windows
build different. **Non-goals:** M3's README sections (findings 3, 4). **Anti-goal:** rewriting the 17 committed
bundles; their checksums protect them, and M3's README covers their old `replay.md`.

**Approaches.** (A, chosen) fix `_replay_md` and the OS comparison where they are; new bundles carry correct text.
(B) record a separate "verifier commit" in the manifest: a contract change, for something step 1's wording solves.
(C) regenerate the committed bundles: changes evidence after the fact.

**The how (decided).**
- Path: the output folder as given when it is relative, else `eval/bundles`; quoted (`#` is in every name). A line
  says to run from the FlakeTrace folder, with `py` instead of `python` on Windows.
- Step 1: any FlakeTrace commit that has `eval/bundle.py`, e.g. the current `main`; the bundle names the commit it
  was made with, and `replay` prints any difference.
- `--project`: `fixture` subject → its `module_path`; another repository → `"CHECKOUT"` or `"CHECKOUT/<module_path>"`
  with "CHECKOUT is your clone of <repository> at commit <sha>". No `<` or `>` inside a command.
- OS: `Windows-10-<build>` and `Windows-11-<build>` compare equal; anything else compares as text.

**Verification.** New tests fail first, then pass; the bundle and replay suites; a real F1 bundle whose `replay.md`
commands are run exactly as written from the repo root (verify OK, replay `same`).
