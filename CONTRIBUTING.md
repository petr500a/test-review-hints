# Contributing

Please include a small reproducible Python example and the expected hint.

The tool is advisory. New rules should document false-positive boundaries and should not execute the files they inspect. Run:

```powershell
python -m unittest discover -s tests -v
python -m test_review_hints.cli examples
```

Keep pull requests focused and do not include production data, secrets, or private repository paths.
