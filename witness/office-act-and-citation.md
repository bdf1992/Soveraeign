# Witness record — office-act-and-citation (PR #225)

```witness
standing_supported  BUILT -> WITNESSED (citation-gate repair; the recorded act and reading as journal facts)
subject             office-act-and-citation
revision            8ef29e12e4213c3f67516bb428688186cee35b71
pass                4
```

## Pass 4: commit 8ef29e1 (2026-09-07)

**Verdict: RATIFIABLE.** Every finding raised across four passes is closed. H5 turned
out to name a compression rather than a patch: `node` and `head` already determine the
address, so one equality replaced three comparisons and reached H3, H4 and H5 at once —
and writing its failing case is what exposed that H4 had never been closed at all. That
is the loop working. One residual is recorded and I am not holding the change for it.

- **Commit witnessed:** `8ef29e12e4213c3f67516bb428688186cee35b71`, HEAD of
  `claude/sovereign-phase-1-5-5uzffu` after the force-push; tree
  `02d4247d7bfce83d304446c5bb9cc1a7003c1710`; base `b1448eeb458afa4a8c60b57c1cb46906246af7f7`.
- **Working tree witnessed against:** the worktree at `8ef29e1`, porcelain empty before
  every measurement and holding only this pass's deposits after. Measurements ran in a
  clean full-history clone at the same commit; the clone was returned to `8ef29e1` with
  empty porcelain after the merge probe described below.
- **Observed:** 2026-09-07T20:05Z (UTC).
- **Receipt:** `witness/observations/2026-09-07-office-act-and-citation-observation-4.json`.
- **Landing record:** `.local/observations/2026-09-07-office-act-and-citation-landing-4.json`.
- **Absorbing these deposits:** they stale `docs/documentation.html` and nothing else.

### The rebase

**Linear, and I checked it with the repository's own instrument as well as by hand.**
Five commits, one parent each, on `b1448ee`; no merge commits in the range.
`sov_ci_subject.py candidate` emits `construction_history: LINEAR`,
`construction_commits: 5`, `base_is_ancestor: true`, `candidate_tree: 02d4247` — the same
tree I froze.

**Blob identity, wider than you asked.** Rather than the four named files I diffed whole
trees. Each rebased commit differs from its pre-rebase original in exactly three paths:
`.clarity/coverage.json` and `ROADMAP.md`, which the trunk brought, and
`docs/documentation.html`, which is generated. Every other blob in all five trees is
byte-identical — `a13b888→7918314`, `d56fff5→a6f7c42`, `575d65f→4b978aa`,
`d03772a→bce972d`, `e6ee165→8ef29e1`.

**My receipts replayed.** Each earlier receipt's declared digests, recomputed against the
blobs of its rebased counterpart: 13 of 13 for pass 1, 10 of 11 for pass 2, 11 of 12 for
pass 3. The only two misses are `docs/documentation.html` in each. So 34 of 36 digests
replay exactly and the code readings of passes 1 to 3 carry to this history. My three
receipts and this record survived the rebase byte-identical, which I confirmed by digest.

**The rule.** Your correction is right by the contract's own words and not only by the
gate that refused you: `contracts/repository-candidate-lifecycle.json` has
`rewrite_policy.mutable_allowed` containing `rebase-onto-current-target` and
`rewrite_policy.frozen_forbidden` containing `rebase`. The prohibition attaches to a
FROZEN candidate; this carrier was MUTABLE. The instinct that produced the merge — that
my receipts bind to SHAs and a rebase orphans them — was a real cost correctly
identified and weighed against the wrong rule.

**The gate, checked both ways rather than taken.** On the linear branch
`sov_ci_subject.py candidate` exits 0 with a receipt. On a merge commit I built myself —
a side commit off `b1448ee` merged into the candidate with `--no-ff` — it exits 2 with
`REFUSED: CANDIDATE_HISTORY_NONLINEAR` naming that commit.

**What the rebase cost.** The SHA binding and nothing else. All 33 witness receipts in
the tree now read `STALE` against their subjects, mine included, because every subject
SHA moved; `sov_witness_layer` grades that as record ageing rather than failure, which is
the right grade. Had these been FROZEN the rebase would have been forbidden, and the move
would have been `SUPERSEDED` and a fresh freeze.

### Dispositions, re-derived

**H1 closed.** The T3 case now declares `node:loc` against `node:local` with an address
otherwise exactly right, so nothing but the node comparison can refuse it, and the
mutant reading the declared node as contained in the real one dies on it.

**H2 closed.** The comparison the pass-3 commit called unreachable is reached by a
shipped case now, and my two-node case still passes unmutated against these bytes.

**H3 closed.** The suffix mutant dies on two cases.

**H4 closed, and it had not been closed before.** A declared node is checked whether or
not the address is live. A report naming the current export while declaring `node:gone`
is refused. That early return carried this open from pass 2 through pass 3 and is gone.

**H5 closed, and it was the right compression.** One equality against
`<node dir>/<head[:12]>.json` refuses an invented parent, another node's directory, a
missing address and an invented filename — all on one line. The compression is sound
because `node` and `head` genuinely determine the address: one directory per node, each
export named by the head it replays to. A citation of an earlier head still passes when
its address names *that* head, which is what keeps a superseded citation readable.

