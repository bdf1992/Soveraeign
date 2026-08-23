# Console Service Charter

Status: `PROPOSED SERVICE BOUNDARY · NOT IMPLEMENTED`

## Role

The Console Service is a sibling of the Asset Service and the Proofing Service
inside a local Soveraeign Node. It governs the operator-facing session: what
needs an operator's attention, what an operator prefers, what is waiting on a
human right, and what has happened across the node's services. It owns the
records behind five operator surfaces:

1. notifications — addressed inputs telling an operator that a record,
   receipt, mention, or pending right concerns them;
2. settings — typed, scoped operator and node preferences;
3. dashboards — declared projections over receipts, events, standing, and
   judgement spend for operators holding an administrative scope;
4. human-in-the-loop and human-on-the-loop work — judgement requests that queue
   without blocking, and a watched activity stream from which an operator may
   counter an effective record through the kernel;
5. activity reporting — a declared projection over event envelopes and receipts
   emitted by every service in the node, and later by other nodes through a
   governed crossing.

The operator experience is threaded and domain-driven: a channel per domain or
purpose, a thread per bounded piece of work, attributed posts by human and
model operators in the same thread. That experience is a projection of the
records below. It does not own asset payloads, proofing decisions, authority,
standing, or settlement, and it never becomes a private authority system.

## Relationship to Phase-I requirements

- `PRD.md` two-binding proof and `bindings/README.md` require a human-facing
  binding that exposes state, choices, authority, provenance, and receipts
  intelligibly. The Console Service is the domain that binding renders.
- `PRD.md` PROD-I-3 (Cross): a human post and a model post in one thread are
  one crossing through the same record.
- `PRD.md` PROD-I-6 (Founder judgement budget): judgement requests queue
  without blocking operation; the dashboard reports where judgement was spent
  and which rights remain pending.
- `PRD.md` PROD-I-4 (Gate and retract): the activity view is where an operator
  on the loop sees an effective record and counters it through the kernel.
- `SPEC.md` Projection rule: dashboards and activity views are rebuildable
  projections whose every value resolves to authoritative records.
- `PRD.md` non-goal "a graphical production interface": the Phase-I Console is
  a local operator console proving parity and judgement accounting. It is not a
  production GUI claim, and no binding implementation is admitted until the
  transition contract is frozen or Bdo authorizes a provisional target.

## Owned domain records

- operator session — one operator's continuity: binding, opened and closed
  times, active thread, unread cursor;
- channel — a named domain-driven container for threads;
- thread — a bounded conversation in a channel, optionally pinned to an exact
  operation, record, or asset version address;
- post — one attributed turn in a thread by a human or model actor, with a
  content address and digest; a post that proposes enters as a kernel
  Proposal;
- notification — an addressed input to an operator naming its source record
  address and digest, its kind, and its acknowledgement;
- judgement request — a queued request for a judgement-typed right, with loop
  mode, requested authority type, the operation it conditions, and a
  `resolution_id` back-reference to its judgement resolution;
- judgement resolution (proposed) — the answer record for one judgement
  request: the resolver, the grant checked at the transition, the decision, a
  rationale address and digest, and its receipt; the only console record whose
  standing is expected to reach `RATIFIED`, and only by an appended event;
- operator setting — a typed, scoped preference held by an operator or by the
  node, with the authority required to change it;
- projection view — a declared dashboard or activity view with its source
  addresses, omissions, rebuild operation, and rebuild time;
- console receipt and history.

Proposed initial lifecycles (service policy awaiting owner ratification; they
do not replace the shared `RECORDED`, `ADMITTED`, `RATIFIED`, and `EFFECTIVE`
standings):

```text
operator session:  OPEN → CLOSED
thread:            OPEN → ARCHIVED
judgement request: QUEUED → RESOLVED | WITHDRAWN | EXPIRED
notification:      ISSUED → ACKNOWLEDGED
```

Proposed loop modes for a judgement request:

```text
IN_LOOP  the conditioned operation stays UNRESOLVED until a human right resolves it
ON_LOOP  the operation proceeds; the human watches and may counter through retraction
```

## Integration with sibling services and the kernel

The Console Service:

1. reads event envelopes and receipts from the Asset Service, the Proofing
   Service, and the kernel through a declared read-only crossing; it never
   writes their state;
2. emits a notification as a `SYSTEM` actor event when an operator is
   mentioned, assigned, asked for judgement, or named on a receipt outcome or
   counteraction; every emission carries a receipt;
3. records a judgement request when an operation's required authority type is
   `JUDGEMENT` and no live grant covers it; the conditioned operation receives
   an `UNRESOLVED` receipt and other operation continues; reach (proposed):
   the request emits a `JUDGEMENT_REQUESTED` notification with delivery
   `LOCAL` whose recipient is the owner; Phase I has no push, so the owner
   pulls the pending list from an operator session through the Human Binding;
4. resolves a judgement request only through a typed, scoped, live human
   `JUDGEMENT` grant checked at the transition; a model attempt is `REFUSED`;
   `resolve-judgement` (proposed) is the `SPEC.md` `ratify` transition row —
   preconditions: proposal admitted and a live matching grant; refusals:
   `AUTHORITY_REFUSED` or `STALE_STATE` — in which the request's question is
   the Proposal being ratified and the answer lands as a judgement resolution;
5. stores operator settings as records that condition projections and
   notification routing only; a setting never grants capability or authority;
6. rebuilds dashboard and activity projections from authoritative records on
   request; a projection-originated edit returns as a proposal through the
   transition contract;
7. refuses external delivery of a notification (email, push, chat platform)
   and cross-node activity as `UNCONFIGURED` with a receipt until a separate
   decision admits the effect;
