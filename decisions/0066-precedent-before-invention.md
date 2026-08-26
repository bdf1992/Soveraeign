# 0066 · Precedent before invention

Status: `OWNER-DIRECTED · PROPOSED`

## Decision

Add `CONTRACT.md` C16: consequential technical boundaries inspect applicable
stable precedent before a private convention is defined, then deliberately
`ADOPT`, `PROFILE`, `DEFER`, `DEVIATE`, or `MONITOR` it. Precedent informs the
choice but creates no Soveraeign authority.

Use the existing design System of Record and verification loop. There is no
standards registry, journal, reducer, standing ladder, or permanent research
queue. `ENGINEERING.md` owns the current language and representation profiles;
Sov already loads `CONTRACT.md` and `ENGINEERING.md`, and Claude already defers
to the same governing set.

## Precedents and dispositions

- **ADOPT** BCP 14 (RFC 2119 and RFC 8174) for uppercase normative terms in
  explicitly normative governing text.
- **ADOPT/PROFILE** JSON Schema Draft 2020-12. Every schema names the dialect;
  the dependency-free validator refuses unsupported keywords instead of
  pretending full coverage.
- **PROFILE** RFC 3339 as `SOV-RFC3339-1`, a strict machine-instant form with an
  explicit known offset. Python `datetime.fromisoformat` extensions do not enter
  the wire contract.
- **PROFILE** RFC 9562 UUIDv4 for random identifier material while preserving
  Soveraeign's typed opaque identifiers and the distinction between identity,
  address, and digest.
- **ADOPT** SHA-256 for exact payload bytes where current contracts already name
  it.
- **DEFER** RFC 8785 JCS. Phase I has persisted Python-era encodings and no
  established cross-language number boundary; silently relabelling them JCS
  would be false and migrating them would break custody. New consequential hash
  inputs must instead name and version their exact representation.
- **MONITOR** broader security, supply-chain, observability, container, and AI
  precedents until a concrete boundary can be profiled without a compliance
  claim.

## Bounded repair

The Record Service joined five fields with `|` before hashing. Distinct subject
and actor partitions could therefore produce identical preimages. New entries
use `soveraeign-record-chain/v2`: a compact UTF-8 JSON array beginning with the
profile identifier, with the profile stored on every row and export entry.

Existing stores migrate by marking their existing rows
`soveraeign-record-chain/v1`. Version-1 exports remain readable and restore with
that profile. Version 2 never accepts the legacy algorithm for a row marked v2,
so compatibility does not reopen the collision.

The local JSON Schema validator previously described `datetime.fromisoformat`
as RFC 3339. It now applies the explicit `SOV-RFC3339-1` lexical profile before
calendar validation.

## BLUE evidence

- Equivalent mappings produce identical compact bytes under each named local
  profile.
- Every current JSON Schema file declares Draft 2020-12.
- Existing v1 journals and exports remain reconstructable; new entries and
  exports carry v2 explicitly.
- Sov and host bindings inherit through their existing governing-source chain.

## RED attacks

- move a `|` between subject and actor while keeping the legacy preimage equal;
  v2 digests differ;
- relabel a v2 entry as v1 or alter its profile; verification refuses;
- submit a Python-only ISO spelling, naive time, lower-case separator, leap
  second, or unknown offset; the machine-instant profile refuses;
- remove or change a schema dialect declaration; the precedent self-check fails;
- treat an external standard as authority or compliance; C3 and C16 still
  refuse the promotion.

## Consequences

Ordinary implementation stays boring: follow `ENGINEERING.md` when it already
settles the boundary. A new consequential protocol/default needs only the
smallest durable disposition and a testable local contract. Compatibility work
remains explicit and versioned rather than hidden behind a runtime default.

This decision establishes `BUILT` evidence only. Independent observation and
the campaign's pre-acceptance grant govern landing; this record does not witness
itself or promote standing.
