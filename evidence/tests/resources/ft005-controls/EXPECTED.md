# FT005 controls: expected results

*Member 1, W21. Written on 2026-11-18 before the project was first compiled or run.*

Two controls for the static-overlap wording (FT005, ADR-010, claims ledger G3). In each, static
analysis finds an edge that is **not** why the victim fails. FlakeTrace must not call it the cause.

| Control | Polluter → victim | Why the victim really fails | Expected static evidence |
| --- | --- | --- | --- |
| 1. Write-then-restore | `RestoringPolluterTest#pollute` → `RestoringVictimTest#check` | `State.hidden`, set **through reflection** | One edge, on `controls.State#restored` (written twice, then restored); no edge on `State#hidden`; a `REFLECTION` observation on the polluter side |
| 2. Unrelated overlap | `TwoFieldPolluterTest#pollute` → `TwoFieldVictimTest#check` | `State.b` | Two edges at the same depth, `controls.State#a` first (by name) and `controls.State#b`; `shared_resource` is `State#a`, the one that does not matter |

Expected from a full `diagnose` of each victim: the polluter is found by reruns, and the resource
is described only as a static overlap, "a possible mechanism, not confirmed as the cause". Each
victim passes when run alone.
