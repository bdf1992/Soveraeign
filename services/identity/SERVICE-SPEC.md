# Identity Service — Specification

Status: `BUILT` — self-reported by the drafting session under `decisions/0067`;
not witnessed. Mirrors `SPEC.md`'s shape at service scope. Named
`SERVICE-SPEC.md`, not `SPEC.md`: the root document owns that name.

Legal transitions and their preconditions, commit values, and refusals are
declared in `contracts/service.json` and are cited here, not re-derived
(`decisions/0067`). Where this document goes further than the contract, it is
because reading `challenges.py` and `recovery.py` against
`contracts/service.json` surfaced a gap between what is declared and what is
implemented; every such finding below is marked as read from the code, not
asserted from the charter.

## Owned domain records

`contracts/service.json` `owns`: `challenge`, `challenge-token-digest`,
`verification-basis`, `recovery-secret-digest`, `recovery-set`.

**`Challenge`** (`challenges.py`) — `challenge_id`, `principal_id`,
`channel_kind`, `channel_reference`, `token_digest`, `minted_at`,
`expires_at`, `state`, `presented_at`. Holds a digest, never a token.

**`RecoverySet`** (`recovery.py`) — `principal_id`, `enrolled_at`,
`live_digests`, `spent_digests`, `revoked_at`. Holds digests only. `remaining`
is derived (`0` once `revoked_at` is set, else `len(live_digests)`), never
stored as its own field.

**`verification_basis`** — not a stored field but a derived string,
`urn:soveraeign:challenge:<challenge_id>`, returned only once a challenge's
state is `PRESENTED` (`challenges.py` `verification_basis()`). This is the
value `decisions/0048` says a `VERIFIED` claim must carry; nothing in this
service writes it into a principal record (see `JOURNEYS.md`).

Neither record is durable. Both classes hold their instances in a plain
`dict` in memory; the emitted `.records` list is the only thing the module
offers a caller to persist, and even that list lives only as long as the
process (`CHARTER.md`, "It stores nothing durably").

## Service-local states

**Challenge:** `MINTED → PRESENTED` (success) or `MINTED → SPENT` (expiry,
principal mismatch, or a principal revoked since minting — the token is
burned rather than left live, `challenges.py` `present()`). Presenting a
challenge already in `PRESENTED` or `SPENT` always refuses `CHALLENGE_SPENT`
regardless of which; the two terminal states are not distinguished in the
refusal a caller sees, only in the stored record.

**RecoverySet:** no principal has a set (`Recovery.status` reports
`enrolled: False`) → enrolled (`live_digests` populated, `revoked_at` unset)
→ each redemption moves one digest from `live_digests` to `spent_digests`,
independently of the others (`test_each_secret_is_independent`) → revoked
(`revoked_at` set, `live_digests` cleared; `spent_digests` untouched, so
redemption history survives revocation) → a fresh `enroll` call after revoke
creates a new `RecoverySet` for the same `principal_id`
(`test_revoke_then_re_enroll`). Revocation is terminal for that instance, not
for the principal: nothing prevents re-enrollment.

## Legal transitions

`contracts/service.json` `operations`, cited by name rather than restated:
`mint-challenge` (CREATE), `deliver-challenge` (READ, `commit: DERIVED`),
`present-challenge` (SUPERSEDE), `enroll-recovery` (CREATE), `redeem-recovery`
(SUPERSEDE), `revoke-recovery` (COUNTER, `commit: COUNTERED`),
`report-unenrolled` (READ, `commit: DERIVED`). Every operation cites
`PROD-I-3` as the requirement it serves and uses only the shared kernel
contracts `standing`, `receipt`, `operation` (`uses_kernel_contracts`) — it
declares no schema of its own beyond the digests and sets above.

### Kernel transitions

None of the seven operations above is named in
`contracts/kernel-transitions.json`'s `transitions` array. That table's
fourteen transitions (`capture_source` through `invoke_model`) are the
kernel's own vocabulary; Identity's operations are service-local and reach
the kernel only by producing records shaped to fit inside its `receipt` and
`operation` contracts, per `uses_kernel_contracts`. The nearest kin, read
rather than declared:

- `present-challenge` produces a `verification_basis`, structurally similar
  to what the kernel's `cross` transition carries (`reader_declaration`,
  `omissions`, `destination_address`) — but `cross` also requires an
  `authority_grant_id` precondition that `present-challenge` does not
  declare, consistent with `CHARTER.md`'s "It grants nothing."
- `revoke-recovery`'s `commit: COUNTER` echoes the kernel's `retract`
  transition in name, but `retract` requires `authority_grant_id` and
  `known_effect` preconditions that `contracts/service.json` does not
  declare for `revoke-recovery` (it declares only `recovery_set_exists`,
  `declared_actor`) — a narrower precondition set, not an instance of the
  kernel transition.

Both observations are this document's own reading of the two contract files
against each other, offered so a future participant does not have to
re-derive them; neither is a ruling that either transition set should
change.

## Refusal reason codes

`CHARTER.md` declares two tables — one for challenges, one for recovery —
reproduced here with what reading the code against
`contracts/service.json` adds:

