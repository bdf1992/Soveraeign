# Acceptance packets

One finished result per file, presented to the seat one edge up.

A packet is not a question and not a request for permission. The work behind it
is already done; the owner seat reads the claim, runs the command, and answers
`ACCEPT`, `REJECT`, `STRIKE`, or `REDIRECT`. Nothing here holds standing — a
standing change lands in the document that owns it, by an ordinary edit, after
the action is recorded.

```
python scripts/sov_accept.py queue          what is waiting, and on which seat
python scripts/sov_accept.py present A1     read one result
python scripts/sov_accept.py present A1 --run   read it and run its demo
python scripts/sov_accept.py accept A1 --seat seat:root --actor urn:soveraeign:actor:bdo
python scripts/sov_accept.py rulings        defaults taken without asking
python scripts/sov_accept.py audit          fails if anything waits without a reason
```

## What may be presented

A claim that binds a seat other than the one presenting it. A seat's own
execution choices are its own and are refused if presented upward
(`SELF_DIRECTION_PRESENTED`).

## Where it goes

To `owner_seat` of the presenting seat, from `contracts/seat-registry.json`, and
nowhere else. Ownership does not chain: a worker presents to its orchestrator,
never past it to the root. The accepting seat must also settle the claim's type,
so a `VERIFICATION`-only seat cannot accept a `JUDGEMENT` claim.

## Shape

`contracts/acceptance-packet.schema.json`. The two fields that carry the weight:

- **visible_result.demo** — a command the reader can actually run. If the result
  cannot be shown, it is not finished.
- **what_could_defeat_it** — the strongest known failures. An empty list is
  refused. So is a residual left out to make the packet look cleaner.

## The rules behind it

`contracts/acceptance-policy.json`, `decisions/0028-acceptance-not-approval.md`,
and `decisions/0020-owner-seat-topology.md` for what an owner is.
