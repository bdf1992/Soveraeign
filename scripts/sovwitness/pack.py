"""Build the pack a witness pass starts from, so a pass re-derives the delta and not the world.

Five witness passes over one service each re-ran every gate and re-read every file,
because each was handed a prose brief and nothing else. The brief was also the place
the builder's claims leaked into the witness's reading. This module replaces the brief
with a derived record: the prior receipt over the same subject, the exact digest delta
since it, the commits landed in between, the custody exit the subject serves, and a
`RecordProjection` over the subject at the head. It conforms to
`contracts/witness-pack.schema.json`.

Everything here is recomputed from bytes and from git. Nothing is read from a field
that states its own freshness, and the builder's commit messages are carried as
claims to check, never as findings. A pack asserts nothing about the subject and
grants nothing; it is rebuilt for each pass rather than kept.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import subprocess

from sovwitness import records as record_grader
from sovwitness.shape import ReceiptError, resolve_address

PACK_SCHEMA = "soveraeign-witness-pack/v1"
PROJECTION_SCHEMA = "soveraeign-record-projection/v1"
RELATION = "INDEPENDENT_WITNESS"
CUSTODIES = Path("contracts") / "custodies"


class PackRefused(RuntimeError):
    """A pack that cannot honestly be built. `reason_code` names why."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _record_name(subject: str) -> str:
    return f"witness/{subject}.md"


def _receipts_for(root: Path, subject: str) -> list[Path]:
    """Every receipt whose `observed.record` names this subject's witness record."""
    wanted = _record_name(subject)
    found = []
    for path in record_grader.receipts(root):
        try:
            document = _load(path)
        except (json.JSONDecodeError, OSError):
            continue
        observed = document.get("observed") if isinstance(document, dict) else None
        if isinstance(observed, dict) and observed.get("record") == wanted:
            found.append(path)
    return found


def head_receipt(root: Path, subject: str) -> Path:
    """The receipt at the head of the subject's chain: named by no other receipt as prior."""
    candidates = _receipts_for(root, subject)
    if not candidates:
        raise PackRefused("NO_PRIOR_RECEIPT",
                          f"no receipt under witness/observations names {_record_name(subject)}")
    named_as_prior: set[str] = set()
    for path in candidates:
        for prior in (_load(path).get("observed") or {}).get("prior_receipts") or []:
            named_as_prior.add(str(prior).replace("\\", "/").split("/")[-1])
    heads = [path for path in candidates if path.name not in named_as_prior] or candidates
    return sorted(heads, key=lambda path: path.name)[-1]


