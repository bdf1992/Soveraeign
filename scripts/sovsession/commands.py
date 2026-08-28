"""What each session-coordination command does.

Split from the command line itself so the shape of the interface and the
behaviour behind it can change independently, and so a caller that already
knows what it wants - a hook, a test - can reach the behaviour without
constructing an argument parser.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import os
import subprocess

from sovsession import brief as briefmod
from sovsession import principals
from sovsession import claims as claimsmod
from sovsession import guard as guardmod
from sovsession import store
from sovsession import worktrees as wtmod


def session_name(explicit: str | None = None, fallback: str | None = None) -> str:
    """This session's registry name: given, chosen at launch, or derived from its id.

    Every subprocess a session launches inherits `CLAUDE_CODE_SESSION_ID`, so a
    hook and a hand-run command from the same session agree on who they are
    without any handshake.

    `explicit` is a name a caller typed and must be honoured. `fallback` is a
    name a caller derived because it had nothing better, and must lose to
    `SOV_SESSION`: a launcher that names a session before starting it is the
    only party that knows the name every other surface will use, and a derived
    name that outranked it registered one process twice, once under the name
    the launcher chose and once under a `session-` alias nobody could join to
    it.
    """
    if explicit:
        return explicit
    override = os.environ.get("SOV_SESSION", "").strip()
    if override:
        return override
    if fallback:
        return fallback
    inherited = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if inherited:
        return "session-" + inherited[:6]
    return "unnamed-" + str(os.getpid())


def _context(name: str | None = None) -> tuple[Path, Path, str, str]:
    """Repository root, store directory, session name, and this working tree."""
    root = store.repo_root()
    return root, store.store_dir(), session_name(name), str(root).replace("\\", "/")


def _emit(payload: Any, as_json: bool, text: str = "") -> None:
    """Print machine output or human output, never both."""
    print(json.dumps(payload, indent=2, sort_keys=True) if as_json else text)


def cmd_register(args: argparse.Namespace) -> int:
    """Record that this session is live, and print the briefing it should read."""
    root, directory, name, tree = _context(args.name)
    claim = principals.resolve(root, name)
    store.append(directory, store.SESSIONS_LOG, {
        "event": "register",
        "session": name,
        "principal": claim["principal"],
        "verification": claim["verification"],
        "pid": int(os.environ.get("CLAUDE_PID", 0) or 0),
        "tree": tree,
        "branch": briefmod.branch_of(root),
        "intent": args.intent or "",
    })
    data = briefmod.collect(root, directory, name, tree)
    _emit(data, args.as_json, briefmod.render(data))
    return 0


def cmd_principal(args: argparse.Namespace) -> int:
    """Name the principal this session speaks as, and how strongly the registry claims it."""
    root, _, name, _ = _context(args.name)
    claim = principals.resolve(root, name)
    _emit(claim, args.as_json, principals.render(claim))
    return 0 if claim["principal"] and not claim["defects"] else 1


def cmd_heartbeat(args: argparse.Namespace) -> int:
    """Refresh this session's liveness so its claims do not expire."""
    _, directory, name, _ = _context(args.name)
    store.append(directory, store.SESSIONS_LOG, {"event": "heartbeat", "session": name})
    return 0


def cmd_end(args: argparse.Namespace) -> int:
    """Close this session, releasing every claim it holds."""
    _, directory, name, _ = _context(args.name)
    store.append(directory, store.SESSIONS_LOG, {"event": "end", "session": name})
    return 0


def cmd_claim(args: argparse.Namespace) -> int:
    """Claim paths and resources, refusing a same-tree takeover unless forced.

    A resource is anything held that is not a file: a listening port, an open
    SQLite store, a browser profile. Those collide exactly as paths do - a
    second session binding 8787, or deleting a store the first still has open -
    and nothing in git can see them at all.
    """
    root, directory, name, tree = _context(args.name)
    paths = [claimsmod.relative(path, root) for path in args.paths]
    paths += ["resource:" + item for item in (args.resource or [])]
    blocked = []
    if not args.force:
        for path in paths:
            verdict = guardmod.guard_write(directory, name, path, tree)
            if verdict["decision"] == guardmod.DENY:
                blocked.append(verdict)
    if blocked:
        text = "\n".join(
            "REFUSED " + item["path"] + ": " + item["reason"] + "\n  " + item["escape"]
            for item in blocked)
        _emit(blocked, args.as_json, text)
        return 1
    written = claimsmod.claim(directory, name, paths, tree, args.intent or "")
    _emit(written, args.as_json, "claimed %d path(s) as %s" % (len(written), name))
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    """Give up claims on paths."""
    root, directory, name, _ = _context(args.name)
    paths = [claimsmod.relative(path, root) for path in args.paths]
    claimsmod.release(directory, name, paths)
    _emit({"released": paths}, args.as_json, "released %d path(s)" % len(paths))
    return 0


