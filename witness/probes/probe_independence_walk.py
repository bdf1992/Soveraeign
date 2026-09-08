"""Witness pass 2's adversarial probes over the seven-edge independence walk.

The witness's own construction, checked in: its own entry builder, its own actors and
profiles, no reuse of the service's `journal()` fixture and none of pass 1's probes. Two
things were changed and nothing else: absolute paths became repository-relative, and the flat
run of slices was moved into `main()` with a reach report, which is the shape
`scripts/sovwitness/probes.py` grades a checked-in probe against. The readings are the
witness's.

Pass 1 kept no probe, so its five defeats are prose in
`witness/independence-context-perspective.md` and are not re-derivable from that record. Pass 2
had to build its own from scratch and said so; these bytes are here so the next reader does
not. Several slices now refuse where they once admitted - run them against `7be1323` to see the
defects and against this commit to see the repairs.

Not a test. Nothing in `verify.py` runs the slices; this is evidence of a reading.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: What this probe reaches: the service's own source, and the kernel helpers it validates
#: against. It reaches no binding, no CLI and no journal, which is what the reach report says.
SERVICE_SRC = ROOT / "services" / "observation" / "src"
KERNEL_SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SERVICE_SRC))
sys.path.insert(0, str(KERNEL_SCRIPTS))

from soveraeign_observation_service import (  # noqa: E402
    ObservationService,
    RunRecord,
    declare_predicates,
    observe_run,
)
from soveraeign_observation_service.relation import EDGES, infer_relation  # noqa: E402


RUN = "urn:sov:run:R9"
SUBJ = "urn:sov:work:W9"
OUT = "out/alpha"
BYTES = b'{"k": 1}'
DIG = hashlib.sha256(BYTES).hexdigest()

def prof(n):
    return {"address": f"p/{n}", "digest": hashlib.sha256(f"p:{n}".encode()).hexdigest()}

P_BUILD, P_WIT, P_HELP = prof("builder"), prof("witness"), prof("helper")

def E(i, kind, subj, actor, payload):
    return {"entry_id": i, "kind": kind, "subject": subj, "actor": actor,
            "payload": payload,
            "entry_digest": hashlib.sha256(f"{i}{subj}{actor}".encode()).hexdigest()}

def base(*, lease_holder="builder-1", out_actor="builder-1", ctx=("OBJECTIVE","ARTIFACT"),
         cand="witness-z", cand_prof=P_WIT, pkind="CONTRACT", pauthor="contract:obs",
         extra=()):
    """A clean, complete record: builder-1 ran it, cand is launched fresh."""
    e = [
      E("j1","EVENT",RUN,"builder-1",{"event":"ATTEMPTED","subject_id":SUBJ,
        "lease":{"holder_id":lease_holder,"fence":1},"grant_id":"g1","profile":P_BUILD}),
      E("j2","EVENT",RUN,"builder-1",{"event":"REPORTED","output_record_addresses":[OUT],
        "profile":P_BUILD}),
      E("j3","EVENT",OUT,out_actor,{"event":"OUTPUT","digest":DIG}),
      E("j4","EVENT","g1","root",{"event":"GRANT","holder_id":"builder-1","parent_grant_id":None}),
      E("j5","EVENT",cand,"launcher",{"event":"LAUNCH","launched_actor_id":cand,
        "launched_by":"launcher","profile":cand_prof,
        "context_passed":list(ctx),"predicates_source_kind":pkind,
        "predicates_source_actor":pauthor}),
      E("j6","EVENT","builder-1","root",{"event":"LAUNCH","launched_actor_id":"builder-1",
        "launched_by":"root","profile":P_BUILD,"context_passed":["OBJECTIVE"],
        "predicates_source_kind":"CONTRACT","predicates_source_actor":"contract:obs"}),
      E("j7","EVENT",SUBJ,"builder-1",{"event":"STANDING","from":"OPEN","to":"BUILT"}),
      E("j8","RECEIPT",RUN,"kernel",{"outcome":"COMMITTED"}),
    ]
    return list(e) + list(extra)

def verdict(entries, cand="witness-z"):
    rec = RunRecord.from_entries(RUN, entries)
    inf = infer_relation(rec, cand, "MODEL", "2026-09-08T00:00:00Z")
    return rec, inf

def show(label, entries, cand="witness-z"):
    rec, inf = verdict(entries, cand)
    print(f"{label}: outcome={inf['outcome']} completeness={inf['record_completeness']} "
          f"found={[e['edge'] for e in inf['edges_found']]} "
          f"unans={inf.get('unanswerable_edges')}")
    return rec, inf


def main() -> int:
    """Run every slice, print its reading, then a machine-readable reach report."""
    print("=== control: clean record, fresh witness ===")
    show("C0 clean", base())

    print()
    print("=== D1: context kind the service does not recognise ===")
    show("D1a ctx=['TRANSCRIPT'] (known)", base(ctx=("TRANSCRIPT",)))
    show("D1b ctx=['transcript'] (lowercase)", base(ctx=("transcript",)))
    show("D1c ctx=['CONCLUSIONS'] (plural)", base(ctx=("CONCLUSIONS",)))
    show("D1d ctx=['FULL_BUILD_CONTEXT']", base(ctx=("FULL_BUILD_CONTEXT",)))
    show("D1e ctx=[] (empty list)", base(ctx=()))

    print()
    print("=== D2: candidate is a VERSION of the lease holder (a non-executor) ===")
    # helper-h held the run lease; witness candidate 'helper-h2' loads helper-h's profile.
    extra = [E("j9","EVENT","helper-h","root",{"event":"LAUNCH","launched_actor_id":"helper-h",
               "launched_by":"builder-1","profile":P_HELP,"context_passed":["OBJECTIVE"],
               "predicates_source_kind":"CONTRACT","predicates_source_actor":"contract:obs"})]
    show("D2 lease holder=helper-h, cand=helper-h2 with helper's profile",
         base(lease_holder="helper-h", cand="helper-h2", cand_prof=P_HELP, extra=extra),
         cand="helper-h2")
    show("D2ctl same but cand IS helper-h",
         base(lease_holder="helper-h", cand="helper-h", cand_prof=P_HELP), cand="helper-h")

    print()
    print("=== D3: candidate is a VERSION of the output producer (a non-executor) ===")
    show("D3 output actor=helper-h, cand=helper-h2 with helper's profile",
         base(out_actor="helper-h", cand="helper-h2", cand_prof=P_HELP, extra=extra),
         cand="helper-h2")

    print()
    print("=== D4: forged inference handed straight to observe_run ===")
    rec = RunRecord.from_entries(RUN, base())
    forged = {"inference_id":"urn:sov:observation:relation-inference:FORGED",
              "run_id":RUN,"candidate_observer_id":"builder-1",
              "candidate_observer_kind":"MODEL","executor_id":"builder-1",
              "edges_examined":list(EDGES),"edges_found":[],
              "record_completeness":"COMPLETE","outcome":"INDEPENDENT",
              "evidence_addresses":[],"evidence_digests":[],
              "inferred_at":"2026-09-08T00:00:00Z"}
    decl = declare_predicates(RUN, [{"predicate_id":"p1","kind":"BYTES_PRESENT","address":OUT}],
                              "2026-09-08T00:00:00Z")
    try:
        obs = observe_run(rec, forged, decl, "builder-1", lambda a: BYTES,
                          "2026-09-08T01:00:00Z")
        print("D4 ADMITTED:", obs["observer_id"], "|", obs["observer_relation"][:90])
    except Exception as ex:
        print("D4 refused:", type(ex).__name__, ex)

    print()
    print("=== D5: predicate source kind closure (control for D1's open vocabulary) ===")
    show("D5a pkind='ACTOR' author=builder-1", base(pkind="ACTOR", pauthor="builder-1"))
    show("D5b pkind='GUIDELINE' (unknown kind)", base(pkind="GUIDELINE", pauthor="x"))
    show("D5c pkind absent", base(pkind=None, pauthor=None))

    print()
    print("=== Q4: does an experienced witness become permanently unattestable? ===")
    # witness-z legitimately witnessed a DIFFERENT subject last week. Same journal.
    other = [E("j10","EVENT","urn:sov:work:OTHER","witness-z",
               {"event":"STANDING","from":"BUILT","to":"WITNESSED"})]
    show("Q4a witness-z moved another subject once", base(extra=other))
    # and if the other-subject arrow was moved by an unrelated third party?
    other2 = [E("j11","EVENT","urn:sov:work:OTHER","stranger-s",
                {"event":"STANDING","from":"BUILT","to":"WITNESSED"})]
    show("Q4b a STRANGER moved another subject (no profile on file)", base(extra=other2))
    other3 = [E("j12","EVENT","urn:sov:work:OTHER","stranger-s",
                {"event":"STANDING","from":"BUILT","to":"WITNESSED"}),
              E("j13","EVENT","stranger-s","root",{"event":"LAUNCH","launched_actor_id":"stranger-s",
                "launched_by":"root","profile":prof("stranger"),"context_passed":["OBJECTIVE"],
                "predicates_source_kind":"CONTRACT","predicates_source_actor":"c"})]
    show("Q4c stranger WITH a profile on file", base(extra=other3))

    print()
    print("=== Q1b: is a legitimate observer still reachable at all? ===")
    for name, kw in [("no LAUNCH entry for candidate", dict(cand="unlaunched-q")),
                     ("run names no subject_id", {}),
                     ("no STANDING arrow on the subject", {})]:
        pass
    ents = [e for e in base() if e["entry_id"] != "j5"]
    show("Q1b1 candidate has no LAUNCH entry", ents)
    ents = [e for e in base() if e["entry_id"] != "j7"]
    show("Q1b2 subject has no STANDING arrow yet (first ever witness)", ents)
    ents = []
    for e in base():
        if e["entry_id"] == "j1":
            e = dict(e); p = dict(e["payload"]); p.pop("subject_id"); e["payload"] = p
        ents.append(e)
    show("Q1b3 run declares no subject_id", ents)

    print()
    print("=== M2 reachability: relay by an executor session with NO profile on file ===")
    ents = base()
    # worker sibling 'builder-1b' exists only as a bare id: no LAUNCH, no attempt. UNKNOWN.
    rec = RunRecord.from_entries(RUN, ents)
    decl = declare_predicates(RUN, [{"predicate_id":"p1","kind":"BYTES_PRESENT","address":OUT}],
                              "2026-09-08T00:00:00Z")
    inf = infer_relation(rec, "witness-z", "MODEL", "2026-09-08T00:00:00Z")
    for relay in ["builder-1", "builder-1b"]:
        try:
            observe_run(rec, inf, decl, "witness-z", lambda a: BYTES, "2026-09-08T01:00:00Z",
                        submitted_by=relay)
            print(f"  relay by {relay}: ADMITTED")
        except Exception as ex:
            print(f"  relay by {relay}: refused ({type(ex).__name__})")

    print()
    print("=== W3 through the SERVICE FACADE: can a declared relation reach observe-run? ===")
    svc = ObservationService(lambda: "2026-09-08T01:00:00Z")
    svc.declare_predicates(RUN, [{"predicate_id":"p1","kind":"BYTES_PRESENT","address":OUT}])
    svc.declarations[-1]["declared_at"] = "2026-09-08T00:00:00Z"
    svc.inferences.append({"inference_id":"urn:x:FORGED","run_id":RUN,
        "candidate_observer_id":"builder-1","candidate_observer_kind":"MODEL",
        "executor_id":"builder-1","edges_examined":list(EDGES),"edges_found":[],
        "record_completeness":"COMPLETE","outcome":"INDEPENDENT",
        "evidence_addresses":[],"evidence_digests":[],"inferred_at":"2026-09-08T00:00:00Z"})
    try:
        o = svc.observe_run(rec, "builder-1", lambda a: BYTES)
        print("  facade ADMITTED the executor as its own observer:", o["observation_id"])
    except Exception as ex:
        print("  facade refused:", type(ex).__name__, ex)

    print()
    print("=== W3b: is the inference_id self-certifying and unchecked? ===")
    real = infer_relation(rec, "witness-z", "MODEL", "2026-09-08T00:00:00Z")
    mat = f"{RUN}|witness-z|2026-09-08T00:00:00Z".encode()
    recomputed = "urn:soveraeign:observation:relation-inference:" + hashlib.sha256(mat).hexdigest()[:24]
    print("  real id      :", real["inference_id"])
    print("  recomputable :", recomputed, "->", real["inference_id"] == recomputed)

    json.dump({
        "subject": "services/observation independence walk",
        "reached_through": "soveraeign_observation_service.infer_relation and the package's "
                           "exported observe_run, in process, over journal slices this probe "
                           "builds",
        "not_reached": ["the service facade's own request and declare path",
                        "any real run, and any Record Service journal"],
    }, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