**G1 and G2 not regressed.** `entries` as `null` and as a dict still give clean defects
with no exception; the cited-head prefix mutant still dies.

### Measurements

Fifteen adversarial citation cases, all behaving correctly. Ten mutants: **nine die on
the shipped 30-case suite** — both directions of the address equality, the shortened
head, the cited-head prefix, the unchecked address, the swallowed count, the any-address
branch, node-blind resolution, and expected-built-from-the-address.

### The one residual, which I am not holding this for

The mutant reading the *real* node as contained in the *declared* one —
`_node_id_of(_export_node(path)) in node` — survives the shipped suite. It is killed by
the case I handed over in pass 3, `node="node:local-2"` against a `node:local` export,
which was replaced by the `node:loc` case rather than joined to it. Two directions of one
comparison want two lines in the same case. I record it as a residual and not a
condition because the harm is bounded: the address equality is still built from the real
node's directory, so what would pass is a report whose `node` field names something that
does not exist while its address is otherwise correct. The case exists; absorbing it is
the concern's, and holding a fourth pass open over it would be the caution `AGENTS.md`
calls a defect.

### A small caution, partly my own

Two repaired cases assert on generic fragments — `"names /"` or `"names nodes/"` — where
the earlier wording pinned a specific refusal. They do discriminate here; three mutants
die on them. But an assertion that broad pins the shape of a message rather than its
meaning. The other half is mine: my pass-3 two-node case asserted a refusal string this
repair reworded, and it failed against these bytes until I updated it. I am recording
that rather than quietly fixing it, because a case coupled to message text ages with the
message, and that is worth knowing before the next rewording.

### Judgement

Unchanged, unanswered, and correctly neither yours nor mine: does Bdo affirm that he
directed the act recorded at entries 118 to 123 of `node:local`, in the words quoted in
`office_act.direction`? Four passes have made the gate around that record tighter. None
of them has made the record say who asked, and none of them can.

### Commands

```
git -C <this worktree> rev-parse HEAD                            8ef29e1, tree 02d4247, clean
git log --format='%h %p' b1448ee..HEAD                           five commits, one parent each
git log --merges b1448ee..HEAD                                   none
git diff --name-only <old> <new>, five rebase pairs              3 paths each, all generated or trunk
earlier receipts' digests recomputed at their counterparts       34 of 36 match; both misses generated
python3 scripts/sov_ci_subject.py candidate (linear)             exit 0  LINEAR, 5 commits
python3 scripts/sov_ci_subject.py candidate (merge I built)      exit 2  CANDIDATE_HISTORY_NONLINEAR
python3 scripts/verify.py                                        exit 0  PASS: 52 checks in 12.630s
python3 scripts/lint.py                                          exit 0
python3 scripts/sov_node.py journals                             exit 0
python3 -m unittest scripts.tests.test_sov_node_journal          exit 0  30 tests
witness_layer / clarity / diagrams / surface / docs              exit 0
fifteen adversarial citation cases                               all as expected
ten mutants, shipped suite                                       9 killed, 1 survived (the residual)
the same ten, plus my two cases                                  10 killed; control exits 0
```

## Pass 3: commit d03772a (2026-09-07)

**Verdict: RATIFIABLE-WITH-CONDITIONS.** All four of pass 2's findings are answered
and three are closed. G3, the serious one, is closed by a pin I would not have thought
of and which is better than what I asked for: the address must be named by the head it
declares, which distinguishes a superseded address from a fabricated one without
needing to know whether the file was ever written. What holds this pass short is G4,
where the commit states that one comparison is beyond reach of any case. It is not. I
built the case, and I built the one-word variant of your own T3 case that kills the
other mutant. Both are below, ready to take.

- **Commit witnessed:** `d03772afac294084c62d2ed68f20d0c90d768d13`, HEAD of
  `claude/sovereign-phase-1-5-5uzffu`; tree `e062edc9eec0d50a470dfc2bee0ee3437fb26118`;
  base `6498fc7b3172476df54882d7b65c47f52366c8c8`; trunk at witness time `b1448ee`,
  attestable on the reading pass 2 recorded and unchanged since.
- **Working tree witnessed against:** the worktree at `d03772a`, porcelain empty before
  every measurement and holding only this pass's deposits after. Measurements ran in a
  clean full-history clone at the same commit.
- **Observed:** 2026-09-07T19:05Z (UTC).
- **Receipt:** `witness/observations/2026-09-07-office-act-and-citation-observation-3.json`.
- **Landing record:** `.local/observations/2026-09-07-office-act-and-citation-landing-3.json`.
- **Absorbing these deposits:** they stale `docs/documentation.html` and nothing else;
  the committing step rebuilds it. `sov_surface.py check` exits 0 either way.

### Dispositions, re-derived

**G1 — closed, wider than the case.** A non-numeric count is a clean defect again, and
I checked past the shipped fixture: `entries` as a string, as `null`, as a list and as a
dict all produce `cites ... entries, but its head is entry N of ...` with no exception.
The mutant that swallows the failure and accepts the count silently dies on your case.

**G2 — closed.** `test_a_truncated_head_does_not_resolve_by_prefix` kills the
`startswith` mutant on the cited-head lookup. That is the mutant pass 1 named and pass 2
found still alive. It is dead.