def cmd_who(args: argparse.Namespace) -> int:
    """Name every live session holding a path."""
    root, directory, _, _ = _context(args.name)
    path = claimsmod.relative(args.path, root)
    holders = claimsmod.held(directory).get(path, [])
    if args.as_json:
        _emit(holders, True)
        return 0
    if not holders:
        print(path + ": no live session holds it")
        return 0
    for holder in holders:
        print("%s: %s in %s on %s since %s" % (
            path, holder["session"], holder.get("tree", "?"),
            holder.get("branch", "?"), holder.get("at", "?")))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Every live session and the paths it holds."""
    _, directory, name, _ = _context(args.name)
    live = [record for record in store.sessions(directory).values() if record.get("live")]
    holders = claimsmod.held(directory)
    if args.as_json:
        _emit({"sessions": live, "held": holders}, True)
        return 0
    print("%d live session(s):" % len(live))
    for record in sorted(live, key=lambda item: str(item.get("session"))):
        mark = "  <- you" if record.get("session") == name else ""
        print("  %s  %s  %s%s" % (record.get("session"), record.get("tree"),
                                  record.get("branch"), mark))
    print("%d path(s) under live claim:" % len(holders))
    for path in sorted(holders):
        owners = ", ".join(str(holder["session"]) for holder in holders[path])
        print("  %s: %s" % (path, owners))
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    """Print the briefing a starting session reads."""
    root, directory, name, tree = _context(args.name)
    data = briefmod.collect(root, directory, name, tree)
    _emit(data, args.as_json, briefmod.render(data))
    return 0


def cmd_guard(args: argparse.Namespace) -> int:
    """Judge one pending write or shell command. Exit 2 denies, 0 allows."""
    root, directory, name, tree = _context(args.name)
    if args.command is not None:
        verdict = guardmod.guard_bash(directory, name, args.command, tree)
    else:
        verdict = guardmod.guard_write(
            directory, name, claimsmod.relative(args.path or "", root), tree)
    if args.as_json:
        _emit(verdict, True)
    elif verdict["decision"] != guardmod.ALLOW:
        print(verdict["decision"].upper() + ": " + verdict["reason"])
        if verdict.get("escape"):
            print("  escape: " + verdict["escape"])
    return 2 if verdict["decision"] == guardmod.DENY else 0


def cmd_reserve_decision(args: argparse.Namespace) -> int:
    """Take the next free decision number and claim its file before writing it."""
    root, directory, name, tree = _context(args.name)
    number = claimsmod.next_decision_number(root, directory)
    path = "decisions/%04d-%s.md" % (number, args.slug)
    claimsmod.claim(directory, name, [path], tree, "reserved decision number")
    _emit({"number": number, "path": path}, args.as_json, path)
    return 0


def cmd_worktree(args: argparse.Namespace) -> int:
    """Create, inventory, or prune worktrees of this repository."""
    root, directory, _, _ = _context(args.name)
    if args.worktree_command == "new":
        made = wtmod.create(root, args.name_arg, args.base, args.branch)
        _emit(made, args.as_json, "worktree %s on %s from %s" % (
            made["path"], made["branch"], made["base"]))
        return 0
    if args.worktree_command == "prune":
        pruned = wtmod.prune(root, directory, dry_run=not args.apply)
        tail = " removed" if args.apply else "; re-run with --apply to remove"
        _emit(pruned, args.as_json, "%d disposable worktree(s)%s" % (len(pruned), tail))
        return 0
    entries = wtmod.inventory(root, directory)
    if args.as_json:
        _emit(entries, True)
        return 0
    for entry in entries:
        flags = [flag for flag, on in (
            ("live:" + str(entry["session"]), entry["session"]),
            ("dirty", entry["dirty"]),
            ("temp", entry["temp"]),
            ("disposable", entry["disposable"])) if on]
        print("  %s  %s  +%d/-%d  %s" % (
            entry["path"], entry.get("branch") or entry.get("head"),
            entry["ahead"], entry["behind"], " ".join(flags)))
    return 0


def cmd_contested(args: argparse.Namespace) -> int:
    """Name the uncommitted paths another live session is holding.

    This answers "did I break this, or is it someone's half-finished edit". On
    2026-08-23 three sessions each spent a cycle diagnosing a red gate caused by
    a peer's in-flight write, because `git status` names paths and never names
    who is standing on them.
    """
    root, directory, name, tree = _context(args.name)
    result = subprocess.run(["git", "status", "--porcelain"], cwd=str(root),
                            capture_output=True, text=True, check=False)
    dirty = [line[3:].strip().strip('"') for line in result.stdout.splitlines()
             if len(line) > 3]
    holders = claimsmod.held(directory)
    rows = []
    for path in sorted(dirty):
        others = [holder for holder in holders.get(path, [])
                  if holder.get("session") != name]
        if others:
            rows.append({"path": path,
                         "held_by": [str(holder.get("session")) for holder in others],
                         "same_tree": any(holder.get("tree") == tree
                                          for holder in others)})
    if args.as_json:
        _emit(rows, True)
        return 0
    if not rows:
        print("%d uncommitted path(s), none held by another live session" % len(dirty))
        return 0
    print("%d of %d uncommitted path(s) are held by another live session:"
          % (len(rows), len(dirty)))
    for row in rows:
        where = "this tree" if row["same_tree"] else "another tree"
        print("  %s - %s in %s" % (row["path"], ", ".join(row["held_by"]), where))
    return 0


def cmd_selfcheck(args: argparse.Namespace) -> int:
    """Prove the coordination logic against a temporary store, with no live sessions.

    This is what `scripts/verify.py` runs. It must pass in CI, where no session
    is registered and the store does not exist, so it builds its own.
    """
    import unittest
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite([
        loader.loadTestsFromName("tests.test_sov_session"),
        loader.loadTestsFromName("tests.test_sov_session_guard"),
    ])
    result = unittest.TextTestRunner(verbosity=1 if args.as_json else 2).run(suite)
    if not result.wasSuccessful():
        print("FAIL: session coordination selfcheck")
        return 1
    print("PASS: session coordination selfcheck")
    return 0
