"""A fixture result for the discovery and reuse self-check, and the variants that defeat it.

The result is built by a fixture principal under a fixture root: the fresh-participation
probe run against a persisted temporary node, its lease released, its journal exported, a
history in which its revision landed by a merge, and a fixture witness record and receipt
that observe it. Nothing here names a real principal or issues anything in a real root's
name, and nothing here witnesses anything: the record and receipt are what a witness
would leave, written so the reader can be shown to read them.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import os
import shutil
import tempfile

import sov_fresh
from sovfresh import layers, node as nodelayer, probe
from sovlease import store as lease_store
from sovnode import journal
from sovreuse import discover, reuse, settle
from sovsession import principals

ROOT = Path(__file__).resolve().parents[2]

FIXTURE_RECORD = "witness/fresh-participation.md"
FIXTURE_RECEIPT = "witness/observations/fixture-observation.json"
FIXTURE_SUBJECT = "scripts/sov_fresh.py"

EXPECTED_FAILURES = {
    "no-witness": {"P15-Q3.1": "settlement lacks required independent observation",
                   "P15-Q3.2": "fresh reuse missing standing"},
    "bytes-moved": {"P15-Q3.1": "settlement was not against current state"},
    "revision-unknown": {"P15-Q3.1": "closure lacks receipt"},
    "lease-left-behind": {"P15-Q3.1": "closure left temporary coordination inventory"},
    "branch-left-behind": {"P15-Q3.1": "closure left temporary coordination inventory"},
    "head-private": {"P15-Q3.2": "fresh reuse missing capability"},
    "no-grant": {"P15-Q3.2": "fresh participant did not use the accepted result"},
    "oral-history": {"P15-Q3.2": "reuse required builder or prior-session oral history"},
}
"""Which predicates each defeating variant must fail, and the reason each must give; every
other predicate must hold.

