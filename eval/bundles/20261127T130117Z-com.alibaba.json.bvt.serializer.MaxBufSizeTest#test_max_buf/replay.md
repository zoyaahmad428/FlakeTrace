# Check and re-run this bundle

Made with FlakeTrace commit: 1b2ebd70e5e94173a284460cbc99f918af6c2ded
Subject commit: e05e9c5e4be580691cc55a59f3256595393203a1

1. Use any FlakeTrace commit that has eval/bundle.py (for example the current main); `replay` prints
   any difference from the commit above. CHECKOUT is your clone of https://github.com/alibaba/fastjson at commit e05e9c5e4be580691cc55a59f3256595393203a1.
   Run them from the FlakeTrace folder (on Windows, `py` instead of `python`).
2. Recount the evidence from the record alone:

       python -m eval.bundle verify "eval/bundles/20261127T130117Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf"

3. Re-run the kept sequence, the victim alone and the deletion checks:

       python -m runner replay "eval/bundles/20261127T130117Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf" --project "CHECKOUT/."
