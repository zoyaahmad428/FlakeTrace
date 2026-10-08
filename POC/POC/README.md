# FlakeTrace POC

FlakeTrace diagnoses one order-dependent Java test: which earlier test leaves shared state behind, which
test trips over it, how reliably that order replays, and a patch that restores the state.

This is a proof of concept. The analysis is static (source level) and replays run through a small JDK
harness, not Maven in a clean container.

## What is in this folder

```
POC/
  flaketrace-ui/            the web UI (React + Vite). Start here.
  flaketrace_backend.py     local backend on port 8765. Only needed for Live mode.
  git_extractor_server.py   older, narrower backend. Not used by the UI.
  demo-project/demo-project Maven module with a planted order-dependent failure
  sample-dataset/sample     a tiny second Java project (Holder, ReaderTest, WriterTest)
```

## Requirements

| For | You need |
| --- | --- |
| The UI, offline demo | Node.js 20 or newer |
| Live mode | Python 3.10 or newer, and git |
| Replays and verification in Live mode | A JDK (`javac` and `java` on PATH). Tested with JDK 21 |
| EvoSuite generation | A JDK plus `EVOSUITE_JAR` pointing at `evosuite.jar` |

Maven is not needed.

## Option A: offline demo (UI only)

1. Open `flaketrace-ui`.
2. On Windows, double-click `start.cmd`. On macOS or Linux, run `npm install` then `npm run dev`.
3. Open http://127.0.0.1:5174

The first start downloads packages, so it needs internet once. The demo replays recorded real runs of
`demo-project`, so it works offline afterwards.

## Option B: live backend

Use two terminals.

1. In `POC`, start the backend:
   - Windows: `py flaketrace_backend.py`
   - macOS or Linux: `python3 flaketrace_backend.py`

   It should print `FlakeTrace backend → http://127.0.0.1:8765/` and whether a JDK was found.
2. Start the UI as in Option A.
3. In the UI header, switch to **Live backend**, then load **Demo project**.

Leave both terminals open while you use it.

## The planted bug

`UserCache.currentUser` is a public static field.

- `LoginTest#shouldLoginUser` writes it and never restores it (the polluter).
- `UserServiceTest#shouldRejectAnonymousUser` reads it and expects no user (the victim).

Each passes alone. Run `LoginTest` first and `UserServiceTest` fails. `SessionTest` resets the field, so
the whole module passes in declared order. See `demo-project/demo-project/README.md` for details.

## Before you use Live mode

- **Apply** writes the patch into `LoginTest.java`. **Revert** runs `git checkout -- .` in the demo
  project, which also discards any other uncommitted change there.
- `git_extractor_server.py` uses the same port as `flaketrace_backend.py`. Run only one, and the UI needs
  `flaketrace_backend.py`.
- Opening http://127.0.0.1:8765 directly shows an error, because the old single-page UI is not included.
  Use the UI on port 5174.

## Troubleshooting

| You see | Do this |
| --- | --- |
| "Backend not reachable" in Live mode | Start `flaketrace_backend.py` (Option B, step 1) |
| `py` or `python` not found | Use whichever exists: `py`, `python` or `python3` |
| "No JDK on PATH" | Install a JDK and reopen the terminal |
| The UI opens on a port other than 5174 | Another app has 5174. Use the address Vite prints |

## Changes made for sharing (2026-09-10)

- Both Python files now find `demo-project` next to the script instead of `/home/zoyaahmad`, so the
  folder works wherever it is unzipped.
- Added the missing `@BeforeEach` stub to `demo-project/demo-project/harness`. Without it, a patched
  `LoginTest` did not compile and Verify could never pass.
