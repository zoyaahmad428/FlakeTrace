# FlakeTrace UI

The front end for the FlakeTrace POC. It walks nine steps: Source, Target, Diagnosis, Certificate,
Evidence graph, Repair, Verify, EvoSuite, Export. The Certificate step follows the certificate contract
in the project vault (`03-Design/certificate-contract.md`).

## Run

Double-click `start.cmd` on Windows, or run:

```
npm install
npm run dev
```

Open http://127.0.0.1:5174

## Two data modes (switch in the header)

**Offline demo** (default, needs nothing else running)
- `src/data/recorded.json` holds real responses from `flaketrace_backend.py`, recorded against a copy of
  `demo-project` with JDK 21 on 2026-09-10. The analysis, git history, patch diff and test runs are all real.
- A certificate replays each order N times. The first run of each order is the recorded run; the repeats reuse
  its outcome, because the harness is deterministic. The UI says this on the certificate.
- The Scenario panel on the Target step simulates weaker evidence (write not observable, nondeterministic
  replays, unstable build). Simulated certificates are labelled as simulated. Setting a small budget shows
  Budget exhausted.

**Live backend**
- Start the backend from the `POC` folder (one level up): `py flaketrace_backend.py`.
- Vite forwards `/api` to port 8765, so every replay and verification check runs for real.

## Known issue in the backend

Revert runs `git checkout -- .` in the project, which discards every uncommitted change there, not just the patch.

## Layout

```
src/lib/        api (live + offline), certificate rules and Wilson interval, evidence ranking, order simulator
src/state.tsx   app state and which steps are reachable
src/components/ header, step rail, trace diagram, shared UI pieces
src/screens/    one file per step
```
