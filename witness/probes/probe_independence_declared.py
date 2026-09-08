"""Witness pass 3's adversarial probes: the executor's own word, read faithfully.

Pass 3's construction, checked in. Its four slices are one argument: every field this walk
reads to establish independence is written by the party being graded, so a record can be read
perfectly and still describe an independence that was declared rather than found.

Three of the four still reach `INDEPENDENT` at the commit that checked this in, and that is
deliberate. `F3` and its tail are not repaired and are not repairable at this boundary; they
are `services/observation/KNOWN-GAPS.md`'s first two rows and `decisions/0104`'s fourth
judgement item. Run them to see the property the walk actually has. `F1` and `F2` were
repaired, and run against `3c24420` they show what they found.

Reshaped from four scripts and a helper module into one file with a `main()` and declared
reach targets, which is the shape `scripts/sovwitness/probes.py` grades. Where a slice asserted
admission by calling the gate bare, the call is wrapped so a refusal prints instead of aborting
the run - three of the four are repaired now and the gate refuses them. No slice was otherwise
altered; the records they build and the readings they take are the witness's.

Not a test. Nothing in `verify.py` runs these.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: What this probe reaches. It takes no binding, no CLI and no journal.
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
from soveraeign_observation_service.admission import require_independent  # noqa: E402
from soveraeign_observation_service.relation import EDGES, infer_relation  # noqa: E402



def dg(seed: str) -> str:
    return "sha256:" + hashlib.sha256(seed.encode()).hexdigest()

_n = [0]
def E(kind, subject, actor, payload):
    _n[0] += 1
    eid = f"urn:e:{_n[0]:04d}"
    return {"entry_id": eid, "kind": kind, "subject": subject, "actor": actor,
            "payload": payload, "entry_digest": dg(eid)}

def EV(subject, actor, event, **kw):
    p = {"event": event}; p.update(kw)
    return E("EVENT", subject, actor, p)

def walk(entries, run_id, cand, kind="AGENT", at="2026-09-08T00:00:00Z"):
    rec = RunRecord.from_entries(run_id, entries)
    return rec, infer_relation(rec, cand, kind, at)

def show(name, inf):
    print(f"{name:<46} {inf['outcome']:<13} {inf['record_completeness']:<10} "
          f"found={[e['edge'] for e in inf['edges_found']]} "
          f"unans={inf.get('unanswerable_edges', [])}")
    return inf

PEXEC, PCAND = dg("profile:builder"), dg("profile:witness")

def launch(actor, prof, ctx=("OBJECTIVE", "ARTIFACT"), kind="CONTRACT", author=None):
    p = {"event": "LAUNCH", "launched_actor_id": actor, "launched_by": "orch",
         "context_passed": list(ctx), "profile": {"address": "urn:p:" + actor, "digest": prof},
         "predicates_source_kind": kind}
    if author: p["predicates_source_actor"] = author
    return E("EVENT", actor, "orch", p)

def baseline(subject="urn:s:WORK-1", lease_holder="exec", cand="wit"):
    return [
        launch("exec", PEXEC), launch(cand, PCAND),
        EV("urn:run:1", "exec", "ATTEMPTED", subject_id=subject,
           lease={"holder_id": lease_holder}, grant_id="urn:g:1"),
        EV("urn:run:1", "exec", "REPORTED", output_record_addresses=["urn:out:1"]),
        EV("urn:out:1", "exec", "OUTPUT", digest=dg("out1")),
        EV(subject, "exec", "STANDING", **{"from": "OPEN", "to": "BUILT"}),
    ]


def main() -> int:
    """Run each slice and print its reading, then the reach report."""
    print("\n=== F1 - the corroborated decoy ===")
    print("== A. baseline sanity ==")
    rec, inf = walk(baseline(), "urn:run:1", "wit"); show("A0 clean witness", inf)
    try:
        require_independent(inf, "wit", "urn:run:1", rec)
        print("   admitted: yes")
    except Exception as refusal:
        print(f"   refused: {refusal}")
    rec, inf = walk(baseline(), "urn:run:1", "exec"); show("A1 executor as observer", inf)
    print("\n=== F2 - the correctly hashed forgery ===")
    print("== B1. executor declares lease:null while candidate really holds it ==")
    e = baseline(lease_holder="wit")
    rec, inf = walk(e, "urn:run:1", "wit"); show("B1a truthful lease -> holder is cand", inf)
    e2 = [dict(x) for x in e]
    for x in e2:
        if x["payload"].get("event") == "ATTEMPTED": x["payload"] = dict(x["payload"], lease=None)
    rec, inf = walk(e2, "urn:run:1", "wit"); show("B1b same run, lease rewritten null", inf)
    try:
        require_independent(inf, "wit", "urn:run:1", rec); print("   ADMITTED -- lease edge erased by fiat")
    except Exception as ex: print("   refused:", ex)

    print()
    print("== B2. decoy subject the executor also touched (corroboration satisfied) ==")
    # Real work S1: the candidate moved OPEN->BUILT on it. It is in the record, visible.
    # Executor names S2 as the run's subject and has its own arrow there.
    e = [
        launch("exec", PEXEC), launch("wit", PCAND),
        EV("urn:run:1", "exec", "ATTEMPTED", subject_id="urn:s:DECOY",
           lease={"holder_id": "exec"}, grant_id="urn:g:1"),
        EV("urn:run:1", "exec", "REPORTED", output_record_addresses=["urn:out:1"]),
        EV("urn:out:1", "exec", "OUTPUT", digest=dg("out1")),
        EV("urn:s:REAL", "wit", "STANDING", **{"from": "OPEN", "to": "BUILT"}),   # cand built the real work
        EV("urn:s:REAL", "exec", "STANDING", **{"from": "BUILT", "to": "WITNESSED"}),
        EV("urn:s:DECOY", "exec", "STANDING", **{"from": "OPEN", "to": "BUILT"}), # executor's throwaway
    ]
    rec, inf = walk(e, "urn:run:1", "wit"); show("B2 decoy + corroboration", inf)
    try:
        require_independent(inf, "wit", "urn:run:1", rec)
        print("   ADMITTED -- candidate's own arrow on the real subject is in the record and unread")
    except Exception as ex: print("   refused:", ex)

    print()
    print("== B3. legitimate observer locked out: no executor arrow on the true subject ==")
    e = [
        launch("exec", PEXEC), launch("wit", PCAND),
        EV("urn:run:1", "exec", "ATTEMPTED", subject_id="urn:s:WORK-1",
           lease={"holder_id": "exec"}, grant_id="urn:g:1"),
        EV("urn:run:1", "exec", "REPORTED", output_record_addresses=["urn:out:1"]),
        EV("urn:out:1", "exec", "OUTPUT", digest=dg("out1")),
        EV("urn:s:WORK-1", "orch", "STANDING", **{"from": "NONE", "to": "OPEN"}),  # a seat opened it
    ]
    rec, inf = walk(e, "urn:run:1", "wit"); show("B3 honest record, seat-opened subject", inf)

    print()
    print("== B4. candidate IS the prior standing actor, no executor arrow ==")
    e2 = list(e) + [EV("urn:s:WORK-1", "wit", "STANDING", **{"from": "OPEN", "to": "BUILT"})]
    rec, inf = walk(e2, "urn:run:1", "wit"); show("B4 candidate built the subject", inf)
    print("\n=== F3 - the executor-authored profile ===")
    # The record is the honest one: `exec` attempted, reported, produced, holds the lease,
    # and moved the subject. The real walk calls it DIRECT on four edges.
    entries = baseline()
    rec, honest = walk(entries, "urn:run:1", "exec")
    print("real walk for exec :", honest["outcome"], [e["edge"] for e in honest["edges_found"]])

    AT = "2026-09-08T00:00:00Z"
    material = f"urn:run:1|exec|{AT}".encode()
    forged = {
        "inference_id": "urn:soveraeign:observation:relation-inference:"
                        + hashlib.sha256(material).hexdigest()[:24],
        "run_id": "urn:run:1", "candidate_observer_id": "exec",
        "candidate_observer_kind": "AGENT", "executor_id": "exec",
        "edges_examined": list(EDGES), "edges_found": [],
        "record_completeness": "COMPLETE", "outcome": "INDEPENDENT",
        "evidence_addresses": [], "evidence_digests": [], "inferred_at": AT,
    }
    print("forged id == real id:", forged["inference_id"] == honest["inference_id"])
    try:
        require_independent(forged, "exec", "urn:run:1", rec)
        print(">>> ADMITTED: the run's own executor, over its own honest record.")
    except Exception as ex:
        print("refused:", ex)
    print("\n=== F3 tail - the executor-authored null lease ===")
    entries = baseline()
    rec, _ = walk(entries, "urn:run:1", "exec")
    AT = "2026-09-08T00:00:00Z"

    def forge(run, cand, at, **over):
        m = f"{run}|{cand}|{at}".encode()
        d = {"inference_id": "urn:soveraeign:observation:relation-inference:"
                             + hashlib.sha256(m).hexdigest()[:24],
             "run_id": run, "candidate_observer_id": cand, "candidate_observer_kind": "AGENT",
             "executor_id": "exec", "edges_examined": list(EDGES), "edges_found": [],
             "record_completeness": "COMPLETE", "outcome": "INDEPENDENT",
             "evidence_addresses": [], "evidence_digests": [], "inferred_at": at}
        d.update(over); return d

    payload = b"{\"claim\":\"the build is good\"}"
    for _e in entries:
        if _e["payload"].get("event") == "OUTPUT": _e["payload"]["digest"] = "sha256:" + _h.sha256(payload).hexdigest()
    rec, _ = walk(entries, "urn:run:1", "exec")
    decl = declare_predicates("urn:run:1", [{"predicate_id": "p1", "kind": "BYTES_PRESENT",
                                             "address": "urn:out:1"}], "2026-09-07T00:00:00Z")

    print("== D1. the executor observes its own run through the exported surface ==")
    obs = observe_run(rec, forge("urn:run:1", "exec", AT), decl, "exec",
                      lambda a: payload, "2026-09-08T01:00:00Z")
    print("  observation minted. verdict :", obs.get("outcome") or obs.get("verdict"))
    print("  observer_id                 :", obs.get("observer_id"))
    print("  observer_relation           :", repr(obs["observer_relation"]))

    print()
    print("== D2. same, but citing real addresses so the new evidence check is satisfied ==")
    addrs = [RunRecord.address_of(e) for e in rec.entries][:3]
    digs  = [RunRecord.digest_of(e) for e in rec.entries][:3]
    obs2 = observe_run(rec, forge("urn:run:1", "exec", AT, evidence_addresses=addrs,
                                  evidence_digests=digs), decl, "exec",
                       lambda a: payload, "2026-09-08T01:00:00Z")
    print("  observer_relation           :", repr(obs2["observer_relation"]))

    json.dump({
        "subject": "services/observation independence walk, declared-field surface",
        "reached_through": "infer_relation and the package's exported observe_run, in "
                           "process, over journal slices this probe builds",
        "not_reached": ["the service facade", "any real run or Record Service journal"],
    }, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
