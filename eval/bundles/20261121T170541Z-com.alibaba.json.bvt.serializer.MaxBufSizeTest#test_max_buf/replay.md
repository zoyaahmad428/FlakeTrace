# Check and re-run this bundle

FlakeTrace commit: 9a9707522d52c61f824e4a2ac6098262a74ab9c1
Subject commit: e05e9c5e4be580691cc55a59f3256595393203a1

1. Check out FlakeTrace at the commit above, and the subject project at its commit.
2. Recount the evidence from the record alone:

       python -m eval.bundle verify 20261121T170541Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf

3. Re-run the kept sequence, the victim alone and the deletion checks:

       python -m runner replay 20261121T170541Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf --project <checkout of the subject>
