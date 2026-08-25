"""Human output. One line per branch, widest fact first, no colour and no box drawing.

The ledger is read on a terminal beside `git status`, so it uses git's own vocabulary for
position (`+ahead/-behind`) and says the disposition in a word rather than a symbol. A
reader should be able to act on any single line without consulting a legend.
"""

from __future__ import annotations

from typing import Any

MARK = {"HELD": "held by", "MERGED": "contained", "ORPHANED": "remote gone",
        "CONFLICTED": "conflicts", "READY": "clean", "OPEN": "unprobed"}


def _position(entry: dict[str, Any]) -> str:
    """Where a branch sits relative to the base, in git's own notation."""
    return f"+{entry['ahead']}/-{entry['behind']}"


def ledger(entries: list[dict[str, Any]], base: str) -> str:
    """The branch table, plus a count per disposition."""
    if not entries:
        return f"no branches to report against {base}"
    width = max(len(entry["name"]) for entry in entries)
    lines = [f"{len(entries)} branches against {base}", ""]
    counts: dict[str, int] = {}
    for entry in entries:
        state = entry["disposition"]
        counts[state] = counts.get(state, 0) + 1
        notes = []
        if entry["session"]:
            notes.append(f"session {entry['session']}")
        if entry["dirty"]:
            notes.append("dirty")
        if entry["worktree"] and not entry["session"]:
            notes.append("temp worktree" if entry["temp"] else "worktree")
        if entry["conflicts"]:
            shown = ", ".join(entry["conflicts"][:3])
            more = f" +{len(entry['conflicts']) - 3}" if len(entry["conflicts"]) > 3 else ""
            notes.append(f"{shown}{more}")
        if entry["pr"]:
            draft = " draft" if entry["pr"].get("isDraft") else ""
            notes.append(f"PR #{entry['pr']['number']}{draft} -> {entry['pr']['baseRefName']}")
        if not entry["local"]:
            notes.append("remote only")
        if entry.get("remote_ahead"):
            notes.append(f"origin is {entry['remote_ahead']} ahead of the local ref")
        if entry.get("protected"):
            notes.append("protected")
        lines.append(f"  {entry['name']:<{width}}  {_position(entry):>10}  "
                     f"{state:<11} {'; '.join(notes)}".rstrip())
    tally = ", ".join(f"{count} {state.lower()}" for state, count in sorted(counts.items()))
    return "\n".join([*lines, "", tally])


def plan(record: dict[str, Any]) -> str:
    """The merge sequence and what it could not land."""
    lines = [f"merge plan onto {record['base']} ({record['base_commit'][:12]}), "
             f"{record['order']} first", ""]
    if not record["steps"]:
        lines.append("  nothing lands cleanly")
    for index, step in enumerate(record["steps"], start=1):
        lines.append(f"  {index:>2}. {step['name']}  (+{step['ahead']}) -> {step['result']}")
    if record["blocked"]:
        lines += ["", f"blocked ({len(record['blocked'])}):"]
        lines += _grouped(record["blocked"])
    return "\n".join(lines)


def _grouped(blocked: list[dict[str, Any]]) -> list[str]:
    """Blocked branches gathered by the conflict they share.

    Branches cut from a common feature branch all conflict with the base on the same
    files, so listing them one by one prints the same conflict twenty times and buries
    the two that are genuinely different. Grouping states each conflict once and names
    who is behind it.
    """
    groups: dict[tuple[str, ...], list[str]] = {}
    for step in blocked:
        groups.setdefault(tuple(step["conflicts"]), []).append(step["name"])
    lines = []
    for conflicts, names in sorted(groups.items(), key=lambda item: -len(item[1])):
        shown = ", ".join(conflicts[:4]) or "unknown"
        more = f" +{len(conflicts) - 4} more" if len(conflicts) > 4 else ""
        lines.append(f"  {len(names):>2} branch(es) blocked on {shown}{more}")
        lines += [f"       {name}" for name in sorted(names)]
    return lines


def integrate(record: dict[str, Any]) -> str:
    """What actually landed, what stopped it, and the push command that was not run."""
    lines = [f"integration branch {record['branch']} at {record['path']}",
             f"base {record['base']}", ""]
    for step in record["merged"]:
        checked = step.get("verify")
        state = "" if checked is None else (
            "  verify ok" if checked["passed"] else "  VERIFY FAILED")
        lines.append(f"  merged {step['name']} -> {step['head']}{state}")
    if record["failed"]:
        failure = record["failed"]
        lines += ["", f"stopped at {failure['name']} ({failure['reason']})"]
        lines += [f"    {line}" for line in failure["detail"]]
    final = record.get("verify")
    if final:
        lines += ["", "verify.py passed" if final["passed"] else "verify.py FAILED", final["tail"]]
    lines += ["", "nothing was pushed. to publish this branch yourself:", f"  {record['push']}"]
    return "\n".join(lines)


def retire(actions: list[dict[str, Any]], dry_run: bool) -> str:
    """What would be, or was, deleted."""
    if not actions:
        return "nothing is safe to retire"
    verb = "would delete" if dry_run else "deleted"
    lines = [f"{verb} {len(actions)} branch(es) whose commits the base already holds", ""]
    for action in actions:
        notes = []
        if action["worktree"]:
            notes.append(f"worktree {action['worktree']}")
        if action.get("forced"):
            notes.append("forced past git's HEAD-relative check")
        if action.get("error"):
            notes.append(f"ERROR {action['error']}")
        lines.append(f"  {action['name']}  {'; '.join(notes)}".rstrip())
    if dry_run:
        lines += ["", "re-run with --apply to carry this out"]
    return "\n".join(lines)

def trees(entries: list[dict[str, Any]]) -> str:
    """The worktree inventory, one line each, disposable ones marked."""
    if not entries:
        return "no worktrees"
    lines = [f"{len(entries)} worktrees", ""]
    for entry in entries:
        notes = []
        if entry.get("session"):
            notes.append(f"session {entry['session']}")
        if entry.get("dirty"):
            notes.append("dirty")
        if entry.get("temp"):
            notes.append("under a session scratchpad")
        if not entry.get("exists"):
            notes.append("MISSING from disk")
        if entry.get("disposable"):
            notes.append("disposable")
        ref = entry.get("branch") or entry.get("head") or "detached"
        position = f"+{entry['ahead']}/-{entry['behind']}"
        lines.append(f"  {ref:<38} {position:>10}  {'; '.join(notes)}".rstrip())
        lines.append(f"      {entry['path']}")
    return "\n".join(lines)