**G3 — closed for everything pass 2 raised, and I checked the 2026-09-06 report the way
you asked rather than by reading the code.** Calling `_cited_export` on the real report
at this commit: its `address` is not in `heads`, it declares `node:local`, its filename
`23d3b48086be.json` equals its own `head[:12]`, and the function returns the current
export with no refusal. So it is legitimately resolved, by the superseded path, for the
reason the code gives. Your reading was right. The address still names a file that is
not in the tree — but that is now a recognised and disclosed state pinned to the
report's own head, rather than an unmeasured one, and `address_note` and the repointed
`verify` say so. That is the right resolution of pass 1's F1.

**G4 — partly, and the coverage claim is falsified.** The collapse is a good shape:
after the address-node comparison the two values are provably equal, so one comparison
is better than two, and saying so beats claiming coverage. But the second comparison is
not gone — it moved from node ids to directory names — and both containment mutants are
reachable. See H1 and H2.

### Findings

**H1 — the T3 case is still written in the harmless direction.**
`test_a_declared_node_must_equal_the_nodes_name_and_not_merely_contain_it` declares
`node:loc` against a `node:local` export. Under the mutant
`_node_id_of(_export_node(address)) not in node`, `"node:local"` is not in `"node:loc"`,
so the mutant refuses too and the case still passes: **it survives the shipped suite**.
The killing direction is a declared node that *contains* the real one. Changing
`node:loc` to `node:local-2` in that same case kills it — one word, no second node.
This is the second pass running where a coverage claim ran ahead of the fixture, and it
is the same direction error the commit message says was caught and rerun.

**H2 — the remaining comparison is reachable, and the commit says it is not.** The node
layer pins `node_id` to the registry's single `SELF`, which is why building a second
node through `open_node_at` fails — that part of your reading is right. Build it one
level below instead, with `RecordService` and a `ConsoleService` told a second node id:
the chain is the service's own, so the export replays, and pointing
`journal.NODE_REGISTRY` at a two-node registry puts both exports in `heads`. Naming
decides whether it bites: the wrong candidate must sort first under a containment
reading, so the nodes must be `node:loc` and `node:local`, not `node:local` and
`node:local-2`. Control passes unmutated; the mutant
`_export_node(path) in _export_node(address)` resolves the `node:local` citation to
`node:loc`'s export and the case fails. The two cases, as run:

```python
def test_a_declared_node_that_contains_the_real_one_is_refused(self):
    """H1: the killing direction. A declared node that contains the real one."""
    self.report("wider", journal=self.stale(node="node:local-2"))
    self.advanced()
    defects, _ = self.grade()
    self.assertTrue(any("whose node is not the node:local-2 it declares" in item
                        for item in defects), defects)

class TwoRegisteredNodes(unittest.TestCase):
    """H2: the node layer pins node_id, so the second node is built one level below it."""

    def registry_with(self, temp, *node_ids):
        base = json.loads((ROOT / "contracts" / "fixtures"
                           / "node-registry.reference.json").read_text(encoding="utf-8"))
        first = base["nodes"][0]
        nodes = [first]
        for node_id in node_ids:
            extra = dict(first)
            extra.update({"node_id": node_id, "display_name": node_id, "relation": "PEER",
                          "admitted_by": "seat:root", "known_since": "2026-09-07T00:00:00Z"})
            nodes.append(extra)
        base["nodes"] = nodes
        path = temp / "registry.json"
        path.write_text(json.dumps(base), encoding="utf-8")
        return path

    def node(self, temp, dirname, node_id, operator):
        state = temp / ("state-" + dirname)
        record = RecordService(state / "record")
        console = ConsoleService(record, state / "console", node_id)
        try:
            console.grant(operator, "open:session", operator, granted_by=ISSUER)
            console.grant(operator, "read:registry", "registry:any", granted_by=ISSUER)
        finally:
            record.close()
        return state, journal.export(state, temp / "nodes" / dirname / "journal")

    def test_a_citation_resolves_to_its_own_node_when_another_name_contains_it(self):
        held = journal.NODE_REGISTRY
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            journal.NODE_REGISTRY = self.registry_with(temp, "node:loc")
            try:
                self.node(temp, "node-loc", "node:loc", "principal:fixture-a")
                state, export = self.node(temp, "node-local", "node:local",
                                          "principal:fixture-b")
                document = json.loads(export["path"].read_text(encoding="utf-8"))
                address, head = export["path"].resolve().as_posix(), export["head"]
                record = RecordService(state / "record")
                ConsoleService(record, state / "console", "node:local").grant(
                    "principal:fixture-c", "read:registry", "registry:any", granted_by=ISSUER)
                record.close()
                export["path"].unlink()
                journal.export(state, temp / "nodes" / "node-local" / "journal")
                reports = temp / "reports"
                reports.mkdir()
                (reports / "two.json").write_text(json.dumps(
                    {"journal": {"address": address, "node": "node:local", "head": head,
                                 "entries": document["entry_count"]}}), encoding="utf-8")
                defects, heads = journal.grade(temp / "nodes", temp / "reports")
                self.assertEqual(len(heads), 2, heads)
                self.assertEqual(defects, [], defects)
            finally:
                journal.NODE_REGISTRY = held
```

**H3 — the filename check is pinned in one direction only.** The mutant comparing the
address by `endswith` instead of by exact basename survives the shipped suite and both
my cases. An address whose basename is `xx<head12>.json` passes under it. The shipped
code is right; nothing holds it there. One case with a prefixed basename closes it.

