# Diagram provenance: eight of eight views were stale

Observed 2026-08-24 on `feat/federation-harness-and-hardening`, working tree
uncommitted and shared with other live sessions.

Standing: this is a report. It holds no standing, settles nothing, and
witnesses nothing. Every check below is a self-test run by the same session
that made the change.

## What was claimed

`reports/2026-08-23-stack-certification.md` recorded "four of six diagrams are
stale and nothing reports it", and named refreshing four `source_digest` values
as the next bounded action. `diagrams/README.md` specified the digest so "a
stale diagram is detectable rather than merely suspected", then deferred the
check to whenever the views became generated rather than authored.

## What was observed

There are eight views, not six. When the check was made executable, **all eight
graded stale**: five of the six declared sources had moved
(`SPEC.md`, `CLASSIFICATION.md`, `STATUS.yaml`, `PRD.md`,
`services/console/CHARTER.md`); only `CONTRACT.md` still matched.

Two views had been stamped against `CLASSIFICATION.md` and `STATUS.yaml`
digests that match no commit in the branch's history, so those readings could
not be reconstructed and the views were re-read against the current files
instead of diffed.

The drift was not only digests. Four views cited retired `O<n>` decision
identifiers (O3, O7, O9/O10, O10, O11, O14) that `decisions/0033` retired and
`decisions/0024` had already ruled on. Beyond that:

- `service-map.md` drew three services. There are eight. It also stated "only
  Asset Service has an implementation"; Record is built and self-tested and
  Console's continuity path is built.
- `crossing-topology.md` and `crossing-typology.md` both stated that no adapter
  executes and that no crossing is built on both ends. `adapters/ollama/invoke.py`
  executes a model against the local runtime, and `services/console/` reads the
  Record Service journal — as a Python package import, not as a passage through
  a declared service contract, so that crossing pays none of the four
  obligations the typology says every crossing owes. That is the gap
  `services/gateway/CHARTER.md` was chartered to close.
- `standing-transition.md` stated that `CLASSIFICATION.md` and `SPEC.md` await
  owner ratification, citing retired identifiers. `STATUS.yaml` records both
  accepted while both headers still read `PROPOSED`. The view now reports that
  without ruling on it. **Corrected after first writing:** this report initially
  called the `PROPOSED` headers a defect. That is wrong for `SPEC.md`. An
  acceptance field names the version Bdo accepted, and `STATUS.yaml` states
  directly that SPEC.md moved after that acceptance under `decisions/0034`,
  which sits in `unruled_proposals`. The header and the field describe different
  versions of the document, and flipping the header would claim a ratification
  nobody gave. `CLASSIFICATION.md` carries no equivalent note, so its header may
  or may not be stale; that is open.
- `requirement-lifecycle.md` cited a `STATUS.yaml` field that no longer exists
  and stated Phase-I exit as "two bindings". `PRD.md` now says one human-facing
  binding and two materially different model bindings — three in total.

One unrelated drift surfaced while reading: `services/registry/` has a charter
and a thirteen-operation manifest, `scripts/sov_service.py check` counts eight
manifests, and the table in `services/README.md` listed seven. The row was
added.

## What changed

| Path | Change |
| --- | --- |
| `scripts/sov_diagrams.py` | new: `grade`, `stamp`, `selfcheck` |
| `scripts/tests/test_sov_diagrams.py` | new: 13 tests |
| `scripts/sovverify/checks.py` | new check `diagram provenance` |
| `diagrams/*.md` | eight views repaired and restamped |
| `diagrams/README.md` | the manual-read paragraph replaced by the executable check |
| `services/README.md` | `registry/` row added |
| `CLAUDE.md` | repository snapshot re-observed |
| `docs/documentation.html`, `docs/surface.html` | regenerated |

`stamp` records a re-reading and cannot perform one. Run over an uncorrected
view it would launder a stale diagram into a current-looking one, which is the
failure the digest exists to prevent. The docstring says so and `grade` remains
the gate.

## Checks run

- `python scripts/sov_diagrams.py selfcheck` — 6/6 declared cases, including
  four defeating ones.
- `python scripts/sov_diagrams.py` — 8 graded, 0 stale or invalid.
- `python -m unittest` on the new module — 13 passed.
- `python scripts/lint.py` — pass, 0 named debt.
- `python scripts/verify.py` — 29 checks pass, `SILVER` at about 8.4 s.

## Residuals

- The grade is `SILVER` and the budget for `GOLD` is 6 s. Almost all wall time
  is the single `repository tooling tests` check, which runs 694 tests inside
  one concurrent slot. Recovering `GOLD` means changing the shape of the gate,
  not tuning a test, and it was left alone.
- `services/asset/KNOWN-GAPS.md` still reads "No Model Binding or Model Adapter
  participant exists". As asset-participant phrasing that may still be right;
  as a repository-wide reading it is stale. Not repaired — it belongs to the
  asset domain.
- Decision-record standing has no machinery on this branch.
  `contracts/decision-standing.json` and `scripts/sov_docket.py` do not exist
  here; `.local/registrar/*.pulls.json` carries a pull-request body describing
  forty decision records under twenty-two distinct status strings, nine of whose
  status lines read pending while `STATUS.yaml` already answers them. The
  `CLASSIFICATION.md` header question above is one symptom of that, and a header
  edit is not the fix.
- The check grades whether a view still reads the bytes it declares. It says
  nothing about whether the drawing was ever right, and no independent
  participant has read these eight repairs.
