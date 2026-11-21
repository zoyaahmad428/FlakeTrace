# Check and re-run this bundle

FlakeTrace commit: 03ada56a77e7939fc2de493e3cb50d62c18aebc1
Subject commit: 03ada56a77e7939fc2de493e3cb50d62c18aebc1

1. Check out FlakeTrace at the commit above, and the subject project at its commit.
2. Recount the evidence from the record alone:

       python -m eval.bundle verify 20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode

3. Re-run the kept sequence, the victim alone and the deletion checks:

       python -m runner replay 20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode --project <checkout of the subject>
