# GitHub Registrar

The single declared crossing between this node and the GitHub coordination surface.
It extends the `GitHub` adapter row in `adapters/README.md` from source capture to
coordination capture: issues, their metadata blocks, labels, and pull requests.

Nothing else in the repository may call the GitHub API. Verification, projection, and
transition judgement read the registrar's export from disk and run offline. That split
is the point: a check that needs the network cannot run in the day-zero budget, cannot
run in a sealed CI job, and cannot be reproduced by a fresh witness.

## Two crossings, declared separately

The registrar has a read half and a write half, and they are declared apart because they
carry different effect classes and different risks.

| Crossing | Module | Effect class | What it moves |
| --- | --- | --- | --- |
| `COORDINATION_CAPTURE` | `export.py` | `RECORD_LOCAL` | GitHub to disk: issues, bodies, labels, pull requests |
| `COORDINATION_WRITE` | `apply.py` | `EXTERNAL_WORLD` | disk to GitHub: label catalogue, containment edges, the rendered relations block |

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
- It **never** writes ratification. Owner judgement reaches the repository through
  `CODEOWNERS` review on `STATUS.yaml` and `decisions/`, not through a label or a bot.
- Absence of GitHub produces a visible refusal, never a silent fallback to a cached or
  assumed board.

### `COORDINATION_CAPTURE` — `export.py`

| Field | Declaration |
| --- | --- |
| Data-boundary mode | `LOCAL_READ_ONLY` — issue and pull request text leaves GitHub inbound; nothing crosses outbound |
| Input projection | issue number, title, state, body, label names; the label catalogue's name, colour, and description; pull request number, title, state, head ref, body |
| Authority | none granted, none accepted |
| Effect class | `RECORD_LOCAL` on the capture; the crossing itself consumes a rate-limited external resource |
| Receipt | every export records source repository, captured-at timestamp, item count, and content digest |
| Refusal | `REGISTRAR_UNAVAILABLE`, `REGISTRAR_UNAUTHENTICATED`, `REGISTRAR_EMPTY` |

### `COORDINATION_WRITE` — `apply.py`

| Field | Declaration |
| --- | --- |
| Data-boundary mode | `DECLARED_PROJECTION_OUTBOUND` — only values already derivable from `.github/labels.yml`, `contracts/ticket-label-projection.json`, and an issue's own metadata block cross outbound. No payload bytes, no evidence, no repository source, no credential |
| Output projection | label name, colour, description; the containment edge parent-to-child; an issue body's delimited relations block, and nothing outside those delimiters |
| Authority | the invoking operator's, named in the receipt and scoped to this surface. The crossing grants none and accepts none |
| Effect class | `EXTERNAL_WORLD`. Writing is opt-in: without `--apply` the tool prints the plan and stops |
| Receipt | `.local/registrar/apply.receipt.json` records the crossing, target repository, start and finish, source export, every action, and each outcome |
| Counteraction | `.local/registrar/bodies-before/` holds every body as it stood before the run. A rewrite is reversible from that snapshot; a label deletion is not, which is why only labels the catalogue explicitly retires may be deleted |
| Refusal | the capture refusals, plus `REGISTRAR_REFUSED` for an action no declaration derives |

What it will not do, by construction: open, close, comment on, assign, milestone, or
label an issue outside the governed axes; touch a body outside its delimiters; delete a
label the catalogue does not name in its `retire:` section; write standing, ratification,
or settlement in any form. A label is a projection, and a projection that starts deciding
things is a second authority.

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