A result with no witness record fails both: nothing settled it and there is no standing
to discover. A head the builder kept private leaves the journal unreachable, which is
the clause's own defeating condition read literally. A revision the trunk does not
descend from has no landing receipt, whatever the member declares.
"""


def _git(repo: Path, *args: str) -> str:
    """One git command the fixture needs to succeed; a refusal is a fixture defect."""
    out = settle.git(repo, "-c", "user.name=fixture", "-c", "user.email=fixture@soveraeign.local",
                     *args)
    if out is None:
        raise SystemExit(f"FAIL: fixture history refused: git {' '.join(args)}")
    return out


def _fixture_history(artifact: Path) -> str:
    """A history in which the witnessed revision landed by a merge, as the trunk records one.

    Returns the witnessed revision: the branch commit whose bytes the merge carries.
    """
    subject = artifact / FIXTURE_SUBJECT
    subject.parent.mkdir(parents=True, exist_ok=True)
    subject.write_bytes((ROOT / FIXTURE_SUBJECT).read_bytes())
    _git(artifact, "init", "-q", "-b", "main")
    _git(artifact, "add", "-A")
    _git(artifact, "commit", "-q", "-m", "fixture: trunk")
    _git(artifact, "checkout", "-q", "-b", "feat/fixture")
    with subject.open("a", encoding="utf-8") as handle:
        handle.write("# fixture landing\n")
    _git(artifact, "commit", "-q", "-am", "fixture: the slice")
    revision = _git(artifact, "rev-parse", "HEAD")
    _git(artifact, "checkout", "-q", "main")
    _git(artifact, "merge", "-q", "--no-ff", "feat/fixture", "-m", "merge: fixture landing")
    _git(artifact, "branch", "-q", "-D", "feat/fixture")
    return revision


def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _fixture_artifact(temp: Path, export_head: str, export_address: str) -> Path:
    """The committed surfaces a fresh participant reads, with fixture witness evidence.

    The receipt observes the result's own address and the journal export at the revision
    the fixture history landed, so a moved byte in either is a settlement defect.
    """
    artifact = temp / "artifact"
    revision = _fixture_history(artifact)
    collection = json.loads((ROOT / discover.CUSTODY_COLLECTION).read_text(encoding="utf-8"))
    for custody in collection["custodies"]:
        if custody["custody_id"] == reuse.RESULT_CUSTODY:
            custody["members"] = [{
                "member_kind": "ITEM", "address": FIXTURE_SUBJECT, "stage": "VERTICAL_SLICE",
                "standing": "WITNESSED", "work_state": "LANDED",
                "stage_observed_by": f"fixture-witness ({FIXTURE_RECORD}; {FIXTURE_RECEIPT})",
            }]
    target = artifact / discover.CUSTODY_COLLECTION
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(collection, indent=2) + "\n", encoding="utf-8")
    record = artifact / FIXTURE_RECORD
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("# Fixture witness record\n\n```witness\nstanding_supported  WITNESSED\n"
                      f"subject  fresh-participation\nrevision  {revision}\n```\n",
                      encoding="utf-8")
    addresses = [FIXTURE_SUBJECT, export_address]
    receipt = {
        "case_id": "FIXTURE-DISCOVERY", "participant_id": "fixture-witness",
        "artifact_revision": revision, "participant_claim": "COMPLETED",
        "observed": {
            "standing_supported": "WITNESSED", "observer_id": "fixture-witness",
            "observer_relation": "INDEPENDENT_FIXTURE_ONLY",
            "observed_state_addresses": addresses,
            "observed_state_digests": [_digest(artifact / a) for a in addresses],
            "node_state": {"head_held_outside_the_export": export_head},
        },
    }
    path = artifact / FIXTURE_RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return artifact


def build(temp: Path) -> dict[str, Any]:
    """A result built by a fixture principal under a fixture root, then settled and cleaned.

    The builder's run is the fresh-participation probe itself against a persisted fixture
    node; its lease is released afterwards, and the store as it stood before the release
    is kept for the variant that leaves it behind.
    """
    registry = sov_fresh.fixture_registry(temp)
    state = temp / "builder-node"
    with nodelayer.open_node_at(state) as node:
        nodelayer.open_office(node, sov_fresh.FIXTURE_ISSUER, sov_fresh.FIXTURE_PRINCIPAL,
                              {"read:registry": nodelayer.SCOPE})
    builder = probe.run(ROOT, temp / "builder", sov_fresh.FIXTURE_PRINCIPAL,
                        registry=registry, node_state=state)
    if not builder["passed"]:
        raise SystemExit("FAIL: the fixture builder's run did not pass:\n"
                         + sov_fresh._render(builder))
    sessions = temp / "builder" / "sov-sessions"
    unreleased = temp / "unreleased"
    shutil.copytree(sessions, unreleased)
    for lease_id in layers.orphaned_inventory(sessions):
        lease_store.append(sessions, lease_store.LEASES_LOG,
                           {"event": "release", "lease_id": lease_id})
    artifact = temp / "artifact"
    exported = journal.export(state, artifact / "nodes" / "node-local" / "journal")
    export_address = exported["path"].relative_to(artifact).as_posix()
    _fixture_artifact(temp, exported["head"], export_address)
    revision = json.loads((artifact / FIXTURE_RECEIPT).read_text(encoding="utf-8"))
    return {"registry": registry, "artifact": artifact, "sessions": sessions,
            "unreleased": unreleased, "revision": revision["artifact_revision"]}


def _mutate_receipt(artifact: Path, variant: str) -> None:
    path = artifact / FIXTURE_RECEIPT
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if variant == "bytes-moved":
        receipt["observed"]["observed_state_digests"][0] = "sha256:" + "0" * 64
    if variant == "revision-unknown":
        receipt["artifact_revision"] = "0" * 40
    if variant == "head-private":
        receipt["observed"]["node_state"] = {}
    path.write_text(json.dumps(receipt), encoding="utf-8")


def run_variant(fixture: dict[str, Any], variant: str, temp: Path) -> dict[str, Any]:
    """One variant against its own copy of the fixture artifact."""
    work = Path(tempfile.mkdtemp(prefix=f"{variant}-", dir=temp))
    artifact = work / "artifact"
    shutil.copytree(fixture["artifact"], artifact)
    sessions = fixture["sessions"]
    principal = sov_fresh.FIXTURE_PRINCIPAL
    registry: Path | None = fixture["registry"]
    environment = dict(os.environ)
    if variant == "no-witness":
        (artifact / FIXTURE_RECORD).unlink()
    elif variant in ("bytes-moved", "revision-unknown", "head-private"):
        _mutate_receipt(artifact, variant)
    elif variant == "lease-left-behind":
        sessions = fixture["unreleased"]
    elif variant == "branch-left-behind":
        _git(artifact, "branch", "-q", "feat/left-behind", fixture["revision"])
    elif variant == "no-grant":
        principal = "principal:bdo"
    elif variant == "oral-history":
        environment[principals.ENV_REGISTRY] = str(registry)
        registry = None
    previous = os.environ.get(principals.ENV_REGISTRY)
    try:
        if variant == "oral-history":
            os.environ[principals.ENV_REGISTRY] = environment[principals.ENV_REGISTRY]
        else:
            os.environ.pop(principals.ENV_REGISTRY, None)
        return reuse.run(ROOT, artifact, work / "run", principal,
                         registry=registry, sessions_dir=sessions)
    finally:
        if previous is None:
            os.environ.pop(principals.ENV_REGISTRY, None)
        else:
            os.environ[principals.ENV_REGISTRY] = previous
