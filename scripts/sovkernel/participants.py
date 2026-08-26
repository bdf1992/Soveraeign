"""Drive each real participant and record what it refused.

`parity.py` owns the kernel side: the request that states a fact and the table
that judges it. This module owns the other side, and the two are separate on
purpose - a participant driver runs real code against a real temporary store,
while the kernel side reads a declared table. Keeping them in one module made
that boundary easy to lose, and made the module outgrow its budget.

Each function returns a mapping from a declared fact to whatever the participant
did when the fact was made to happen: the refusal class name, or `PERMITTED` when
it did not refuse at all. `PERMITTED` is never quietly acceptable; `parity.run`
fails on it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sys
import tempfile


def _open_asset_service(root: Path):
    """Import the Asset Service the way its own tests do."""
    src = root / "services" / "asset" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from soveraeign_asset_service.core import AssetService, StaleLease  # noqa: E402

    return AssetService, StaleLease


def asset(root: Path) -> dict[str, str]:
    """Drive the real Asset Service and record what it refused."""
    AssetService, StaleLease = _open_asset_service(root)
    observed: dict[str, str] = {}
    # ignore_cleanup_errors: SQLite on Windows holds the file until the handle is
    # released, and a temp directory that will not delete must not fail a check
    # about transition semantics.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = Path(tmp)
        service = AssetService(store / "state")
        try:
            service.grant("Bdo", "Bdo", "operate:derive")
            source = store / "parity.txt"
            source.write_bytes(b"parity")
            asset = service.ingest(source, "Parity source", "Bdo")
            run = service.request_derivative(asset["asset_id"], asset["version_id"], "Bdo")

            superseded = service.claim(run, "worker-a", ttl_seconds=0)
            service.claim(run, "worker-b")
            try:
                service.report_derivative(run, "worker-a", superseded, b"stale")
                observed["a superseded fence may not report"] = "PERMITTED"
            except StaleLease:
                observed["a superseded fence may not report"] = "StaleLease"

            unreported = service.request_derivative(
                asset["asset_id"], asset["version_id"], "Bdo"
            )
            try:
                service.observe(unreported, "witness-b")
                observed["an executor report is not settlement"] = "PERMITTED"
            except RuntimeError as error:
                observed["an executor report is not settlement"] = f"RuntimeError:{error}"
        finally:
            service.close()
    return observed


def console(root: Path) -> dict[str, str]:
    """Drive the real Console Service and record what it refused."""
    for package in ("console", "record"):
        src = root / "services" / package / "src"
        if str(src) not in sys.path:
            sys.path.insert(0, str(src))
    from soveraeign_console_service import ConsoleService  # noqa: E402
    from soveraeign_console_service.refusals import (  # noqa: E402
        AuthorityRefused,
        ModelClaimWithoutProposal,
    )
    from soveraeign_record_service import RecordService  # noqa: E402

    observed: dict[str, str] = {}
    # ignore_cleanup_errors for the same reason the Asset Service driver uses it:
    # SQLite on Windows holds the file until the handle is released.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = Path(tmp)
        record = RecordService(store / "journal")
        service = ConsoleService(record, store, "node:parity")
        try:
            service.grant("Bdo", "open:channel", "governance", "Bdo")
            channel = service.open_channel("Bdo", "governance", "governance")
            service.grant("Bdo", "open:thread", channel["channel_id"], "Bdo")
            thread = service.open_thread("Bdo", channel["channel_id"], "parity")
            service.grant("model/sov", "post:message", thread["thread_id"], "Bdo")
            # Opening a session is guarded as of 2026-08-25. Both participants hold
            # it so that the refusal below is still the post's, not the session's.
            for operator in ("model/sov", "model/stranger"):
                service.grant(operator, "open:session", operator, "Bdo")

            model = service.open_session("model/sov", "MODEL", "model-binding")
            try:
                service.post("model/sov", model["session_id"], thread["thread_id"],
                             b"settled", claims=True)
                observed["a model claim without a proposal is incomplete"] = "PERMITTED"
            except ModelClaimWithoutProposal:
                observed["a model claim without a proposal is incomplete"] = (
                    "ModelClaimWithoutProposal")

            ungranted = service.open_session("model/stranger", "MODEL", "model-binding")
            try:
                service.post("model/stranger", ungranted["session_id"], thread["thread_id"],
                             b"ungranted")
                observed["no live grant covers this transition"] = "PERMITTED"
            except AuthorityRefused:
                observed["no live grant covers this transition"] = "AuthorityRefused"
        finally:
            record.close()
    return observed


def ticket(root: Path) -> dict[str, str]:
    """Evaluate the ticket workflow's own requests against its own table."""
    sys.path.insert(0, str(root / "scripts"))
    from sovticket import transitions as ticket  # noqa: E402

    table = ticket.load_table(root)

    def decide(request: dict[str, Any]) -> str:
        decision = ticket.evaluate(request, table)
        return "PERMITTED" if decision.allowed else str(decision.reason_code)

    base = {
        "request_schema": "soveraeign-ticket-transition/v1",
        "ticket": "#6",
        "effect_class": "RECORD_LOCAL",
        "reason": "parity fact",
    }
    return {
        "the actor that built an artifact may not witness it": decide({
            **base,
            "from": "BUILT_SELF_TESTED_NOT_WITNESSED",
            "to": "WITNESSED",
            "actor_id": "model/worker-a",
            "actor_kind": "MODEL",
            "builder_actor_id": "model/worker-a",
            "evidence": {"witness_receipt": "obs-1", "purple_receipt": "purple-1"},
        }),
        # A HUMAN who is not the owner, so the request reaches the authority check
        # rather than being refused earlier at the actor-kind gate. The fact under
        # test is about authority, not about what kind of thing the actor is.
        "an actor without judgement authority may not ratify": decide({
            **base,
            "from": "WITNESSED",
            "to": "RATIFIED",
            "actor_id": "someone-else",
            "actor_kind": "HUMAN",
            "evidence": {"owner_ratification": "pull/62#review"},
        }),
        "an external effect outside every declared scope is refused": decide({
            **base,
            "from": "OPEN",
            "to": "PROPOSED",
            "actor_id": "model/orchestrator",
            "actor_kind": "MODEL",
            "effect_class": "EXTERNAL_WORLD",
            "evidence": {"obligation": "#6", "priors": "SPEC.md",
                         "closure_contract": "#6#closure"},
        }),
    }
