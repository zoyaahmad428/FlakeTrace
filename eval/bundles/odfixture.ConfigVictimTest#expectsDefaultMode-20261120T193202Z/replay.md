# Replay

The exact command that produced this bundle (reconstructed from the record header when the CLI's own argv was not recorded):

```
diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode --records <home>/AppData/Local/Temp/w23-records
```

Once `python -m runner replay` exists (ADR-013 section 3), the one-command form is:

```
python -m runner replay <this-bundle-folder> --project <checkout of the subject at 07e0fd7aa630188aeac674209f063f17cd61aba5>
```