def _git(root: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                              check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def _roots(addresses: list[str]) -> list[str]:
    """The directories the subject addresses fall under, deduplicated and ordered."""
    roots: list[str] = []
    for address in addresses:
        parent = str(Path(address).parent).replace("\\", "/")
        if parent in (".", ""):
            parent = address
        if parent not in roots:
            roots.append(parent)
    return roots


def _serves_exit(root: Path, roots: list[str]) -> dict[str, str] | None:
    """The live custody whose member address covers a subject root, if any."""
    directory = root / CUSTODIES
    if not directory.is_dir():
        return None
    for path in sorted(directory.glob("*.json")):
        try:
            collection = _load(path)
        except (json.JSONDecodeError, OSError):
            continue
        for custody in collection.get("custodies") or []:
            for member in custody.get("members") or []:
                address = str(member.get("address", ""))
                if any(r == address or r.startswith(address + "/") for r in roots):
                    return {"custody_id": custody["custody_id"],
                            "exit_clause": custody.get("exit_clause") or "UNSTATED"}
    return None


def _projection(root: Path, subject: str, head: str, addresses: list[str],
                included: list[dict[str, str]], omissions: list[dict[str, str]],
                recipient: str, prior_case: str, now: str) -> dict[str, Any]:
    material = json.dumps(included, sort_keys=True).encode("utf-8")
    digest = "sha256:" + sha256(material).hexdigest()
    seed = f"{subject}|{head}|{digest}".encode("utf-8")
    return {
        "record_projection_schema": PROJECTION_SCHEMA,
        "projection_id": "urn:soveraeign:record-projection:" + sha256(seed).hexdigest()[:24],
        "subject_addresses": addresses,
        "recipient_principal": recipient,
        "recipient_relation": RELATION,
        "purpose": (f"witness pass over {subject} at {head}: re-derive the claims that cite a "
                    f"moved address; carry the rest from {prior_case} as input findings"),
        "record_head": head,
        "as_of": now,
        "included_records": included,
        "omissions": omissions,
        "projection_digest": digest,
        "authority_effect": "NONE",
        "created_at": now,
    }


def build(root: Path, subject: str, recipient: str = "principal:witness",
          now: str | None = None) -> dict[str, Any]:
    """Build the pack for one subject over the current tree. Raises `PackRefused`."""
    now = now or datetime.now(timezone.utc).isoformat()
    receipt_path = head_receipt(root, subject)
    graded = record_grader.grade(receipt_path, root)
    if graded["verdict"] == record_grader.INVALID:
        raise PackRefused("PRIOR_UNGRADEABLE", f"{receipt_path.name}: {graded['defects'][0]}")
    if graded["verdict"] == record_grader.STALE_PROBE:
        raise PackRefused("PRIOR_PROBE_STALE",
                          f"{receipt_path.name}: the witness's own machinery moved, so the "
                          f"receipt no longer describes the code that produced its results")
    document = _load(receipt_path)
    observed = document["observed"]
    pairs = list(zip(observed["observed_state_addresses"], observed["observed_state_digests"]))

    subject_pairs, omissions = [], []
    for address, recorded in pairs:
        target = resolve_address(address, root)
        if record_grader._witness_owned(target, root):
            omissions.append({"record_class": f"witness machinery {address}",
                              "reason": "the witness's own probe; the pack is over the subject"})
        else:
            subject_pairs.append((address, recorded, target))
    if not subject_pairs:
        raise PackRefused("SUBJECT_UNADDRESSED",
                          f"{receipt_path.name} digests only witness machinery")

    moved, gone, included, unchanged = [], [], [], 0
    for address, recorded, target in subject_pairs:
        if not target.exists():
            gone.append(address)
            continue
        live = record_grader.digest_of(target)
        included.append({"address": address, "digest": live})
        if live == recorded:
            unchanged += 1
        else:
            moved.append({"address": address, "recorded": recorded, "live": live})
    if unchanged:
        omissions.append({"record_class": f"{unchanged} unchanged address(es)",
                          "reason": "digest equals the prior receipt's; carried, not re-read"})
    for address in gone:
        omissions.append({"record_class": f"gone {address}",
                          "reason": "named by the prior receipt and absent from the tree"})

    roots = _roots([address for address, _, _ in subject_pairs])
    prior_revision = str(document["artifact_revision"])
    head = _git(root, "rev-parse", "HEAD")
    if head is None:
        head = "WORKING_TREE"
        omissions.append({"record_class": "history",
                          "reason": "no git history readable at the root"})
    known = {address for address, _, _ in subject_pairs}
    diff = _git(root, "diff", "--name-only", f"{prior_revision}..HEAD", "--", *roots)
    if diff is None:
        added, added_source = [], (f"UNAVAILABLE: git diff --name-only {prior_revision}..HEAD "
                                   f"-- {' '.join(roots)} could not be read")
    else:
        added = [line for line in diff.splitlines() if line and line not in known]
        added_source = f"git diff --name-only {prior_revision}..HEAD -- {' '.join(roots)}"
        for address in added:
            target = root / address
            if target.is_file():
                included.append({"address": address, "digest": record_grader.digest_of(target)})
    log = _git(root, "log", "--format=%H%x09%s", f"{prior_revision}..HEAD", "--", *roots)
    commits = []
    for line in (log or "").splitlines():
        sha, _, message = line.partition("\t")
        if sha and message:
            commits.append({"commit": sha, "subject": message})

    addresses = [entry["address"] for entry in included]
    if not addresses:
        raise PackRefused("SUBJECT_UNADDRESSED", "every subject address is gone from the tree")
    projection = _projection(root, subject, head, addresses, included, omissions, recipient,
                             str(document["case_id"]), now)
    seed = f"{subject}|{head}|{receipt_path.name}".encode("utf-8")
    return {
        "witness_pack_schema": PACK_SCHEMA,
        "pack_id": "urn:soveraeign:witness-pack:" + sha256(seed).hexdigest()[:24],
        "subject": subject,
        "subject_roots": roots,
        "serves_exit": _serves_exit(root, roots),
        "record_head": head,
        "prior": {
            "receipt": receipt_path.relative_to(root).as_posix(),
            "case_id": str(document["case_id"]),
            "participant_id": str(document["participant_id"]),
            "artifact_revision": prior_revision,
            "verdict": observed.get("verdict"),
            "standing_supported": observed.get("standing_supported"),
            "record": observed.get("record"),
            "record_section": observed.get("record_section"),
        },
        "delta": {"moved": moved, "gone": gone, "added": added, "unchanged": unchanged,
                  "added_source": added_source},
        "builder_commits": commits,
        "record_projection": projection,
        "authority_effect": "NONE",
        "created_at": now,
    }


def describe(pack: dict[str, Any]) -> list[str]:
    """Human lines for a pack. The JSON is the record; this is the glance."""
    delta = pack["delta"]
    lines = [f"witness pack {pack['pack_id']} over {pack['subject']} at {pack['record_head']}",
             f"  prior: {pack['prior']['case_id']} at {pack['prior']['artifact_revision'][:12]} "
             f"({pack['prior']['verdict'] or 'no verdict'}; supported "
             f"{pack['prior']['standing_supported'] or 'nothing'})",
             f"  serves: {pack['serves_exit'] or 'no live custody names this subject'}",
             f"  delta: {len(delta['moved'])} moved, {len(delta['added'])} added, "
             f"{len(delta['gone'])} gone, {delta['unchanged']} unchanged"]
    lines += [f"    moved {entry['address']}" for entry in delta["moved"]]
    lines += [f"    added {address}" for address in delta["added"]]
    lines += [f"  builder claims: {len(pack['builder_commits'])} commit(s) to check, not adopt"]
    lines += [f"    {entry['commit'][:12]} {entry['subject']}" for entry in pack["builder_commits"]]
    return lines


__all__ = ["PACK_SCHEMA", "PackRefused", "build", "describe", "head_receipt"]
