"""Perform ``settle_run``: judge through the kernel, then append the receipt.

The thin circuit (``reports/2026-09-05-thin-circuit-1.md``, item 4) found that
``settle_run`` had a judge and no participant: ``sov_kernel.py check`` returned
``PERMITTED`` and the controller appended the receipt by hand. This module is
that participant, on the terms ``decisions/0104-settlement-at-three-scales.md``
rules: the act lives beside the judge it uses, and it decides nothing ``check``
does not. Both call ``judge`` below, one function.

The act has two parts, in order (0104, rulings 1 and 2). The run-level
settlement is a RECEIPT on the run subject, appended through the Record Service
command line as a subprocess, never by importing the service
(``services/record/CHARTER.md``: the Record decides no legality, so legality is
decided here and only the entry crosses). With ``--concern`` a RECONCILED event
follows on the concern subject, which is the RECONCILE step
``contracts/concern-admission.json`` names after landing.

What the journal says is measured rather than trusted. The run's reporters, the
observation named by the request, every earlier ``settle_run`` receipt and every
COUNTER naming one are read from the store at the moment of the request. A run
with an un-countered ``settle_run`` receipt is already settled and is refused
with the kernel's declared word ``STALE_STATE`` ("already settled: <entry>");
a run whose every receipt is countered is open again and may settle. The actor
that reported the run or made its observation is refused
``SELF_SETTLEMENT_REFUSED`` (0104, ruling 1: "the act refuses when the settler
is the reporter or the observer"; the code is the one
``contracts/tier-bindings.json`` declares). A Record crossing that does not
answer is ``SERVICE_UNREACHABLE``, the code ``gateway.route-request`` declares
in ``contracts/fixtures/capability-map.reference.json`` for a service that did
not answer; this module has no manifest of its own, so the word is borrowed,
not minted. Nothing here grants authority; a permitted, appended receipt is a
recorded settlement, not a witnessed one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import os
import subprocess
import sys

from sovkernel import transitions as kernel
from sovkernel.jsonschema import validate

TRANSITION = "settle_run"
RELATIONS = ("advances", "satisfies", "supersedes")
RECORD_SOURCE = Path("services") / "record" / "src"
#: How much of the Record CLI's stderr a refusal carries; a traceback's last lines name
#: the cause and the rest is noise a caller can reproduce.
STDERR_LIMIT = 600


class Refusal(Exception):
    """One named refusal; ``appended`` lists entries already written before it fired."""

    def __init__(self, code: str, detail: str, exit_code: int = 2,
                 appended: list[dict[str, Any]] | None = None) -> None:
        super().__init__(detail)
        self.code, self.detail, self.exit_code = code, detail, exit_code
        self.appended = appended or []
        self.measured: dict[str, Any] | None = None


def judge(root: Path, request: dict[str, Any],
          current: dict[str, Any]) -> tuple[list[str], kernel.Decision | None]:
    """The one judgement ``check`` and ``settle`` share: schema, then the kernel table."""
    schema = json.loads((root / "contracts" / "transition.schema.json").read_text("utf-8"))
    defects = validate(request, schema)
    if defects:
        return defects, None
    return [], kernel.evaluate(request, kernel.load_table(root), current)


def record(root: Path, store: Path, *args: str) -> tuple[int, str, str]:
    """Run one Record Service command as a subprocess; return exit code, stdout, stderr."""
    env = dict(os.environ)
    source = str(root / RECORD_SOURCE)
    env["PYTHONPATH"] = source + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, "-m", "soveraeign_record_service.cli", "--root", str(store), *args],
        capture_output=True, text=True, env=env, cwd=str(root), check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _record_json(root: Path, store: Path, *args: str,
                 appended: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    code, out, err = record(root, store, *args)
    if code != 0:
        tail = (err.strip() or out.strip())[-STDERR_LIMIT:]
        raise Refusal("SERVICE_UNREACHABLE",
                      f"record cli exited {code} for {args[0]} at {store}: {tail}",
                      appended=appended)
    return json.loads(out)


def measure(entries: list[dict[str, Any]], run_id: str,
            observation_id: str | None) -> dict[str, Any]:
    """What the journal says about this run, read from its entries rather than a report.

    ``standing`` is every ``settle_run`` receipt on the run that no COUNTER names. Counters
    are collected from the whole journal, not the run subject, so a counter filed under
    another subject still counts; only counters naming this run's receipts are kept.
    """
    reporters: list[str] = []
    observation: dict[str, Any] | None = None
    receipts: list[dict[str, Any]] = []
    countered: set[str] = set()
    for entry in entries:
        payload = entry.get("payload") or {}
        if entry["kind"] == "COUNTER" and payload.get("counters"):
            countered.add(payload["counters"])
            continue
        if entry.get("subject") != run_id:
            continue
        if entry["kind"] == "EVENT" and payload.get("event") == "REPORTED":
            reporters.append(entry["actor"])
        if entry["kind"] == "OBSERVATION" and observation_id and (
                (payload.get("observation") or {}).get("observation_id") == observation_id):
            observation = entry
        if entry["kind"] == "RECEIPT" and payload.get("event") == TRANSITION:
            receipts.append(entry)
    receipt_ids = {entry["entry_id"] for entry in receipts}
    return {"reporters": reporters, "observation": observation, "receipts": receipts,
            "countered": sorted(countered & receipt_ids),
            "standing": [entry for entry in receipts if entry["entry_id"] not in countered]}


def already_settled(measured: dict[str, Any]) -> Refusal | None:
    """An un-countered settle_run receipt is the run's current state; a new one is stale."""
    if measured["standing"]:
        return Refusal("STALE_STATE", f"already settled: {measured['standing'][-1]['entry_id']}")
    return None