**H4 — a live address may still contradict its declared node.** The early return on
`address in heads` happens before any node comparison, so a report naming the current
export while declaring a node with no export passes with no defect. Carried unchanged
from pass 2. Nothing is misdirected, because the address is correct and authoritative;
what passes unremarked is a false `node` field, which is the one field whose entire
purpose is to be checked.

**H5 — everything above the node directory in an address is unread.** `_export_node`
reads only the second-to-last directory, so `node-local/journal/<head12>.json` and
`../../elsewhere/node-local/journal/<head12>.json` both resolve. A reader following
either lands nowhere. Worth saying: after this repair the address is *fully derivable*
from `node` and `head`, so one equality against
`nodes/<node dir>/journal/<head[:12]>.json` would replace three comparisons and close
H4 and H5 together. The fixtures use absolute addresses, so that shape would need them
moved to repository-relative ones — your call whether that trade is worth it.

### The limit I am not calling a defect

An address whose filename is the cited head's prefix but which was never exported cannot
be told from a genuinely superseded export, because the gate cannot know at which heads
a node was exported. I constructed one and it passes. That is the honest boundary of the
pin, and the pin is still what stops a fabricated address from naming any head the node
never reached.

### The F5 boundary reading

Sound. `open_office` records grants through `ConsoleService.grant`, whose payload
`authority.grant_payload` owns, so putting the direction there changes a shape the
Console Service records. The alternative — appending a separate entry from the node
layer — does not clearly avoid the crossing either, because a new `record_kind` is
vocabulary `CLASSIFICATION.md` owns. Naming it and not taking it is right, and the
report now says so in the object it concerns.

### A hazard in my own reading, recorded

One command this pass was issued without an explicit repository path and ran against the
sibling worktree at another HEAD, carrying another session's uncommitted work. I caught
it on the next command and nothing from it entered this record. `CLAUDE.md` T6 is about
the tree moving under the reader; this is its neighbour, the reader moving off the tree.
Every measurement here names its repository explicitly.

### Commands

```
git -C <this worktree> rev-parse HEAD                            d03772a, tree e062edc9, clean
python3 scripts/verify.py                                        exit 0  PASS: 52 checks in 14.222s
python3 scripts/lint.py                                          exit 0
python3 scripts/sov_node.py journals                             exit 0
python3 -m unittest scripts.tests.test_sov_node_journal          exit 0  29 tests
sov_witness_layer records / clarity check / diagrams / surface   exit 0
journal._cited_export over both real reports                     2026-09-06 resolves superseded, no refusal
eleven adversarial citation cases                                8 as expected, 3 admitted (H4, H5, the limit)
seven mutants, shipped suite                                     4 killed, 3 survived (H1, H2, H3)
the same seven, shipped suite + my two cases                     6 killed, 1 survived (H3); control exits 0
```

## Pass 2: commit 575d65f (2026-09-07)

**Verdict: RATIFIABLE-WITH-CONDITIONS.** Pass 1's F1 is repaired where it mattered
and the repair is the right shape: the address is measured again, and the node is
named rather than inferred from a string. F3 is closed better than it was asked to
be. Two of F2's three mutants are closed with cases. What holds this pass short of
clean is one regression the count repair introduced, one mutant reported closed that
is still alive, and what is left of F1.

- **Commit witnessed:** `575d65f5efb32036183ffdc9ed4bbf557677c103`, HEAD of
  `claude/sovereign-phase-1-5-5uzffu`, two commits after `a13b888`; candidate tree
  `e9d7359fbf698f405396871c028105bb76871cfa`; base `6498fc7b3172476df54882d7b65c47f52366c8c8`.
- **Trunk at witness time:** `b1448eeb458afa4a8c60b57c1cb46906246af7f7`. The pass is
  attestable; see *The moved base* below.
- **Working tree witnessed against:** the worktree at `575d65f`, porcelain empty before
  every measurement and holding only this participant's pass-2 deposits after. HEAD was
  re-read before and after every command and never moved. Measurements ran in a clean
  full-history clone at the same commit.
- **Observed:** 2026-09-07T18:20Z (UTC).
- **Receipt:** `witness/observations/2026-09-07-office-act-and-citation-observation-2.json`.
- **Landing record:** `.local/observations/2026-09-07-office-act-and-citation-landing-2.json`.
- **Absorbing these deposits:** they stale `docs/documentation.html` and nothing
  else. `python scripts/sov_docs.py check` fails with them present;
  `python scripts/sov_surface.py check` exits 0 either way. Rebuild the one page.
- **Independence:** this participant wrote pass 1's findings and none of the repairs.
  It did not see the builder's mutant commands and did not run them; every disposition
  below was re-derived from twelve adversarial cases and ten mutants of its own.

### Dispositions, re-derived

**F1 — closed where it mattered, with a residual.** A report whose `address` names a
file no longer under `nodes/`, and which declares no node, now earns `which is no
export under nodes/`. That is the exact case pass 1 constructed, and it is caught.
Resolution is by node identity through `_node_id_of(_export_node(path))` rather than by
string granularity, which is the better shape: it says what it means. See G3 for what
is left.

**F2 — two of three.** Understating the entry count is refused (`int(...) != position`)
and a six-character export filename is refused (`head[:12] == stem`); both carry new
cases and both of my mutants for them die. The third is not closed; see G2.

