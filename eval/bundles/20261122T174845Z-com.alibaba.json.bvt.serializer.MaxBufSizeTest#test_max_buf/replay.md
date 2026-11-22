# Check and re-run this bundle

Made with FlakeTrace commit: ec5652b9ad763992d46012c8472266c674afd158
Subject commit: e05e9c5e4be580691cc55a59f3256595393203a1

1. Use any FlakeTrace commit that has eval/bundle.py (for example the current main); `replay` prints
   any difference from the commit above. CHECKOUT is your clone of https://github.com/alibaba/fastjson at commit e05e9c5e4be580691cc55a59f3256595393203a1.
   Run them from the FlakeTrace folder (on Windows, `py` instead of `python`).
2. Recount the evidence from the record alone:

       python -m eval.bundle verify "eval/bundles/20261122T174845Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf"

3. Re-run the kept sequence, the victim alone and the deletion checks:

       python -m runner replay "eval/bundles/20261122T174845Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf" --project "CHECKOUT/."
