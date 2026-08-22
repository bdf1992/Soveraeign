# Phase-I Conformance Testbed

Status: `EXECUTABLE ORACLE · COVERAGE PROPOSED`

The conformance suite evaluates externally visible records, authority results,
receipts, and effects. It does not require a storage engine, framework,
transport, service topology, or internal API.

`oracle-controls.json` contains a good observation and a causally defeating
observation for each Phase-I requirement. Those embedded observations test the
oracle itself; they are not participant scenarios.

`scenarios.json` freezes one strategy-neutral participant narrative for each
requirement. A real participant binds by executing those narratives and
producing a JSON document with the same case IDs and an `observed` object for
each case:

```bash
python conformance/run.py
python conformance/run.py --cases conformance/scenarios.json \
  --observations path/to/participant-observations.json
```

The second form does not trust a participant's pass/fail claim. The runner
derives defects from the observation records.

## Observation contract

Every participant observation must contain:

```json
{
  "case_id": "CONF-I1-POS",
  "observed": {}
}
```

The requirement-specific fields are demonstrated in `oracle-controls.json`. Values are
logical evidence summaries and addresses; they are not prescribed storage
schemas. A participant may attach richer telemetry, but the oracle considers
only contract fields.

## Result meanings

- `PASS` — the observation contains no detected contract violation.
- `FAIL` — one or more semantic defects were observed.
- `INVALID` — the case or participant report cannot be evaluated.

Passing the bundled controls proves that the oracle distinguishes the included
positive and defeating narratives. It does not witness an implementation.
Implementation standing remains `BUILT` until an independent witness runs the
suite against real participant observations.
