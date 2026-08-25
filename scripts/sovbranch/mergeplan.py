"""Simulate a whole merge sequence in the object database before any tree is touched.

Probing each branch against the base one at a time answers the wrong question. Branches
that each merge cleanly into `main` routinely conflict with each other, so a plan built
from independent probes lands the first branch and then stops. This module instead
carries the accumulated result forward: every probe is against the tree the previous
merges produced, which is the tree the real merge will actually meet.

Nothing here writes a ref or a file. `gitio.chain` records each simulated merge as an
unreferenced commit, so a rejected plan leaves nothing to undo.

A branch that conflicts is deferred rather than dropped, and retried once against the
finished accumulation, because a conflict is often with a sibling that had not landed
yet at the moment it was first tried.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sovbranch import gitio

ORDERS = ("oldest", "newest", "smallest", "given")


def order_refs(entries: list[dict[str, Any]], how: str = "oldest") -> list[dict[str, Any]]:
    """Sequence candidate branches.

    `oldest` first is the default because it replays the order the work was written in,
    which is the order whose conflicts a person can still reason about. `smallest` first
    lands the cheapest branches before the expensive one that may stall the run.
    """
    if how == "given":
        return list(entries)
    if how == "smallest":
        return sorted(entries, key=lambda e: (e.get("ahead", 0), e["name"]))
    return sorted(entries, key=lambda e: (e.get("when", 0), e["name"]),
                  reverse=(how == "newest"))


def _ref_of(entry: dict[str, Any]) -> str:
    """The ref to merge: the local branch when it exists, else its remote-tracking ref."""
    return entry["name"] if entry.get("local") else (entry.get("remote") or entry["name"])


def build(root: Path, base: str, entries: list[dict[str, Any]],
          how: str = "oldest", retry: bool = True) -> dict[str, Any]:
    """A merge sequence proved against a rolling accumulation, plus what it could not land."""
    head = gitio.resolve(root, base)
    if head is None:
        raise ValueError(f"base ref {base!r} does not exist")
    sequence, deferred, accumulated = [], [], head
    for entry in order_refs(entries, how):
        accumulated, step = _attempt(root, accumulated, entry)
        (sequence if step["clean"] else deferred).append(step)
    retried = []
    if retry and deferred and sequence:
        for step in deferred:
            entry = step["entry"]
            accumulated, again = _attempt(root, accumulated, entry)
            (sequence if again["clean"] else retried).append(again)
        deferred = retried
    return {"base": base, "base_commit": head, "order": how,
            "steps": [_public(step) for step in sequence],
            "blocked": [_public(step) for step in deferred]}


def _attempt(root: Path, accumulated: str, entry: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Probe one branch against the accumulation; advance it only when the merge is clean."""
    ref = _ref_of(entry)
    clean, tree, conflicts = gitio.probe(root, accumulated, ref)
    step = {"entry": entry, "name": entry["name"], "ref": ref, "clean": clean,
            "conflicts": conflicts, "ahead": entry.get("ahead", 0)}
    if not clean or tree is None:
        step["clean"] = False
        return accumulated, step
    chained = gitio.chain(root, tree, accumulated, ref)
    if chained is None:
        step["clean"] = False
        step["conflicts"] = ["could not record the simulated merge"]
        return accumulated, step
    step["result"] = chained[:12]
    return chained, step


def _public(step: dict[str, Any]) -> dict[str, Any]:
    """A step without the ledger entry it was derived from."""
    return {key: value for key, value in step.items() if key != "entry"}
