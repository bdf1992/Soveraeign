// Reproduces sovkernel.authority.evaluate() and sovkernel.scope.out_of_scope()
// for a single grant against a single request, using Cedar-native primitives:
// grant fields as entity attributes, time and budget as ordered comparisons,
// branch and capability as entity-set membership, and scope as a Path entity
// hierarchy walked with Cedar's `in` operator.
//
// Cedar itself is implicit-deny-by-default with an explicit forbid always
// overriding any permit (reports/2026-08-23-gateway-research-and-controller-plan.md,
// finding 2). That shape is used directly here: the one permit policy carries
// every condition that must hold for a live, in-scope, in-budget grant to cover
// the request, and each forbid policy is one of the kernel's own explicit
// overrides - revocation, JUDGEMENT authority from a non-owner issuer, and the
// two directions a requested path can select something the grant excludes.

permit(principal, action, resource)
when {
  context.grant.status == "RATIFIED" &&
  principal == context.grant.actor &&
  context.grant.capabilities.contains(action) &&
  resource in context.grant.includedPaths &&
  context.now >= context.grant.validFrom &&
  context.now < context.grant.validUntil &&
  context.effectClassOrdinal <= context.grant.effectCeilingOrdinal &&
  (if context.grant has branches
   then context.branch in context.grant.branches
   else true) &&
  (if context.grant has budgetCeiling && context.grant has budgetUnit
   then (if context has spendAmount && context has spendUnit
         then context.spendUnit == context.grant.budgetUnit &&
              context.spendAmount <= context.grant.budgetCeiling
         else true)
   else true)
};

// A grant that was revoked refuses regardless of everything else it would
// otherwise cover (authority.py `_grant_unavailable`, `revoked_at`).
forbid(principal, action, resource)
when { context.grant has revokedAt };

// JUDGEMENT authority may be issued by the owner and by nobody else
// (authority.py `JUDGEMENT_ISSUER`).
forbid(principal, action, resource)
when {
  context.grant.authorityType == "JUDGEMENT" &&
  context.grant.issuerId != "bdo"
};

// The requested path is the excluded entry, or sits beneath it
// (sovkernel.scope `_selects_excluded`, the "is inside" direction).
forbid(principal, action, resource)
when { resource in context.grant.excludedPaths };

// The requested path is a directory that contains the excluded entry
// (sovkernel.scope `_selects_excluded`, the "is a directory containing"
// direction). Cedar's `in` only walks ancestors, so the reverse direction -
// resource is an ancestor of something excluded - has no single expression
// over the dynamic `excludedPaths` set; it is spelled out against the fixed
// entries this corpus's one grant excludes.
forbid(principal, action, resource)
when {
  SoveraeignAuthority::Path::"contracts/standing-grants.json" in resource ||
  SoveraeignAuthority::Path::"decisions" in resource ||
  SoveraeignAuthority::Path::"STATUS.yaml" in resource ||
  SoveraeignAuthority::Path::"SPEC.md" in resource ||
  SoveraeignAuthority::Path::"AGENTS.md" in resource
};
