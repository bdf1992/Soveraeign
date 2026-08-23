# GitHub Registrar

The single declared crossing between this node and the GitHub coordination surface.
It extends the `GitHub` adapter row in `adapters/README.md` from source capture to
coordination capture: issues, their metadata blocks, labels, and pull requests.

Nothing else in the repository may call the GitHub API. Verification, projection, and
transition judgement read the registrar's export from disk and run offline. That split
is the point: a check that needs the network cannot run in the day-zero budget, cannot
run in a sealed CI job, and cannot be reproduced by a fresh witness.

## What it is and is not

The registrar is a **read projection** of a coordination surface. Under
`AGENTS.md`, Directory boundaries, an adapter may not own standing, ratification,
settlement, or hidden fallback, and it receives no authority by operating successfully.

- It **captures** what GitHub currently says, with exact provenance.
- It **never** decides standing. `scripts/sov_ticket.py` evaluates; the owning
  governing documents hold the answer.
- It **never** writes ratification. Owner judgement reaches the repository through
  `CODEOWNERS` review on `STATUS.yaml` and `decisions/`, not through a label or a bot.
- Absence of GitHub produces a visible refusal, never a silent fallback to a cached or
  assumed board.

| Field | Declaration |
| --- | --- |
| Data-boundary mode | `LOCAL_READ_ONLY` — issue and pull request text leaves GitHub inbound; nothing crosses outbound |
| Input projection | issue number, title, state, body, label names; pull request number, title, state, head ref, body |
| Authority | none granted, none accepted |
| Effect class | `RECORD_LOCAL` on the capture; the crossing itself consumes a rate-limited external resource |
| Receipt | every export records source repository, captured-at timestamp, item count, and content digest |
| Refusal | `REGISTRAR_UNAVAILABLE`, `REGISTRAR_UNAUTHENTICATED`, `REGISTRAR_EMPTY` |

## Operating it

```bash
python adapters/github/export.py --repo <owner>/<name> --out .local/registrar/tickets.json
python scripts/sov_ticket.py validate --export .local/registrar/tickets.json
python scripts/sov_ticket.py labels   --export .local/registrar/tickets.json --strict
python scripts/sov_ticket.py queue    --export .local/registrar/tickets.json --limit 20
```

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
