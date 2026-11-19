# Real cases — W26 (real-project validation)

One subfolder per real case from [[05-Testing/real-case-protocol]]. Each holds this project's
**own** artefacts for that case: the frozen `--order` file (with its checksum recorded in the
protocol doc), and a record of what was confirmed when. The analysed project's **source is
never committed here** — it is fetched by script at a pinned commit into a scratch folder
outside this repository, per the protocol's "Source" row and the project's licence/ethics rules
([[00-Meta/risk-register]]).

| Folder | Case | Status |
| --- | --- | --- |
| `fj03/` | FJ-03 (fastjson, `MaxBufSizeTest#test_max_buf`) | Steps 1-5 done (2026-11-19); steps 6-9 blocked on a real `runner/discovery.py` gap — see [[05-Testing/real-case-protocol]]'s Findings and [[00-Meta/risk-register]] |
