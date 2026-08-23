# Sov Context Profile

Sov is the portable, provider-neutral context profile for Soveraeign's main
operating agent. Start with [`SOV.md`](../../SOV.md).

This directory owns only the realization of that profile:

- `profile.json` identifies Sov and its context, agency, state, and activation
  boundaries;
- `profile.schema.json` and `session.schema.json` describe the two local JSON
  surfaces;
- `validate.py` checks profile invariants and request-only session declarations;
- `fixtures/` contains one admitted declaration and one defeating declaration;
- `tests/` independently invokes the checker over both cases.

The profile points to policy owned by `AGENTS.md`, `SYSTEM.md`, `CONTRACT.md`,
`SPEC.md`, and `SDLC.md`. It does not restate itself into authority. On any
divergence, the owning governing document prevails.

## Current limit

The checker answers whether a context declaration is structurally ready. It
does not resolve a live authority grant and never authorizes an operation. It
admits inspection declarations with no effect class and refuses consequential
effect claims until
issues #14, #16, #25, and #30 provide the live Registry, Gateway, shared-contract,
and operator-binding boundaries.

Run the focused checks with:

```bash
python -m unittest discover -s bindings/sov/tests -v
```