**F3 — closed, and stronger than asked.** `grant_id` is in `ID_KEYS`, and
`_recorded_ids` reads grants out of payloads. A fabricated grant id is refused; a real
grant at or below the cited head passes; and a real grant the node recorded *after* the
cited head is refused, which pass 1 did not ask for and should have. The `session_id`
lesson checks out independently: adding `session_id` to `ID_KEYS` on a copy of the tree
makes `sov_node.py journals` exit 1 with `names ids the node had not recorded at its
cited head: fresh-e39c72b9` — the probe's own *host* session name, which the node never
records. The docstring's reason is the true reason.

**F4, F5, F6 — recorded adequately.** `observation_schema_note` says plainly that no
such schema exists at v1, v2 or v3 and that nothing validates the file.
`what_the_record_does_not_hold` names the direction's absence from the node, the
unauthenticated `principal:bdo`, and the stale serving-model claim routed as owner-held
identity naming. Each sits in the object it is about. On the question asked back: F6 is
correctly routed and I would not repair it here. F4 is repairable inside this concern —
write the schema, drop the field, or carry the note on all three reports, since only
the newest has it. F5 is repairable in part: `open-office` could record the direction
and `directed_in` as an entry the node keeps, which puts the words in the record
instead of a gitignored ndjson without authenticating anyone; but that changes a
recorded shape, and whether it stays inside this concern or crosses into the console
record contract is the builder's call to make and to state.

**F7 — answered, with two small inaccuracies.** All five spans are there, 111–117
included. The 111–117 line omits the sharpest fact in the span, the
`console.open-session` receipt `REFUSED NO_LIVE_GRANT` at entry 111. And 124–173 is
written as one entering and one crossing, where the chain holds two sessions —
`session_0fc948f67d3c40d8` at 124–148 and `session_5bbe1d42cdd64427` at 149–173 — each
entering, crossing once and refused three times.

**F8 — half of it was mine and is withdrawn.** `docs/documentation.html` was genuinely
staled by the pass-1 deposits and is rebuilt here; the real check reads `PASS:
documentation page matches 287 documents`. `docs/surface.html` was never stale. The
`FAIL: docs/surface.html is stale` line I cited is a planted case inside
`test_sov_surface` in tooling shard 4, and `python scripts/sov_surface.py check` exits 0
with `PASS`. Pass 1 read a planted line out of stdout as a verdict — the exact defect
this repository names by example — and the correction belongs to this witness, not to
the builder. Rebuilding only the documentation page was right.

### The moved base

Attestable, and the reconciliation is mechanical. `b1448ee` changes three paths over
`6498fc7`, which is exactly `git merge-base` of this branch and the trunk:
`.clarity/coverage.json`, `ROADMAP.md`, and `docs/documentation.html`. The only overlap
with this candidate is the generated page. `git merge --no-commit --no-ff b1448ee` in a
clone of `575d65f` exits 1 with exactly one conflict, in `docs/documentation.html`; the
other two merge clean. So the un-reconciled state hides no source conflict, and the
conflict that exists is resolved by rebuilding the page rather than by choosing a side —
choosing either side leaves a stale page the check catches. Two limits worth stating:
this observation covers the candidate, not the merge result; and if reconciliation is
done by rebase the candidate takes a new SHA and this observation does not transfer to
it.

### Findings

**G1 — a traceback where a defect used to be.** `int(journal["entries"])` raises out of
`grade()` when a report states a non-numeric or null count. At `a13b888` those same two
reports produced clean defects: `cites many entries, but its head is entry 10 of ...`
and `cites None entries, ...`. At `575d65f` they raise `ValueError` and `TypeError`,
which propagate through `command_journals` and out of the check. It fails closed, so
nothing bad passes — but the suite keeps a case named
`test_an_edited_entry_is_a_defect_not_a_traceback`, and this is that defect,
introduced by the count repair. Coerce or refuse around the count, and pin it.

**G2 — the mutant pass 1 named is still alive.** Pass 1's third survivor was the
*cited-head* position lookup matched by `startswith` instead of equality, in
`_grade_citation`. It survives the 23-case suite unchanged. The repair fixed a real
second instance of the same shape — the export filename in `_grade_export` — and
reported the finding closed. Nothing pins full-digest equality on the cited head, and
the twelve-character prefix is the form this repository writes into every export
filename and every `journals` output line, so under that mutant a report citing
`"head": "23d3b48086be"` would resolve. I take the disposition as honestly made and the
finding as open.

**G3 — the address is unmeasured whenever a node is declared.** `_cited_export` returns
early on an exact address match and otherwise resolves on `node` alone, so once `node`
is present the address is never read. Four constructed reports pass with no defect: a
fabricated address under the right node; an address naming a different node's directory
entirely; no address at all; and a live address contradicted by a node that has no
export. The repaired 2026-09-06 report is itself in the first of those states — its
`address` still names the file this branch deleted — and the `address_note` gives the
purpose of the repair as "so a reader is not sent to a file that is no longer in the
tree". That is now true of `verify` and not of `address`. Two comparisons using
functions already in the module close it: when `node` is declared and `address` is
non-empty, require `_node_id_of(_export_node(address)) == node`; when `address` is in
`heads`, require the declared node to agree.

