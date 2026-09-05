# Disposition Lab test execution plan

Status: `EXPERIMENTAL · ISSUE #200`

Run the focused software suite first:

```bash
python -m unittest scripts.tests.test_sov_disposition -v
```

Then run the repository verifier:

```bash
python scripts/verify.py
```

Focused tests cover:

- deterministic replay;
- center plus variation reporting;
- insufficient-evidence standing;
- required model configuration;
- unknown-construct refusal;
- scale-bound refusal;
- empty-evidence refusal;
- explicit opt-in for unvalidated projections;
- report rebuildability;
- ledger tamper detection;
- cross-kind comparison refusal.

After software verification, execute `EXPERIMENT-01.md`. That experiment is the first measurement-quality trial and must not be replaced by green unit tests.
