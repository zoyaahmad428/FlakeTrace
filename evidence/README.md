# evidence/ — resource evidence (Member 1)

**Owner:** Member 1 · **State:** not started (2026-10-09)

Finds the shared resource a polluter writes and a victim reads, from **compiled bytecode
only** — the target project's source is never modified and no application logs are needed.
Contract: [docs/contracts/interfaces.md](../docs/contracts/interfaces.md) (Interface 2).

## Iteration 1 scope

| Resource kind | Bytecode signal | Fixture case |
| --- | --- | --- |
| `static-field` | `putstatic` in polluter, `getstatic` in victim (incl. through called methods, `setUp`, `<clinit>`) | F1 (`Config.mode`), F3 (`Toggles.flagA/flagB`) |
| `system-property` | `System.setProperty(key, …)` in polluter, `System.getProperty(key)` in victim | F2 (`odfixture.turbo`) |

Out of Iteration 1: filesystem paths (Iteration 2), runtime instrumentation (see
[ADR-001](../docs/03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation.md)).

The POC's `extract_static.py` (javap-based getstatic/putstatic extraction with bytecode offsets)
is the reference idea; per the vault, the code itself does not carry over.
