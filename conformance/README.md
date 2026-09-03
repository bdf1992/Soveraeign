# Phase-I Conformance Testbed

Status: `EXECUTABLE ORACLE · COVERAGE PROPOSED`

The conformance suite evaluates externally visible records, authority results,
receipts, and effects. It does not require a storage engine, framework,
transport, service topology, or internal API.

`oracle-controls.json` contains a good observation and a causally defeating
observation for each Phase-I requirement, and the same pair for every kernel
transition and discovery predicate `SPEC.md` states below the nine
(`conformance/kernel_predicates.py`, merged into one check table in
`requirements.py`). Those embedded observations test the oracle itself; they are
not participant scenarios. A control run must carry both polarities for every key
in that table. A participant run is held to the nine requirements plus whichever
kernel rows its own case file declares.

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

## How a report is read

The runner indexes observations by `case_id` before evaluating any of them, and refuses
a report it cannot read exactly as submitted rather than resolving the ambiguity itself:

- the report must be a JSON array of observation objects;
- every entry must carry a non-empty string `case_id`;
- every entry must carry an `observed` object;
- no `case_id` may appear twice.

The duplicate rule is the load-bearing one. Indexing used to be last-wins, so an honest
failing observation followed by a fabricated passing one under the same `case_id`
produced `SUITE PASS` with no signal that a choice had been made. A repeated `case_id`
now refuses the whole run: which observation counts is not the submitter's to decide.

The same reading applies to the case file, so a duplicated control id is refused too.

These are runner mechanics — the shape a report must have to be read at all. They do not
settle which document owns the observation crossing's fields; that question is open.

## Result meanings

- `PASS` — the observation contains no detected contract violation.
- `FAIL` — one or more semantic defects were observed.
- `INVALID` — the case or participant report cannot be evaluated. A whole run reports
  `SUITE INVALID` with the reason and exits non-zero when the report cannot be read.

Passing the bundled controls proves that the oracle distinguishes the included
positive and defeating narratives. It does not witness an implementation.
Implementation standing remains `BUILT` until an independent witness runs the
suite against real participant observations.