**G4 — node equality is right and unpinned.** The comparison is `==` today; a mutant
weakening it to substring containment survives the suite. `CLAUDE.md` T3 records that
this repository has already shipped a substring comparison over exactly this kind of
token and had it produce a false claim in a governed document. One case with a node id
that contains another closes it.

### Repair or rewrite

Repair, on my reading, and the question was worth asking. Nothing that constitutes the
2026-09-06 report's claim moved: `head`, `entries` and `cited_entries` are
byte-identical, and the diff is three lines — `address_note` added, `node` added,
`verify` repointed. The `verify` string was an instruction to a reader that named a file
the repository no longer contains; it was wrong, and wrong is not evidence. The change
is disclosed inside the same object rather than made silently, and the original bytes
survive at `a13b888` and every commit before it. What would have made it a rewrite:
touching `head`, `entries` or `cited_entries`, or making the change with no note. The
one thing left undone is that `address` still points at the deleted file, which is G3.

### Judgement

Unchanged and still unanswered, correctly: does Bdo affirm that he directed the act
recorded at entries 118 to 123 of `node:local`, in the words quoted in
`office_act.direction`? Putting it to him is the right disposition; nothing in the
repository can answer it.

### Commands

```
git clone --no-local <this worktree> <clone>; checkout 575d65f   tree e9d7359, porcelain empty
python3 scripts/verify.py                                        exit 0  PASS: 52 checks in 15.030s
python3 scripts/lint.py                                          exit 0  1230 text files, 10 named debt
python3 scripts/sov_node.py journals                             exit 0
python3 -m unittest scripts.tests.test_sov_node_journal          exit 0  23 tests
python3 scripts/sov_surface.py check                             exit 0  PASS (the log line is planted)
python3 scripts/sov_witness_layer.py records                     exit 0  31 receipts, 0 unusable
python3 scripts/sov_clarity.py check                             exit 0
python3 scripts/sov_diagrams.py                                  exit 0
twelve adversarial citation cases against journal.grade()        8 as expected, 4 admitted (G3), 2 raised (G1)
ten mutants of scripts/sovnode/journal.py                        8 killed, 2 survived (G2, G4)
ID_KEYS + session_id, then sov_node.py journals                  exit 1 on fresh-e39c72b9 (confirms F3's reason)
the same malformed counts replayed at a13b888                    clean defects, no exception (G1 is a regression)
git merge --no-commit --no-ff b1448ee into a clone of 575d65f    exit 1, one conflict, the generated page only
```

## Pass 1: commit a13b888 (2026-09-07)

**Verdict: RATIFIABLE-WITH-CONDITIONS.** Every claim the builder makes about the
artifact reproduces, including the two the report itself hedges. What holds the
verdict short of clean is not a false claim: it is that the repaired gate now takes
on trust the one field it used to measure, three mutants of the changed code survive
the shipped fixtures, and the session's own attribution drift is disclosed in a note
rather than carried anywhere a later reader of the record would meet it.

- **Commit witnessed:** `a13b888f860a0b866d706f04e9eacd22fda769af`, HEAD of
  `claude/sovereign-phase-1-5-5uzffu`; base `6498fc7b3172476df54882d7b65c47f52366c8c8`;
  candidate tree `789c4348c497bcdccb0e8664c866f954185ff04d`.
- **Working tree witnessed against:** the `<this worktree>` worktree at
  `a13b888`, porcelain empty before every measurement and holding only this
  participant's own deposits after. `git rev-parse HEAD` was re-read before and after
  every command and never moved. Measurements ran in a full-history clone at the same
  commit with empty porcelain; node runs ran against this participant's own restores,
  never against `.local/node-interface`.
- **Observed:** 2026-09-07T17:45Z (UTC).
- **Receipt:** `witness/observations/2026-09-07-office-act-and-citation-observation.json`.
- **Landing record:** `.local/observations/2026-09-07-office-act-and-citation-landing.json`.
- **Principal:** `SOV_PRINCIPAL=principal:claude-fable-5-1` for every command.
- **Independence:** this participant built nothing here and edited no file under
  `scripts/`, `nodes/`, `reports/`, `contracts/` or `services/`.

### Claim

From `git show a13b888`: the node was restored from the committed export
`nodes/node-local/journal/23d3b48086be.json` into an empty state, `sov_fresh.py
open-office` was run in the root seat's name and granted `principal:claude-fable-5-1`
three capabilities, and that principal then read the registry through the node. And:
`_cited_export`/`_grade_citation` let a self-report keep its citation while the node
records more, by pinning the cited head to a position in the node's current chain
instead of to an export filename.

### Observed

**1. The act. Reproduced.** Restoring `a8b989484adf.json` into a scratch node and
querying the restored SQLite store — not the JSON — finds all three grants with the
exact identifiers the report names, at entries 118, 120 and 122, each `granted_by
principal:bdo` and naming `operator_id principal:claude-fable-5-1`:
`grant_fdf1477d279244db` `open:session`, `grant_e37a2885580a4e62` `close:session`,
`grant_553ce95769c74292` `read:registry`. Entry 85 of the same chain has digest
`23d3b48086be...`, and its 85-entry prefix is byte-identical to the export this
commit deletes, read from base `6498fc7`. That prefix carries no grant to
`principal:claude-fable-5-1` and no mention of it anywhere; its seven grants name
`principal:bdo` and `principal:claude-fable-5`.

