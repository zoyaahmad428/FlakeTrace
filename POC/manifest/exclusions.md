# Case exclusions log
Every case attempted and why it was dropped. Kept for yield reporting.

| case_id | project | reason | stage |
|---|---|---|---|
| JI-01 | json-iterator/java | no single-predecessor order reproduces: 0 OD-relevant at package scope (210/134) and 0 across the full module (382). Suite-level or multi-predecessor effect outside the pairwise model | Hour 2 reproduction |
| JI-02 | json-iterator/java | no single-predecessor order reproduces: 0 OD-relevant at package scope (210/134) and 0 across the full module (382). Suite-level or multi-predecessor effect outside the pairwise model | Hour 2 reproduction |
| JI-03 | json-iterator/java | no single-predecessor order reproduces: 0 OD-relevant at package scope (210/134) and 0 across the full module (382). Suite-level or multi-predecessor effect outside the pairwise model | Hour 2 reproduction |
| JI-04 | json-iterator/java | no single-predecessor order reproduces: 0 OD-relevant at package scope (210/134) and 0 across the full module (382). Suite-level or multi-predecessor effect outside the pairwise model | Hour 2 reproduction |
| (pre-ID) DateTest5_iso8601.test_date | alibaba/fastjson | shared fixing PR 2148 with FJ-01, not an independent root cause; replaced by MaxBufSizeTest.test_max_buf | Hour 1 selection |
| OR-01..04 (scope note) | j256/ormlite-core | reproduced only after widening past the frozen >300 package restriction, which returned 0/4; retained and disclosed, not excluded | strengthening iteration |
