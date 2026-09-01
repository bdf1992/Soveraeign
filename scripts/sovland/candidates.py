"""Freeze and settle exact repository candidates.

Mutable construction is allowed to move. This module creates the boundary after
that movement: `freeze` commits the exact reconciled bytes and emits a candidate
record; `land` later verifies evidence names that exact commit/tree/base and
merges the commit without rewriting it.

The lifecycle predicates live in `scripts/sov_candidate.py`. This module owns the
Git effects needed to realize those predicates and nothing about product standing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from sovkernel import authority
from sovland import preflight, repo, tree
import sov_candidate


class CandidateRefused(RuntimeError):
    """A candidate operation cannot be performed without changing its meaning."""


def _request(args: Any, capability: str, paths: list[str], checks: dict[str, str],
             observation: dict | None = None) -> dict:
    return {
        "request_schema": "soveraeign-authority-request/v1",
        "actor_id": args.actor,
        "capability": capability,
        "effect_class": "RESOURCE_CONSUMPTION",
        "at": datetime.now(timezone.utc).isoformat(),
        "branch": args.target,
        "paths": paths,
        "spend": {"unit": "agent_invocations", "amount": args.spend},
        "evidence": {"checks": checks, "observation": observation},
    }


def _candidate_path(commit: str, output: str | None) -> Path:
    if output:
        path = Path(output)
        return path if path.is_absolute() else repo.ROOT / path
    return repo.ROOT / ".local" / "candidates" / f"{commit}.json"


def _repo_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else repo.ROOT / path


def freeze(args: Any, grants: list[dict]) -> tuple[dict, dict, dict]:
    """Commit an exact checked mutable carrier and emit its frozen candidate record."""
    if not args.path:
        raise CandidateRefused("freeze requires explicit --path arguments")

    branch = repo.current_branch()
    staged = [tree.repo_relative(path) for path in args.path]
    carried = [tree.repo_relative(path) for path in repo.carried_paths(args.target, branch)]
    graded_paths = sorted(set(staged) | set(carried))
    graded_as = tree.fingerprint(staged)
    graded_blobs = {path: repo.worktree_blob(path) for path in staged}
    checks, reading = tree.gather_checks(args.skip_checks, set(graded_paths))
    by_checks = tree.drifted(graded_as, tree.fingerprint(staged))
    request = _request(args, "repository.commit", graded_paths, checks)
    result = authority.evaluate(grants, request)
    if result["verdict"] != authority.PERMITTED:
        raise CandidateRefused(f"{result['code']}: {result['detail']}")

    _ahead, behind = repo._commit_span(args.target, branch)
    detail = preflight.refusal(args, staged, behind, graded_as, by_checks)
    if detail is not None:
        raise CandidateRefused(detail)

    base_commit = repo.head_commit(args.target)
    if base_commit is None:
        raise CandidateRefused(f"cannot resolve target {args.target!r} before freeze")

    repo._git("add", "--", *staged)
    wrong = tree.staged_wrong(staged, graded_blobs)
    if wrong:
        repo._git("reset", "--", *staged)
        raise CandidateRefused(
            "staged content differs from the bytes that were graded: " + ", ".join(wrong)
        )

    repo._git("commit", "-m", args.message)
    candidate_commit = repo.head_commit("HEAD")
    candidate_tree = repo.commit_tree("HEAD")
    if candidate_commit is None or candidate_tree is None:
        raise CandidateRefused("git committed the candidate but its commit/tree cannot be resolved")

    candidate = {
        "candidate_schema": "soveraeign-repository-candidate/v1",
        "state": "FROZEN",
        "repository": repo.repository_address(),
        "concern_id": getattr(args, "concern", None),
        "branch": branch,
        "target": args.target,
        "base_commit": base_commit,
        "candidate_commit": candidate_commit,
        "candidate_tree": candidate_tree,
        "changed_paths": graded_paths,
        "checks": checks,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
    }
    path = _candidate_path(candidate_commit, getattr(args, "output", None))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate["candidate_file"] = (
        str(path.relative_to(repo.ROOT)) if path.is_relative_to(repo.ROOT) else str(path)
    )
    return candidate, result, reading


def load(path: str) -> dict:
    return json.loads(_repo_path(path).read_text(encoding="utf-8"))


def _observation_subject(candidate: dict, observation: dict) -> dict:
    return {
        "operation": "QUALIFY",
        "state": candidate.get("state"),
        "candidate_commit": candidate.get("candidate_commit"),
        "candidate_tree": candidate.get("candidate_tree"),
        "base_commit": candidate.get("base_commit"),
        "evidence_candidate_commit": observation.get("candidate_commit"),
        "evidence_candidate_tree": observation.get("candidate_tree"),
        "evidence_base_commit": observation.get("base_commit"),
    }


def _candidate_integrity(candidate: dict) -> None:
    commit = candidate.get("candidate_commit")
    actual_tree = repo.commit_tree(commit) if commit else None
    if actual_tree != candidate.get("candidate_tree"):
        raise CandidateRefused(
            f"candidate tree mismatch: record {candidate.get('candidate_tree')}, git {actual_tree}"
        )
    try:
        actual_paths = sorted(repo.carried_paths(candidate["base_commit"], commit))
    except (KeyError, repo.LandingRefused) as exc:
        raise CandidateRefused(f"candidate range cannot be reconstructed: {exc}") from exc
    declared_paths = sorted(candidate.get("changed_paths") or [])
    if actual_paths != declared_paths:
        raise CandidateRefused(
            "candidate changed_paths do not describe its exact base...commit range"
        )


def land(args: Any, grants: list[dict]) -> tuple[dict, dict, str]:
    """Merge one exact frozen candidate after subject-bound independent evidence."""
    candidate = load(args.candidate)
    if args.target != candidate.get("target"):
        raise CandidateRefused(
            f"candidate target is {candidate.get('target')!r}, not requested {args.target!r}"
        )
    observation = json.loads(_repo_path(args.observation).read_text(encoding="utf-8"))
    _candidate_integrity(candidate)

    qualification = sov_candidate.evaluate(
        sov_candidate.load_contract(), _observation_subject(candidate, observation)
    )
    if qualification["verdict"] != sov_candidate.PERMITTED:
        raise CandidateRefused(f"{qualification['code']}: {qualification['detail']}")

    current_base = repo.head_commit(candidate["target"])
    landing_claim = {
        **_observation_subject(candidate, observation),
        "operation": "LAND",
        "current_base_commit": current_base,
    }
    lifecycle = sov_candidate.evaluate(sov_candidate.load_contract(), landing_claim)
    if lifecycle["verdict"] != sov_candidate.PERMITTED:
        raise CandidateRefused(f"{lifecycle['code']}: {lifecycle['detail']}")

    request = _request(
        args,
        "repository.land",
        candidate["changed_paths"],
        candidate["checks"],
        observation,
    )
    result = authority.evaluate(grants, request)
    if result["verdict"] != authority.PERMITTED:
        raise CandidateRefused(f"{result['code']}: {result['detail']}")

    original = repo.current_branch()
    repo._git("checkout", candidate["target"])
    try:
        repo._git(
            "merge", "--no-ff", candidate["candidate_commit"],
            "-m", f"merge: {args.message}",
        )
        merge_commit = repo.head_commit(candidate["target"])
    finally:
        repo._git("checkout", original)
    if merge_commit is None:
        raise CandidateRefused("merge completed but the settlement commit cannot be resolved")
    return candidate, result, merge_commit


__all__ = ["CandidateRefused", "freeze", "land", "load"]
