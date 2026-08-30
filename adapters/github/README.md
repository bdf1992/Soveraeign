# GitHub Registrar

The declared crossing between this node and the GitHub coordination surface. It has
two halves that never call each other: `export.py` reads and `apply.py` writes.
It extends the `GitHub` adapter row in `adapters/README.md` from source capture to
coordination capture: issues, their metadata blocks, labels, and pull requests.

Nothing else in the repository may call the GitHub API. Verification, projection,
transition judgement, and board survey read the registrar's export from disk and run
offline. That split is the point: a check that needs the network cannot run in the
day-zero budget, cannot run in a sealed CI job, and cannot be reproduced by a fresh
witness.

## Two crossings, declared separately

The registrar has a read half and a write half, and they are declared apart because they
carry different effect classes and different risks.

| Crossing | Module | Effect class | What it moves |
| --- | --- | --- | --- |
| `COORDINATION_CAPTURE` | `export.py` | `RECORD_LOCAL` | GitHub to disk: issues, bodies, labels, pull requests |
| `COORDINATION_WRITE` | `apply.py` | `EXTERNAL_WORLD` | disk to GitHub: label catalogue, merged-head retirement, and issue bodies |

The write half exists because the board was a projection nobody projected. Colours,
descriptions, and the containment tree were declared in the repository and never reached
the surface, so the surface drifted from its own contract with no way to close the gap
except by hand (`decisions/0044-github-coordination-write-crossing.md`).

## What it is and is not

The registrar is a **projection of a coordination surface in both directions**: it reads
what GitHub says, and it writes back only what a local declaration already determined.
Under `AGENTS.md`, Directory boundaries, an adapter may not own standing, ratification,
settlement, or hidden fallback, and it receives no authority by operating successfully.

- It **captures** what GitHub currently says, with exact provenance.
- It **never** decides standing. `scripts/sov_ticket.py` evaluates; the owning
  governing documents hold the answer.
- It **never** writes ratification. `CODEOWNERS` protects governed paths but is not
  itself the owner's judgement surface; ratification requires an explicit recorded
  root-seat action, not a label, bot, or repository write credential.
- Absence of GitHub produces a visible refusal, never a silent fallback to a cached or
  assumed board.

### `COORDINATION_CAPTURE` — `export.py`

| Field | Declaration |
| --- | --- |
| Data-boundary mode | `LOCAL_READ_ONLY` — issue and pull request text leaves GitHub inbound; nothing crosses outbound |
| Input projection | issue number, title, state, body, label names; the label catalogue's name, colour, and description; pull request number, title, state, head ref, body, draft flag, last update; branch names |
| Authority | none granted, none accepted |
| Effect class | `RECORD_LOCAL` on the capture; the crossing itself consumes a rate-limited external resource |
| Receipt | every export records source repository, captured-at timestamp, item count, and content digest |
| Refusal | `REGISTRAR_UNAVAILABLE`, `REGISTRAR_UNAUTHENTICATED`, `REGISTRAR_EMPTY` |

### `COORDINATION_WRITE` — `apply.py`

| Field | Declaration |
| --- | --- |
| Admitted actions | `LABEL_ADD`, `LABEL_REMOVE`, `LABEL_CREATE`, `BRANCH_DELETE`, `BODY_SET`. An action kind absent from that table is refused by name; the crossing never falls through to a generic GitHub call |
| Data-boundary mode | `DECLARED_PROJECTION_OUTBOUND` — label values are derivable from `.github/labels.yml` and `contracts/ticket-label-projection.json`; a body is authored in the repository and must satisfy `contracts/issue-metadata.schema.json` before it crosses. No payload bytes, no evidence, no repository source, no credential |
| Output projection | label name, colour, description; a merged pull request's head ref; an issue body in full |
| Authority | the invoking operator's, named in the receipt and scoped to this surface. The crossing grants none and accepts none. Labels take one owner approval per action; `BRANCH_DELETE` and `BODY_SET` each name a basis that `proofs.py` re-proves against live state immediately before the write |
| Effect class | `EXTERNAL_WORLD`. Writing is opt-in: without `--apply` the tool prints the plan and stops |
| Receipt | `.local/registrar/apply.receipt.json` records the crossing, target repository, start and finish, source export, every action, and each outcome. A body write additionally records the prior body's snapshot path and digest, and the replacement's digest |
| Counteraction | `.local/registrar/bodies-before/` holds each body as it stood immediately before its write, recorded by the proof rather than by the caller. A rewrite is reversible by writing the snapshot back; a label deletion is not, which is why only labels the catalogue explicitly retires may be deleted |
| Refusal | the capture refusals, plus `REGISTRAR_REFUSED` for an action no declaration derives, `BODY_BLOCK_REFUSED` for a replacement the ticket contract will not admit, `BODY_SOURCE_MISSING`, `BODY_SOURCE_EMPTY`, and `AUTHORITY_BASIS_UNKNOWN` |