`sov_fresh.py run --principal principal:claude-fable-5-1 --node-state <my restore>`
exits 0, `PASS`, `registry.resolve` `COMMITTED`, `P15-Q1.1`, `P15-Q1.2` and `P15-Q1.3`
all `holds`, with `foreign_session` and `other_actor_on_this_session` refused
`ACTOR_ATTRIBUTION_MISMATCH` and `beyond_the_grant` refused `AuthorityRefused`. The
same run as `principal:claude-fable-5` also exits 0 with all three predicates holding,
because that principal holds its own grants at entries 5, 7, 55, 57 and 59; so that
run is not the defeating case for this act and should not be read as one.

The defeating case this participant ran instead: the same command as
`principal:claude-fable-5-1` against a restore of the **pre-act** 85-entry export
exits 1, `FAIL`, `registry.resolve` `REFUSED SESSION_IDENTITY_REQUIRED`, `P15-Q1.3`
unmet, and the node says `principal:claude-fable-5-1 holds no live open:session grant
for this operation`. The act is what changed the outcome, and the record already
contains its own copy of that refusal at entries 111 to 117.

The report's identity claims are record-borne: entry 154 is a
`gateway-authority-check` naming `authority_grant_id grant_553ce95769c74292`,
`required_authority read:registry`, `decision ALLOWED`, inside session
`session_5bbe1d42cdd64427`, which is entries 149 to 173. The registry digest the
report quotes is the sha256 of `contracts/principals.json` at this commit.

**2. The citation repair. Reproduced.** The 2026-09-06 report cites head
`23d3b48086be...`, which is entry 85 of the 173-entry chain; it declares 85 entries,
which is that position; and the nine entry ids it names are all inside the prefix.
`python scripts/sov_node.py journals` exits 0. Independently constructed cases refuse
as claimed: a node with no export, a head that is not an entry of the chain, an entry
recorded after the cited head, a `journal` field with no head, and a traversal
address. A head that a twin node reaches only *later* is caught, because an entry
digest binds `prev_digest`, so finding the cited head in the chain proves the whole
prefix under it.

**3. What it weakened.** See F1 and F2. The node-directory derivation cannot resolve
to a *different* node — `nodes/node-other/...` fails on the directory prefix — but it
does resolve any path under the right node directory, including one naming a file
that never existed.

**4. Gates.** On a clean full-history clone at `a13b888`, empty porcelain:

| command | exit | reading |
| --- | --- | --- |
| `python3 scripts/verify.py` | 0 | `PASS: 52 checks in 15.589s`; wall-clock and per-check budget debt, no semantic failure |
| `python3 scripts/lint.py` | 0 | `PASS: repository hygiene (1225 text files, 562 Python modules, 10 named debt)` |
| `python3 scripts/sov_node.py journals` | 0 | one export replays; every citation resolves (run twice) |
| `python3 -m unittest scripts.tests.test_sov_node_journal` | 0 | 16 tests OK (run twice) |
| `python3 scripts/sov_witness_layer.py records` | 0 | 27 receipts, 0 unusable |
| `python3 scripts/sov_clarity.py check` | 0 | scope and receipts current |
| `python3 scripts/sov_diagrams.py` | 0 | 8 views, 0 stale |

The 19 `CONF-*-DEF` lines and the `FAIL: declared refusals no case fires: SELF_GRADED`
line inside the verify log are defeating fixtures and planted cases firing as
declared, not failures; `verify.py`'s own verdict is exit 0. Under `CLAUDE.md` T2,
that green means unchanged, not qualified.

**5. Diff scope.** `git diff --name-status 6498fc7..a13b888` carries exactly the five
declared paths and nothing else. No secret shape, no absolute host path, no weakened
oracle outside the one this change is about. The deleted export loses no evidence: its
85 entries are the exact prefix of the new one, and its bytes remain at `6498fc7`.
`scripts/sovnode/journal.py` is 211 lines.

### Findings

**F1 — the gate now trusts the one field it used to measure.** `_cited_export`
resolves by node directory, so `journal.address` no longer has to name a file that
exists. A report naming `nodes/node-local/journal/dddddddddddd.json`, or
`nodes/node-local/not-a-journal/z.json`, with a true head, a true count and true entry
ids, passes with no defect. This is not hypothetical: the 2026-09-06 report's address
`nodes/node-local/journal/23d3b48086be.json` is deleted **by this commit**, and the
`verify` command that report prints for a reader now names a file that is not in the
tree — and `journals` says every citation resolves. The head pin is a measurement and
is sound; the address is a declaration next to it, and the gate could compare the two
for the price of one line. Cheapest repair inside the concern: report the resolved
export when it differs from the cited address, or repair the older report's address,
or drop the field to the node and keep the head as the pin.

**F2 — three mutants of the changed code survive the shipped fixtures.** Nine were
run; six die. Survivors: the entry-count check weakened from `!= position` to
`> position`, so a report may under-declare what it read and pass — the suite only
ever over-declares; the node derivation weakened from the node directory to the
journal directory, so the granularity the new docstring asserts has no fixture; and
the head matched by `startswith` instead of equality, which would admit the
12-character head prefix this repository uses for its own export filenames. Each needs
one case.

