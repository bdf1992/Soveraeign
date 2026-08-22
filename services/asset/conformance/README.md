# Asset Service Conformance Binding

The observation adapter runs the current reference participant against the
Phase-I scenario shapes without pretending missing behavior exists.

```bash
PYTHONPATH=services/asset/src \
  python services/asset/scripts/conformance_observations.py > /tmp/asset-observations.json

python conformance/run.py \
  --cases conformance/scenarios.json \
  --observations /tmp/asset-observations.json
```

The current baseline is expected to fail. That failure is the implementation
work surface: repair the participant while keeping the scenarios and oracle
frozen. `BASELINE.md` records the observed defects.
