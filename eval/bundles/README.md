# Evidence bundles (W23, ADR-013 §4, Interface 8)

Fixture bundles, committed. Each folder is one diagnosis as five files — `report.json`, `record.jsonl`,
`replay.md`, `environment.txt`, `manifest.json` (SHA-256 of the other four) — with personal paths removed.
`.gitattributes` keeps Git from changing their line endings, so the checksums hold on every machine.

| Case | Bundle | Made |
| --- | --- | --- |
| F1 (`odfixture.ConfigVictimTest#expectsDefaultMode`, polluter `ConfigPolluterTest#pollute`, `VERIFIED`) | `f1/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/` | 2026-11-21 by M2 with `--bundle`, from a clean checkout of `main` at `03ada56` (tool and subject `dirty: false`); Windows 11, JDK 21.0.9, Maven 3.10.0. Added with M3's agreement (this folder is M3's); also the W32 practitioner case |

Check one (from the repository root, at the commit in its `manifest.json`):

```
python -m eval.bundle verify eval/bundles/f1/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode            # M3's recount (W23, not built yet)
python -m runner replay eval/bundles/f1/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode --project fixtures/od-fixture
```

`replay` printed `verdict: VERIFIED -> VERIFIED same` (exit 0) on 2026-11-21. The remaining fixture bundles are
M3's to add (Interface 8, who does what, step 2).