8. never rewrites a post, notification, or judgement request; corrections are
   new records or counter-records.

Authority stays where the kernel puts it: the Console Service surfaces pending
rights and spent judgement; it does not hold, infer, or delegate a right.

## Human and model participation

Humans and models operate the same console through different bindings:

- both open sessions, read threads, post, and receive notifications;
- a model post that claims anything is a Proposal standing `RECORDED`;
- a human holding a live `JUDGEMENT` grant may resolve a judgement request; a
  model may draft a recommendation into the thread but may not resolve;
- machine verification authority may settle checkable dashboard predicates
  (counts, digests, rebuild equality) but cannot ratify a judgement request;
- an administrative dashboard requires a scoped grant to read; holding it does
  not grant the right to change what it shows;
- every open, post, request, resolution, acknowledgement, setting change, and
  rebuild returns a receipt.

### First slice: the owner's judgement surface (proposed)

`OPEN-SEAMS.md` S12 records the owner's input of 2026-08-23: Bdo will rarely
interact with GitHub, so a code-owner review click cannot be the owner's
ratification surface. The first console slice is therefore the surface through
which the owner receives a judgement request, answers it, and has the answer
land as a record that can carry `RATIFIED` standing. It has three legs:

- reach — `request-judgement` records the judgement request, the conditioned
  operation receives an `UNRESOLVED` receipt, and a `JUDGEMENT_REQUESTED`
  notification with delivery `LOCAL` is addressed to the owner as its
  recipient; Phase I has no push, so the owner pulls the pending list from an
  operator session through the Human Binding;
- answer — the owner invokes `resolve-judgement` through the Human Binding;
  the console realizes it as the `SPEC.md` `ratify` transition, with the
  request's question as the Proposal being ratified;
- land — a judgement resolution record carries the resolver, the grant
  checked, the decision, a rationale address, its receipt, and the
  `UNRESOLVED` receipt it answers (`unresolved_receipt_id`); its standing
  reaches `RATIFIED` by an appended event, never by overwrite; the conditioned
  operation receives a successor receipt whose `prior_receipt_id` names its
  `UNRESOLVED` receipt.

Target: a local CLI over the Python API, the Local surface row of
`ENGINEERING.md` (Python API and CLI; human and model bindings use the same
kernel operations). No HTTP and no UI framework. This is not a GUI claim; it
is the smallest Human Binding the owner can actually use, and every effect in
it is `RECORD_LOCAL`. Nothing in this slice is implemented: O18 gates
`console_implementation`, not this charter text, and the slice remains a
proposal until O18 is ruled and a logical spec and defeating fixtures exist.

## Initial proving narrative

From a clean local checkout:

1. open one human operator session and one model operator session;
2. open a channel for the asset domain and a thread pinned to an exact asset
   version address;
3. let the human and the model each post in the thread; reconcile the two
   receipts as the same transition; show the model post standing `RECORDED`;
4. let the model mention the human; observe the issued notification resolving
   to the post address and digest;
5. reach: let the model attempt an operation whose required authority is
   `JUDGEMENT`; observe an `UNRESOLVED` receipt, a `QUEUED` judgement request,
   and a `JUDGEMENT_REQUESTED` notification with delivery `LOCAL` addressed to
   the human operator, while an unrelated operation still commits; pull the
   pending list through the Human Binding and show the request on it;
6. let the model attempt to resolve the request; observe `REFUSED`;
7. answer: let the human invoke `resolve-judgement` through the Human Binding
   under a live `JUDGEMENT` grant; observe the `ratify` transition check the
   grant against the request's Proposal;
8. land: observe the judgement resolution record, its `RECORDED` event and the
   appended `RATIFIED` event, its receipt, a successor receipt for the
   conditioned operation whose `prior_receipt_id` names the `UNRESOLVED`
   receipt, and the `JUDGEMENT_RESOLVED` notification whose `recipient_id` is
   the requesting model operator;
9. change a human setting; show it alters notification routing and changes no
   authority check;
10. rebuild the admin dashboard and the activity view from receipts; show every
    value resolves to a source address and digest and that a second rebuild is
    identical;
11. let the human counter one effective record from the activity view through
    kernel retraction; show the original event and the counter-record both
    remain visible;
12. attempt external delivery of a notification and cross-node activity; observe
    `UNCONFIGURED` refusals with receipts;
13. close both sessions with reconstructable receipts.

## Defeating cases

- a judgement request blocks the whole node, or the pending right is hidden;
- a model resolves a judgement request, or a setting, dashboard role, or
  session state widens an authority check;
- a resolution that enters through any surface that is not a kernel transition
  with a receipt — a code-owner review click, a chat reply, an edited file — is
  treated as the owner's judgement;
- a judgement resolution reaches `RATIFIED` without its `RECORDED` event, the
  grant checked at the transition, or its receipt;
- a judgement request addressed to the owner is absent from the owner's
  pending list;
- a notification cannot name its source address and digest, or is treated as
  the record it points to;
- a dashboard or activity value does not resolve to an authoritative record,
  or a dashboard edit writes service state directly;
- two rebuilds of the same projection from the same records differ;
- an activity entry appears for a node or service that is not configured, or
  an omitted source is not declared;
- a human post and a model post in the same thread take different transitions
  or yield irreconcilable receipts;
- a post, notification, or request is rewritten or erased instead of countered;
- external delivery is reported as success instead of `UNCONFIGURED`;
- a console worker's or renderer's report settles what the operator saw.

## Deferred

Real-time presence and cursors, reactions and emoji, voice or video, external
chat-platform bridges, email and push delivery, public share links, cross-node
activity, role hierarchies beyond typed scoped grants, and production rendering
are outside the first proof. Their interfaces may be declared as ports; their
effects remain refused or isolated until separately admitted.