def self_settlement(actor: str, request: dict[str, Any], current: dict[str, Any],
                    measured: dict[str, Any]) -> Refusal | None:
    """The actor that produced a report, or observed it, may not settle it (0104, ruling 1)."""
    producers = {current.get("reporter_id"), *measured["reporters"]}
    observers = {(request.get("observation") or {}).get("observer_id")}
    if measured["observation"] is not None:
        payload = measured["observation"]["payload"]
        observers.add(payload.get("observer_id"))
        observers.add((payload.get("observation") or {}).get("observer_id"))
    if actor in producers:
        return Refusal("SELF_SETTLEMENT_REFUSED", f"{actor} produced the report it would settle")
    if actor in observers:
        return Refusal("SELF_SETTLEMENT_REFUSED",
                       f"{actor} made the observation it would settle on")
    return None


def _measured_view(measured: dict[str, Any]) -> dict[str, Any]:
    observation = measured["observation"]
    return {"reporters": measured["reporters"],
            "observation_entry": None if observation is None else observation["entry_id"],
            "settle_receipts": [entry["entry_id"] for entry in measured["receipts"]],
            "countered": measured["countered"],
            "standing": [entry["entry_id"] for entry in measured["standing"]]}


def perform(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    """Judge, measure, refuse or append. Raises ``Refusal``; returns the success record."""
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    current = json.loads(Path(args.current).read_text(encoding="utf-8")) if args.current else {}
    store = Path(args.record_root)
    if request.get("transition") != TRANSITION:
        raise Refusal("MALFORMED_REQUEST",
                      f"settle performs {TRANSITION} only, not {request.get('transition')!r}", 1)
    declared = request.get("declared") or {}
    journal = _record_json(root, store, "reconstruct-journal")
    measured = measure(journal["entries"], declared.get("run_id"), declared.get("observation_id"))
    try:
        return _settle_measured(root, store, args, request, current, measured)
    except Refusal as refusal:
        # A refusal after the journal was read carries what the journal said.
        refusal.measured = _measured_view(measured)
        raise


def _settle_measured(root: Path, store: Path, args: argparse.Namespace, request: dict[str, Any],
                     current: dict[str, Any], measured: dict[str, Any]) -> dict[str, Any]:
    """Judge against the measured state, then append; every refusal leaves the journal as read."""
    declared = request.get("declared") or {}
    run_id, observation_id = declared.get("run_id"), declared.get("observation_id")

    defects, decision = judge(root, request, current)
    if defects:
        raise Refusal("MALFORMED_REQUEST", "; ".join(defects), 1)
    assert decision is not None
    if not decision.permitted:
        raise Refusal(decision.reason_code or "REFUSED", decision.detail)
    outcome = request.get("requested_outcome")
    terminal = kernel._entry(kernel.load_table(root), TRANSITION)["terminal_outcomes"]
    if outcome not in terminal:
        raise Refusal("MISSING_PRECONDITION",
                      f"{TRANSITION} needs a requested_outcome among {', '.join(terminal)}")
    for refusal in (already_settled(measured),
                    None if measured["observation"] is not None else Refusal(
                        "OBSERVATION_MISSING",
                        f"no OBSERVATION entry on {run_id} at {store} carries {observation_id}"),
                    self_settlement(args.actor, request, current, measured)):
        if refusal is not None:
            raise refusal

    detail = {"kernel_verdict": decision.render(), "observation_id": observation_id,
              "input_state_digest": declared.get("input_state_digest"),
              "settled_by": args.actor}
    receipt = _record_json(
        root, store, "append-receipt", "--outcome", outcome, "--event", TRANSITION,
        "--subject", run_id, "--actor", args.actor, "--detail", json.dumps(detail))
    appended = [{"entry_id": receipt["entry_id"], "seq": receipt["seq"], "kind": "RECEIPT"}]
    result: dict[str, Any] = {
        "outcome": outcome, "verdict": decision.render(), "run_id": run_id,
        "settled_by": args.actor, "record_root": str(store), "measured": _measured_view(measured),
        "receipt": appended[0], "reconcile": None,
    }
    if not args.concern:
        result["reconcile_note"] = "no --concern given; no RECONCILED entry appended"
        return result
    payload = {"event": "RECONCILED", "run_id": run_id, "receipt_entry_id": receipt["entry_id"],
               "relation": args.relation, "basis": args.basis}
    reconcile = _record_json(
        root, store, "append-entry", "--kind", "EVENT", "--subject", args.concern,
        "--actor", args.actor, "--payload", json.dumps(payload), appended=appended)
    result["reconcile"] = {"entry_id": reconcile["entry_id"], "seq": reconcile["seq"],
                           "concern": args.concern, "relation": args.relation}
    return result


def command_settle(args: argparse.Namespace, root: Path) -> int:
    """CLI handler: one JSON object on stdout; 0 appended, 2 refused, 1 malformed usage."""
    if args.concern and not (args.relation and args.basis):
        print(json.dumps({"outcome": "REFUSED", "reason_code": "MALFORMED_REQUEST",
                          "detail": "--concern needs --relation and --basis"}))
        return 1
    try:
        result = perform(root, args)
    except Refusal as refusal:
        print(json.dumps({"outcome": "REFUSED", "reason_code": refusal.code,
                          "detail": refusal.detail, "appended": refusal.appended,
                          "measured": refusal.measured}, indent=2, sort_keys=True))
        return refusal.exit_code
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def add_parser(sub: Any, root: Path) -> None:
    """Register ``settle`` on the kernel command line."""
    settle = sub.add_parser(
        "settle",
        help="perform settle_run: judge exactly as check, then append the RECEIPT (and with "
             "--concern one RECONCILED event) through the Record Service CLI; decides nothing "
             "check did not",
    )
    settle.add_argument("--request", required=True, help="path to a settle_run request")
    settle.add_argument("--current", help="path to the observed current state")
    settle.add_argument("--record-root", dest="record_root", required=True,
                        help="Record Service store root the receipt is appended to")
    settle.add_argument("--actor", required=True, help="settling principal, recorded as actor")
    settle.add_argument("--concern",
                        help="concern subject to append a RECONCILED event on after the receipt; "
                             "if that second append fails the receipt stays in the journal and "
                             "is listed under `appended` in the refusal")
    settle.add_argument("--relation", choices=RELATIONS,
                        help="what the run did to the concern (contracts/ticket-settlement.json)")
    settle.add_argument("--basis", help="what the relation rests on, in one sentence")
    settle.set_defaults(handler=lambda args: command_settle(args, root))