**F3 — most of the report's identities are outside the gate's reach.** `ID_KEYS` is
`("entry_id", "receipt_id")`, unchanged. A constructed report naming
`grant_never_recorded_0000` and `session_never_recorded` passes. The new docstring
says "the report may name only entries that existed at that head", which is broader
than what `_ids_in` enforces. In the subject report, three of about twelve
record-borne identities are graded; this participant checked the rest by hand and all
are true.

**F4 — a version number doing a contract's work.** `observation_schema:
soveraeign-fresh-participation-live-node/v3`. That identifier, and `v1` and `v2`
before it, appear nowhere in the repository except in the three reports declaring
them. No schema document, nothing validating against one.

**F5 — the direction is not in the record.** `open-office` takes `--direction` and
`--directed-in` and writes them to `<node-state>/office-acts.ndjson`, which is
gitignored runtime state; the journal entries carry `granted_by` and no direction. So
the only surviving attribution of the act to Bdo is prose in the builder's own report,
which is the artifact that cannot witness itself. The report says that plainly, and
the command's own docstring says the act line "proves nothing the journal does not".
Both are honest. The gap is real anyway, and it is the reason this observation
supports no standing for the authorization.

**F6 — the model drift is noted, not seamed.** The report states that the serving
model became Claude Opus 5 partway through while the session kept declaring
`principal:claude-fable-5-1`. `contracts/principals.json` still describes that
principal as "the model the host reports serving this node's interactive sessions
since 2026-09-06", and this commit leaves it there while adding about sixty journal
entries whose actor is that principal, with no counter-record. Principal identity and
naming are owner-held under `contracts/acceptance-policy.json`, so the fix is not the
builder's to make alone — but a disclosure in a JSON `note` field is neither
presented nor held at a named seam.

**F7 — the narrative is incomplete, in the builder's own favour.** The export carries
88 entries past the restored prefix; the report narrates the office act and one run.
Unreported: entries 86–110, a committed run as `principal:claude-fable-5`; entries
111–117, `principal:claude-fable-5-1` refused `NO_LIVE_GRANT` before the act, which is
the live defeating case and the strongest thing in the file; and entries 124–148, an
earlier committed run. The report names the later run, which is correct.

**F8 — the witness deposit turns the tree red, and that is the landing path's
problem, not the change's.** `verify.py` exits 0 on a clean clone at `a13b888` and
exits 1 on this worktree once this witness's own two deposits exist, because
`sov_docs.py` counts every document under `witness/`; `docs/documentation.html` and
`docs/surface.html` then read stale. Attributed by moving the two deposits aside and
re-running `python scripts/sov_docs.py check`, which returns to `PASS: documentation
page matches 286 documents`. No defect of the builder's is involved. It matters
because `sov_land.py` runs verify before its gate, so absorbing a witness record means
rebuilding both pages in the same commit or the landing refuses for a reason that has
nothing to do with the work. The `FAIL: 1 defects in the acceptance routing` and
`FAIL: declared refusals no case fires: SELF_GRADED` lines appear in the clean-clone
log too: they are planted cases proving their checks refuse, and reading them as
failures is the trap this repository has already been bitten by.

### Judgement

Two questions this observation cannot answer and does not try to.

1. Does Bdo affirm that he directed the act recorded at entries 118 to 123 of
   `node:local`, in the words quoted in `office_act.direction`? Nothing in the node,
   the export, the report or this witness authenticates who passed the name
   `principal:bdo`. Three grants now stand in the root seat's name on the strength of
   a self-report.
2. Should `contracts/principals.json` be amended, or a counter-record recorded in the
   node, now that acts attributed to `principal:claude-fable-5-1` were performed by a
   differently-versioned serving model?

### Standing

**BUILT -> WITNESSED** for the citation-gate repair in `scripts/sovnode/journal.py`,
and for the office act and the live reading **as facts of `node:local`'s journal at
`a13b888`**. Not supported: any claim that the root seat authorized the act. This
observation settles nothing; it is an observation, not a ratification.

### Commands

```
git clone --no-local <this worktree> <clone>          exit 0
git -C <clone> checkout a13b888                                exit 0  tree 789c4348, porcelain empty
python3 scripts/sov_node.py restore-journal --export nodes/node-local/journal/a8b989484adf.json
    --node-state <scratch> --expect-head a8b989484adf...       exit 0  173 entries
python3 scripts/sov_fresh.py run --principal principal:claude-fable-5-1 --node-state <scratch>
                                                               exit 0  PASS, three predicates hold
python3 scripts/sov_fresh.py run --principal principal:claude-fable-5 --node-state <scratch2>
                                                               exit 0  PASS, three predicates hold
python3 scripts/sov_fresh.py run --principal principal:claude-fable-5-1 --node-state <pre-act>
                                                               exit 1  FAIL, P15-Q1.3 unmet
python3 scripts/verify.py                                      exit 0  PASS: 52 checks
python3 scripts/lint.py                                        exit 0
python3 scripts/sov_node.py journals                           exit 0  (twice)
python3 -m unittest scripts.tests.test_sov_node_journal        exit 0  16 tests (twice)
python3 scripts/sov_witness_layer.py records                   exit 0
python3 scripts/sov_clarity.py check                           exit 0
python3 scripts/sov_diagrams.py                                exit 0
nine-mutant run over scripts/sovnode/journal.py                6 killed, 3 survived
nine adversarial citation cases against journal.grade()        6 refused as expected, 3 admitted (F1, F3)
```