| Code | Meaning | Declared for | Implemented in |
| --- | --- | --- | --- |
| `CHANNEL_UNDECLARED` | principal has no verification channel | `mint-challenge` | `mint()` |
| `CHANNEL_REFUSED` | channel is `external` or an unknown kind | `mint-challenge`, `deliver-challenge` | `mint()` only — `deliver()` performs no channel-kind check |
| `PRINCIPAL_REVOKED` | principal is revoked | `mint-challenge`, `enroll-recovery` | `mint()` and `present()` — `enroll()` takes only a `principal_id` string, not a principal record, and cannot evaluate revocation |
| `TOKEN_UNKNOWN` | token or challenge id not found | `present-challenge` (declared); returned by `deliver()` too | `deliver()`, `present()` |
| `CHALLENGE_SPENT` | challenge already presented | `present-challenge` | `present()` |
| `CHALLENGE_EXPIRED` | window has closed | `present-challenge` | `present()` |
| `PRINCIPAL_MISMATCH` | presenter is not the named principal | `present-challenge` | `present()` |
| `NOT_ENROLLED` | no set exists for this principal | not declared for any operation | `redeem()`, `revoke()` |
| `SECRET_UNKNOWN` | secret never issued | not declared for any operation | `redeem()` |
| `SECRET_SPENT` | secret already redeemed | not declared for any operation | `redeem()` |
| `SET_REVOKED` | set was revoked | not declared for any operation | `redeem()`, `revoke()` |
| `ALREADY_ENROLLED` | a live set already exists | not declared for any operation | `enroll()` |

Findings from this table, each read from the code rather than stated in
`CHARTER.md`:

- **`present-challenge` refuses `PRINCIPAL_REVOKED`** (`present()`, tested by
  `test_revocation_after_mint_refuses_presentation`), but
  `contracts/service.json`'s declared refusal list for `present-challenge` is
  `["TOKEN_UNKNOWN", "CHALLENGE_SPENT", "CHALLENGE_EXPIRED",
  "PRINCIPAL_MISMATCH"]` — `PRINCIPAL_REVOKED` is absent from it.
- **`deliver-challenge` declares `CHANNEL_REFUSED`** as a possible refusal,
  but `deliver()`'s only refusal path is `TOKEN_UNKNOWN` for an unrecognized
  `challenge_id`; it never re-checks the channel kind it echoes back.
- **`enroll-recovery` declares `PRINCIPAL_REVOKED`**, but `enroll()`'s
  signature (`principal_id: str`) cannot receive a revocation flag to check.
  Its one actual refusal, `ALREADY_ENROLLED`, is declared for no operation
  in `contracts/service.json` and is absent from `local_refusals`.
- **`redeem-recovery` declares `["MISSING_PRECONDITION",
  "DIGEST_MISMATCH"]`**; `redeem()`'s four actual refusal codes
  (`NOT_ENROLLED`, `SET_REVOKED`, `SECRET_SPENT`, `SECRET_UNKNOWN`) match
  neither, and none of the four appears in `local_refusals`.
- **`revoke-recovery` declares `AUTHORITY_REFUSED`** against a
  `declared_actor` precondition; `revoke()` implements no authority check —
  see `SVC-IDENTITY-8` in `SRD.md`.
- **`local_refusals`** (`contracts/service.json`, the map from a
  service-level reason code to a kernel-level refusal family) covers only
  the seven challenge-lifecycle codes. None of the five recovery-lifecycle
  codes has a kernel-level mapping.
- No code in either module ever returns the literal string
  `"MISSING_PRECONDITION"`; it appears only as a kernel-level target that
  `local_refusals` maps other codes onto (e.g. `CHANNEL_UNDECLARED →
  MISSING_PRECONDITION`), and as a declared-but-unreached entry in several
  operations' refusal lists.

All of the above is this document's own reading of `contracts/service.json`
against `challenges.py` and `recovery.py`; none of it is stated in
`CHARTER.md`, and none of it is resolved here.

## Persistence and authority notes

- **No durable store.** Both `Challenges` and `Recovery` hold state in a
  process-local `dict`; the caller journals `.records` if it wants a durable
  trace. Whether that durable home is this service's own storage or a
  kernel-level registry is `decisions/0048` judgement 3, open
  (`CHARTER.md`, "An assumption stated rather than buried").
- **No authority checks.** Neither module inspects an `authority_grant_id`
  or any grant at all; `mint`, `present`, `enroll`, `redeem`, and `revoke`
  all proceed on the principal or actor data the caller supplies, per
  `CHARTER.md`'s "It grants nothing." Where `contracts/service.json`
  declares an authority-shaped precondition anyway (`revoke-recovery`'s
  `declared_actor` / `AUTHORITY_REFUSED`), the code does not yet enforce it
  — see Refusal reason codes above.
- **Clock and token source are injected**, never read from a global (
  `Challenges.__init__`, `Recovery.__init__`), which is what lets
  `test_a_microsecond_past_expiry_is_refused` and similar tests pin exact
  moments without waiting on a real clock.
