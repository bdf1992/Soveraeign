"""Probe kinds that spawn a process or interrogate git, rather than reading a file.

Split from `probes.py` at the line ceiling, along the boundary that already mattered: these
are the expensive probes, the ones `--fast` skips, and the ones whose failure modes are
about exit codes and freshness rather than about parsing. `probes.py` keeps the file and
document kinds and owns the dispatch table both halves feed.
"""

from __future__ import annotations

from typing import Any
import json
import re

from sovcoldstart.source import DEFAULT_TIMEOUT, ProbeError, _git, _run


def p_cmd_exit(spec: dict[str, Any]) -> int:
    return _run(spec["argv"], spec.get("timeout", DEFAULT_TIMEOUT)).returncode


def p_cmd_out(spec: dict[str, Any]) -> str:
    done = _run(spec["argv"], spec.get("timeout", DEFAULT_TIMEOUT))
    stream = done.stdout + ("\n" + done.stderr if spec.get("stderr") else "")
    if "pattern" in spec:
        found = re.search(spec["pattern"], stream, re.MULTILINE)
        if not found:
            raise ProbeError(f"pattern {spec['pattern']!r} not found in output")
        return found.group(spec.get("group", 1)).strip()
    return stream.strip()


def p_cmd_grep_count(spec: dict[str, Any]) -> int:
    done = _run(spec["argv"], spec.get("timeout", DEFAULT_TIMEOUT))
    stream = done.stdout + "\n" + done.stderr
    return len(re.findall(spec["pattern"], stream, re.MULTILINE))


def p_verify_failures(spec: dict[str, Any]) -> list[str]:
    """The names of the checks verify.py reports as failing, excluding the budget entry.

    Counting its PASS and FAIL lines counted the stdout of unit tests racing inside a
    sharded runner: 59/59/56 and 15/15/19 across three runs on one commit. The failing
    check names were identical every time. The budget line is dropped because a slipped
    grade is a reportable observation and not a failing gate (decisions/0050).
    """
    done = _run(["python", "scripts/verify.py", "--json"],
                spec.get("timeout", DEFAULT_TIMEOUT))
    try:
        report = json.loads(done.stdout)
    except ValueError as exc:
        raise ProbeError(f"verify.py --json did not emit JSON: {exc}") from None
    checks = report.get("checks") if isinstance(report, dict) else report
    if not isinstance(checks, list):
        raise ProbeError("verify.py --json emitted no list of checks")
    failed = [str(check.get("subject") or check.get("name")) for check in checks
              if isinstance(check, dict) and _failed(check)]
    if done.returncode == 0 and failed:
        raise ProbeError(f"verify.py exited 0 while reporting {failed} as failing")
    return sorted(n for n in failed if n and not n.startswith("verification budget"))


def _failed(check: dict[str, Any]) -> bool:
    """One check's outcome, from the field that carries it rather than from a printed line."""
    predicates = check.get("predicate_results") or check
    if predicates.get("outcome") in ("PASS", "FAIL"):
        return predicates["outcome"] == "FAIL"
    return bool(predicates.get("exit_code"))


def p_git_count(spec: dict[str, Any]) -> int:
    """Commits reachable from a ref."""
    return int(_git(["rev-list", "--count", *spec.get("args", [spec.get("ref", "HEAD")])]).strip())


def p_git_out(spec: dict[str, Any]) -> str:
    return _git(spec["args"]).strip()


def p_git_lines(spec: dict[str, Any]) -> int:
    return len([ln for ln in _git(spec["args"]).splitlines() if ln.strip()])





def p_ahead_behind(spec: dict[str, Any]) -> list[int]:
    """[ahead, behind] of HEAD relative to a base ref."""
    base = spec.get("base", "main")
    raw = _git(["rev-list", "--left-right", "--count", f"{base}...HEAD"]).split()
    return [int(raw[1]), int(raw[0])]
