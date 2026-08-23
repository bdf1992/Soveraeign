# Claude Harness Binding (Provisional)

This directory is the first harness binding of the operating loop defined in
`SDLC.md`, admitted as a provisional target by owner direction (decision
0013). It realizes the loop for the Claude Code harness; it owns no policy.

Binding rules from `bindings/README.md` apply: this surface may project the
loop for this harness, but it may not introduce private standing, authority,
transitions, or direct storage writes. Every rule a skill applies is owned by
a governing document; skills point, they do not restate. On any divergence
between a skill and an owning document, the owning document prevails.

Skills are prefixed `sdlc-`. Tier skills: `sdlc-control`,
`sdlc-orchestration`, `sdlc-worker`. Domain skills: `sdlc-product`,
`sdlc-development`, `sdlc-qa`, `sdlc-release`, `sdlc-feedback`. Workflow
templates remain declarations in `SDLC.md`; executable orchestration scripts
are not admitted before their logical specification and defeating fixtures
exist.

Model substitutability applies to the loop itself: a second, materially
different harness binding must be able to run the same loop from the
governing documents alone. Nothing in this directory may become
load-bearing for the loop's semantics.
