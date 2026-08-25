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

The Phase-I participant suite is expected to fail overall while open
requirements remain. Individual repairs may move one requirement to participant
`PASS` without changing the frozen scenarios or oracle. `BASELINE.md` records
the current grading; bounded build records preserve the evidence for each move.

- `PROD-I-2-BUILD.md` records the self-tested reconstruction repair.
