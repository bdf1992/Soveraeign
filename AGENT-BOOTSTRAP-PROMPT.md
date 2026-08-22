# Agent Prompt — Establish the Founding Repository

Copy everything below this line into a capable coding agent after attaching or
extracting this ZIP.

---

You are establishing the canonical founding repository for a locally
sovereign, algorithmic, AI-native enterprise operating environment.

The attached `founding-repository-bootstrap` directory is the seed repository.
It contains a populated canonical layer, an immutable historical evidence
corpus, a source lock, open seams, lineage standings, conformance seeds, and a
verification script.

This is a consequential repository operation. Work carefully and preserve
evidence byte-for-byte.

## Actor and authority

This is a joint operation.

- Bdo holds product intent, naming authority, judgement authority, phase-gate
  authority, and final acceptance.
- You may inspect, compare, initialize, structure, validate, and make mechanical
  repairs required to establish this bootstrap.
- The owner-selected product and repository name is `Soveraeign`. You may not
  alter or normalize its spelling, ratify a product
  judgement, resolve an open seam by preference, import predecessor code,
  choose the production stack, publish a remote, or begin runtime implementation.

## Target

Create a clean local Git repository from this seed while preserving the seed's
content and authority distinctions. The result must be ready for the next
bounded work session: F0 founding closure.

## First actions

1. Resolve the intended target directory. If none was supplied, ask for only
   that directory. Do not ask for or change the product name.
2. Refuse to overwrite a non-empty target directory. Report the collision and
   wait for an explicit alternative.
3. Copy the seed contents into the empty target without adding another wrapper
   directory.
4. Read, in order:
   - `AGENTS.md`
   - `STATUS.yaml`
   - `README.md`
   - `SYSTEM.md`
   - `CONTRACT.md`
   - `PRD.md`
   - `OPEN-SEAMS.md`
   - `lineage/README.md`
   - `lineage/ANCESTORS.yaml`
5. Run `python scripts/verify_bootstrap.py` before modifying anything.
6. If verification fails, stop and report the exact structural or digest
   residual. Never repair a locked evidence file in place.

## Establishment operation

After the pre-check passes:

1. Initialize Git with `main` as the initial branch if the target is not already
   a repository.
2. Confirm that every file under `lineage/evidence/` matches
   `lineage/SOURCES.lock`.
3. Confirm that `product_name: Soveraeign` and `repository_name: Soveraeign`
   remain present in `STATUS.yaml`.
4. Inspect the canonical layer for broken relative links, malformed YAML-like
   scenario structure, accidental references to absent runtime code, and files
   that incorrectly claim owner ratification.
5. Make only mechanical bootstrap repairs. For any semantic contradiction, add
   or refine an entry in `OPEN-SEAMS.md`; do not choose the answer.
6. Do not add `src/`, a package manifest, framework scaffold, database schema,
   production workflow, remote origin, or deployment configuration.
7. Run the verification script again.
8. Review the staged diff. Confirm that no evidence file changed and no final
   owner-selected product name was not changed.
9. Create the initial commit:

   `founding: establish initial repository`

   If local Git identity is unavailable, do not invent it. Leave the files
   uncommitted and report the blocker.

## Required observations

The operation succeeds only when all of the following are observed:

- the repository initializes from an empty target;
- the verification script passes before and after establishment;
- all locked evidence digests remain unchanged;
- the canonical founding documents are present and non-empty;
- seven or more founding conformance scenarios are present;
- no production runtime implementation exists;
- no predecessor code was imported;
- no remote was created;
- the product and repository names remain `Soveraeign`;
- all unresolved semantic conflicts remain visible;
- and the resulting Git state is clean after the commit, or the missing Git
  identity is reported without fabrication.

## Completion report

Return:

1. target path;
2. initial commit hash, or the exact reason no commit was created;
3. verification result and number of checks;
4. evidence-file count and confirmation of unchanged digests;
5. files mechanically changed during establishment;
6. semantic seams discovered but not resolved;
7. assumptions introduced;
8. the exact next bounded request:

   `HowDo we close F0 by reconciling the canonical founding layer against the locked evidence corpus without selecting a production stack?`

Do not report success from file creation alone. The evidence-integrity check,
protected OPEN naming state, and observed Git result are the acceptance proof.
