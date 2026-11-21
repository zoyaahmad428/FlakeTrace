# Check and re-run this bundle

FlakeTrace commit: aaf69df8638c27ecb0a4eb0666439320a6332510
Subject commit: aaf69df8638c27ecb0a4eb0666439320a6332510

1. Check out FlakeTrace at the commit above, and the subject project at its commit.
2. Recount the evidence from the record alone:

       python -m eval.bundle verify 20261121T094724Z-odfixture.ConfigVictimTest#expectsDefaultMode

3. Re-run the kept sequence, the victim alone and the deletion checks:

       python -m runner replay 20261121T094724Z-odfixture.ConfigVictimTest#expectsDefaultMode --project <checkout of the subject>
