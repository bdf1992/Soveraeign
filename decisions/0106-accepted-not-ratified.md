# 0106 · Accepted, not ratified

Status: `OWNER-DIRECTED · ACCEPTED POLICY`

Bdo said on 2026-09-10 that he did not like "ratified" as the name of the
standing an owner gives a finished result, and directed the replacement:
accepted. This record applies it and says what moved.

## Decision

**The standing an owner seat gives a finished, evidenced result is `ACCEPTED`.**
The participant lifecycle is `OPEN -> BUILT -> WITNESSED -> ACCEPTED`. The
record lifecycle in `SPEC.md` is `RECORDED -> ADMITTED -> ACCEPTED -> EFFECTIVE`.
The transition is `accept`, the receipt of it is an acceptance, and the root
seat's act is `ACCEPT`.

The word was already the doctrine. `decisions/0023` fixed the owner gate as
acceptance over an evidenced result and never approval to begin; acceptance
packets carried `owner_acceptance: ACCEPTED`; `STATUS.yaml` listed
`owner_accepted`. "Ratified" named the same act in a treaty word that said
nothing about who did it or what they did, and it carried two meanings at once:
the participant standing in `AGENTS.md` and the typed authority decision in
`SPEC.md`. One word, one act, both lifecycles.

## What moved

The replacement is global, at Bdo's direction, so the old word cannot return
through a record nobody re-reads. Every form moved with its case: ratified,
ratify, ratifies, ratifying, ratification, ratifiable, unratified, and the
identifiers built on them. Four files carrying the stem in their name were
renamed and every reference to them followed.

Three directories were held, and they are the whole exception: `archives/` keeps
superseded governing documents byte-identical by the directory boundary in
`AGENTS.md`; `lineage/` is immutable attributed evidence whose digests
`lineage/SOURCES.lock` verifies; and `witness/` is receipts, the probes they ran,
and the reports and README those receipts digest, which
`python scripts/sov_witness_layer.py records` recomputes from bytes and fails
when any address under `witness/` moves. The first pass renamed thirty-eight
files there and that check refused fifteen receipts, so the directory was
restored to the bytes the witnesses signed. All three are labelled as history,
so the old word there reads as history. `docs/` is a projection and was rebuilt.

Two acts in the seat etiquette collapsed into one name and were merged rather
than aliased: the old `RATIFY`, the one act that could raise standing to the top,
and `ACCEPT`, the owner's acceptance of a finished result, were the same act
described twice. `ACCEPT` now carries the standing ceiling `WITNESSED -> ACCEPTED`
and the sentence from `decisions/0023`.

Two status lines collided and were kept apart. `PROPOSED · DRAFTED AT OWNER
DIRECTION · RATIFICATION PENDING`, carried by `decisions/0020` and `0035` and
graded unsettled, renamed onto the line `0058`, `0059` and `0069` already carry,
which grades settled. `contracts/decision-standing.json` then held the same key
twice and the second reading won, so two questions that reach the owner vanished
from the docket, and `python scripts/sov_docket.py check` was the check that
caught it. The two records now read `PROPOSED · DRAFTED AT OWNER DIRECTION ·
OWNER ACCEPTANCE PENDING`, the crosswalk maps that line to `PROPOSED`, and the
owner-facing count is seventeen again. A rename that merges two vocabularies can
merge two standings; the crosswalk is where that shows.

One reading was made explicit rather than aliased. `STATUS.yaml` already carried
`OWNER_ACCEPTED_...` values recording the owner's acceptance of a charter or
document. Under the shared word those read as standing claims, which the
standing gate would refuse for want of a witness record. The gate now reads a
token preceded by `OWNER` as the packet gate's business, which
`scripts/sov_accept.py` audits, and says so in its docstring. It is the same act
taken over a document rather than a built claim.

## Derived state re-stamped, not re-reviewed

The capability map and the Node Interface were rebuilt by their own commands.
Eight diagrams declared source digests that moved and were re-stamped against
the sources they already read. The cold-start answers corpus changed bytes, so
the two fixtures pinning its digest now pin the new one. Clarity receipts for
every artifact the rename touched were re-recorded with `changed` set: the
reviewer read the diff, which is one word in each, and did not conduct a fresh
prose review. Anyone reading a clarity receipt dated today should know that.

## What would defeat this

A place where the two former meanings needed to stay apart: a typed authority
decision that is not an acceptance, or an acceptance that records no decision.
None was found in the rename. If one appears, the fix is a second word for that
case, never the return of the first.

## What still waits on Bdo

- Nothing on the name; it was his.
- Whether the bdos core and its engine, which carry the same standing
  vocabulary, follow in the same landing. This record binds Soveraeign.

## Residuals

1. `archives/` and `lineage/` keep the old word, by their own rules.
2. The clarity receipts re-stamped today certify the rename, not the prose.
