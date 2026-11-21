# Check and re-run this bundle

FlakeTrace commit: db76288e9f0ca4bc7d25e7f4f3a43b99e90ce473
Subject commit: db76288e9f0ca4bc7d25e7f4f3a43b99e90ce473

1. Check out FlakeTrace at the commit above, and the subject project at its commit.
2. Recount the evidence from the record alone:

       python -m eval.bundle verify 20261121T152513Z-odfixture.DualFailureVictimTest#expectsStateTwo

3. Re-run the kept sequence, the victim alone and the deletion checks:

       python -m runner replay 20261121T152513Z-odfixture.DualFailureVictimTest#expectsStateTwo --project <checkout of the subject>
