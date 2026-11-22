# Check and re-run this bundle

FlakeTrace commit: c5eff18f366edf94f7e76003db3903f1afadea44
Subject commit: e05e9c5e4be580691cc55a59f3256595393203a1

1. Check out FlakeTrace at the commit above, and the subject project at its commit.
2. Recount the evidence from the record alone:

       python -m eval.bundle verify 20261121T200523Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf

3. Re-run the kept sequence, the victim alone and the deletion checks:

       python -m runner replay 20261121T200523Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf --project <checkout of the subject>