What it will not do, by construction: open, close, comment on, assign, or milestone an
issue; label one outside the governed axes; land a body the ticket contract refuses or a
blank one; delete a label the catalogue does not name in its `retire:` section; write
standing, ratification, or settlement in any form. A label is a projection, and a
projection that starts deciding things is a second authority. Typing `standing:
WITNESSED` into a block is not witnessing it: the evidence rules in `AGENTS.md` decide
whether the claim is true, whoever is permitted to write the word.

`plan.py` renders the `sov:relations` block from a ticket's own metadata and plans the
containment edge. The relations half now has an executor in `BODY_SET`; the containment
edge still has none, and GitHub's native sub-issue link is set by hand.

## Operating it

```bash
python adapters/github/export.py --repo <owner>/<name> --out .local/registrar/tickets.json
python scripts/sov_ticket.py validate --export .local/registrar/tickets.json
python scripts/sov_ticket.py labels   --export .local/registrar/tickets.json --strict
python scripts/sov_ticket.py queue    --export .local/registrar/tickets.json --limit 20
```

Writing back runs from the same export, and always in two steps. The first prints the
plan; the second performs it.

```bash
python adapters/github/apply.py --repo <owner>/<name> --export .local/registrar/tickets.json
python adapters/github/apply.py --repo <owner>/<name> --export .local/registrar/tickets.json --apply
python adapters/github/apply.py --repo <owner>/<name> --export .local/registrar/tickets.json --only labels --apply
```

Then capture again and judge the result through the read path, which is independent of
the code that performed the write. A run that reports success and a re-capture that still
shows drift means the write did not do what it said.

The export lands under `.local/`, which is gitignored runtime state. A captured board
is an observation with a timestamp, not a record; committing one would create a second
copy of a surface that changes without us.

Authentication is whatever credential the `gh` CLI already resolves for the invoking
user. The registrar holds no credential, reads no token from the environment, and
records none in the export or the receipt.

## The write crossing

`apply.py` is the only module permitted to write to GitHub. It exists because a drift
report that nobody can act on is not a control surface, and because handing the owner
a finding without a recommended action moves the expensive half of the work onto them
(`decisions/0057-board-management-role.md`).

It is deliberately self-contained. The module holding write authority should be
readable in one file without following an import into shared plumbing, so it repeats
the eight-line `gh` runner rather than sharing one with `export.py`.

| Field | Declaration |
| --- | --- |
| Data-boundary mode | `OWNER_APPROVED_WRITE` — one approval per action, at the moment of the action |
| Admitted actions | `LABEL_ADD`, `LABEL_REMOVE`, `LABEL_CREATE`, `BRANCH_DELETE`, and nothing else |
| Authority | none held; an approval accompanies each action and expires with it |
| Effect class | `EXTERNAL_WORLD` |
| Receipt | one per attempt, recording the exact command, outcome, and reason code |
| Refusal | `NO_APPROVAL`, `ACTION_NOT_ADMITTED`, `MALFORMED_TARGET`, `CROSSING_UNAVAILABLE`, `CROSSING_REJECTED` |

```bash
python scripts/sov_board.py review
python scripts/sov_board.py apply --batch .local/board/batch.json --approve <id>,<id> --dry-run
python scripts/sov_board.py apply --batch .local/board/batch.json --approve <id>,<id>
```

Three things it will not do. It will not run without an approved action list, so no
schedule can drive it. It will not admit a fifth verb; closing an issue or a pull
request is a judgement and is reported for a human instead. It will not stop at the
first failure, because a partial run is the normal case and the receipt list is the
record of what actually happened.

The retired Phase-I blanket refusal no longer governs this crossing. The write half
remains `EXTERNAL_WORLD` and can act only inside its declared action table with the
invoking operator's explicit scoped authority and receipts; `OPEN-SEAMS.md` S9 records
the closure of the old contradiction.

## The MCP seam

An MCP server over this coordination surface is the same crossing with a different
transport. It is queued, not built. Two rules bind it in advance:

1. It exposes the registrar's declared projection and refusals — not the raw GitHub
   API. A tool that hands a model arbitrary GitHub write access has replaced a declared
   adapter with an undeclared one.
2. It is a transport, never a second authority path. An MCP call may capture, propose,
   and refuse. It may not settle, witness, or ratify.

The gateway seam that would host it is open work; see `decisions/0016-github-coordination-registrar.md`
and the deployment topology ticket on the board. Until a two-node crossing case exists,
the registrar stays a local read.
