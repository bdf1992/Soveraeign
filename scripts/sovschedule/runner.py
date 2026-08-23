"""Gate, invoke, and record one scheduled run of a workflow or skill.

The runner is host plumbing: it holds no authority and grants none. It checks
the declared effect class, the working tree, and the single-runner lock; emits
an ATTEMPTED event; invokes ``claude -p --agent sov-controller`` with the tool
rights of the declared mode and with commit and push denied; then emits a
REPORTED event. REPORTED is the executor's report, not an observation. A later
witness (``sov-qa`` or a human) decides what the run actually did.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Callable
import json
import subprocess

from sovschedule import cron, ledger
from sovschedule.declaration import Declaration


Invoker = Callable[[list[str], Path, int], tuple[int, str, str]]
TreeProbe = Callable[[Path], dict]

CONTROLLER_AGENT = "sov-controller"
SCHEDULER_ACTOR = "urn:soveraeign:actor:system:sov-schedule"
CONTROLLER_ACTOR = "urn:soveraeign:actor:model:claude-code:" + CONTROLLER_AGENT
OBSERVE_TOOLS = (
    "Read", "Grep", "Glob", "Agent", "Workflow", "Skill", "Write",
    "Bash(python *)", "Bash(git status*)", "Bash(git diff*)", "Bash(git log*)",
    "Bash(git rev-parse*)", "Bash(ls*)",
)
BUILD_TOOLS = OBSERVE_TOOLS + ("Edit",)
FORBIDDEN_TOOLS = (
    "Bash(git commit*)", "Bash(git push*)", "Bash(git reset*)", "Bash(git rebase*)",
    "Bash(git checkout*)", "Bash(git switch*)", "Bash(git stash*)",
    "PowerShell(git commit*)", "PowerShell(git push*)",
)
LOCK_TTL_FACTOR = 2
REFUSAL_CODES = ("SCHEDULE_DISABLED", "EFFECT_CLASS_REFUSED", "TREE_DIRTY", "RUN_IN_PROGRESS")


@dataclass
class RunResult:
    """What the runner recorded for one attempt."""

    run_id: str
    phase: str
    outcome: str
    reason_code: str | None = None
    exit_code: int | None = None
    command: list[str] = field(default_factory=list)
    capture_path: Path | None = None
    report_paths: list[str] = field(default_factory=list)


def git_probe(root: Path) -> dict:
    """Read HEAD and porcelain status; ``None`` values mean git could not answer."""

    def run(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args], cwd=root, capture_output=True, text=True,
                encoding="utf-8", check=False,
            )
        except OSError:
            return None
        return result.stdout if result.returncode == 0 else None

    return {"head": run("rev-parse", "HEAD"), "status": run("status", "--porcelain")}


def subprocess_invoker(command: list[str], cwd: Path, timeout: int) -> tuple[int, str, str]:
    """Run the command; missing executable and timeout are reported as exit codes."""
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, check=False,
        )
    except FileNotFoundError:
        return 127, "", f"executable not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"
    return result.returncode, result.stdout, result.stderr


def run_id_for(decl: Declaration, now: datetime) -> str:
    return f"{decl.name}-{now.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def build_prompt(decl: Declaration, run_id: str, run_date: str) -> str:
    """The controller prompt: explicit target, report location, and the no-commit rule."""
    args_text = json.dumps(decl.target_args, sort_keys=True)
    if decl.target_kind == "workflow":
        action = f'Run the workflow named "{decl.target_name}" with args {args_text}.'
    else:
        action = f'Invoke the "/{decl.target_name}" skill with args {args_text}.'
    return (
        f'Scheduled run {run_id} of schedule "{decl.name}" (mode {decl.mode}, '
        f"effect class {decl.effect_class}). {action} When it returns, write the completion "
        f"report to reports/{run_date}-{decl.name}.md using repository-relative paths only "
        "(never absolute local paths): what was dispatched and why, per-domain outcomes with "
        "witness verdicts, standing proposals capped at BUILT -> WITNESSED, residuals, and the "
        "judgement queue for Bdo. Never run git commit or git push; leave the working tree for "
        "review. Finish with a one-paragraph summary."
    )


def build_command(decl: Declaration, run_id: str, prompt: str, claude: str = "claude") -> list[str]:
    """Headless invocation with mode-scoped tool rights; commit and push are denied."""
    tools = BUILD_TOOLS if decl.mode == "build" else OBSERVE_TOOLS
    command = [
        claude, "-p", prompt, "--agent", CONTROLLER_AGENT, "--permission-mode", "dontAsk",
        "--allowedTools", ",".join(tools), "--disallowedTools", ",".join(FORBIDDEN_TOOLS),
        "--output-format", "json", "--max-budget-usd", str(decl.max_budget_usd),
    ]
    if decl.isolation == "worktree":
        command += ["--worktree", run_id]
    return command


def tree_inputs(root: Path, decl: Declaration, probe: dict) -> list[dict]:
    head = (probe.get("head") or "unavailable").strip()
    status = probe.get("status")
    return [
        {"address": decl.path.relative_to(root).as_posix(),
         "digest": ledger.digest_path(decl.path)},
        {"address": "git:HEAD", "digest": "git:" + head},
        {"address": "git:status --porcelain",
         "digest": ledger.digest_text("unavailable" if status is None else status)},
    ]


def gate(
    decl: Declaration, now: datetime, probe: dict, lock: ledger.Lock, force: bool,
) -> str | None:
    """Return a refusal reason code, or None when every gate passes."""
    if not decl.enabled and not force:
        return "SCHEDULE_DISABLED"
    if decl.effect_class == "EXTERNAL_WORLD":
        return "EFFECT_CLASS_REFUSED"
    if decl.clean_tree and decl.isolation == "tree":
        status = probe.get("status")
        if status is None or status.strip():
            return "TREE_DIRTY"
    if lock.is_held(now, decl.timeout_seconds * LOCK_TTL_FACTOR):
        return "RUN_IN_PROGRESS"
    return None


def _report_names(root: Path) -> set[str]:
    reports = root / "reports"
    return {p.name for p in reports.glob("*.md")} if reports.is_dir() else set()


def is_due(
    root: Path, decl: Declaration, now: datetime, tz: tzinfo | None = None,
) -> datetime | None:
    """Local minute at which the schedule is due, or None; refusals count as attempts."""
    local_now = now.astimezone(tz).replace(tzinfo=None)
    last = ledger.last_attempt(root, decl.name)
    if last is None:
        after = local_now - timedelta(minutes=decl.lookback_minutes)
    else:
        after = last.astimezone(tz).replace(tzinfo=None)
    return cron.first_due(decl.spec, after, local_now)


def execute(
    root: Path,
    decl: Declaration,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    invoke: Invoker = subprocess_invoker,
    probe: TreeProbe = git_probe,
    claude: str = "claude",
    force: bool = False,
) -> RunResult:
    """Gate, attempt, invoke, and report one run; every path leaves a ledger event."""
    now = clock()
    run_id = run_id_for(decl, now)
    operation_id = f"urn:soveraeign:operation:scheduled-run:{run_id}"
    snapshot = probe(root)
    inputs = tree_inputs(root, decl, snapshot)
    lock = ledger.Lock(root)
    reason_code = gate(decl, now, snapshot, lock, force)
    if reason_code:
        ledger.append(root, decl.name, run_id, ledger.envelope(
            event_id=f"urn:soveraeign:event:{run_id}:attempted", operation_id=operation_id,
            phase="ATTEMPTED", actor_id=SCHEDULER_ACTOR, actor_kind="SYSTEM",
            reason=f"refused before invocation: {reason_code}", occurred_at=ledger.timestamp(now),
            inputs=inputs, outputs=[], effect_class=decl.effect_class, outcome="REFUSED",
        ))
        return RunResult(run_id, "ATTEMPTED", "REFUSED", reason_code=reason_code)
    lock.acquire(run_id, now, decl.timeout_seconds * LOCK_TTL_FACTOR)
    run_date = now.astimezone().strftime("%Y-%m-%d")
    prompt = build_prompt(decl, run_id, run_date)
    command = build_command(decl, run_id, prompt, claude)
    ledger.append(root, decl.name, run_id, ledger.envelope(
        event_id=f"urn:soveraeign:event:{run_id}:attempted", operation_id=operation_id,
        phase="ATTEMPTED", actor_id=SCHEDULER_ACTOR, actor_kind="SYSTEM",
        reason=f"schedule {decl.name} due by cron '{decl.spec.expression}'; "
               f"target {decl.target_kind} {decl.target_name}",
        occurred_at=ledger.timestamp(now), inputs=inputs, outputs=[],
        effect_class=decl.effect_class, outcome="ATTEMPTED",
    ))
    before = _report_names(root)
    try:
        exit_code, stdout, stderr = invoke(command, root, decl.timeout_seconds)
    finally:
        lock.release()
    finished = clock()
    capture = ledger.runs_dir(root) / f"{run_id}.json"
    capture.parent.mkdir(parents=True, exist_ok=True)
    capture.write_text(json.dumps({
        "run_id": run_id, "command": command, "exit_code": exit_code, "stdout": stdout,
        "stderr": stderr, "started_at": ledger.timestamp(now),
        "finished_at": ledger.timestamp(finished),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    new_reports = sorted(_report_names(root) - before)
    after = probe(root).get("status")
    outputs = [{"address": capture.relative_to(root).as_posix(),
                "digest": ledger.digest_path(capture)}]
    outputs += [{"address": f"reports/{name}",
                 "digest": ledger.digest_path(root / "reports" / name)}
                for name in new_reports]
    outputs.append({"address": "git:status --porcelain",
                    "digest": ledger.digest_text("unavailable" if after is None else after)})
    outcome = "ATTEMPTED" if exit_code == 0 else "FAILED"
    ledger.append(root, decl.name, run_id, ledger.envelope(
        event_id=f"urn:soveraeign:event:{run_id}:reported", operation_id=operation_id,
        phase="REPORTED", actor_id=CONTROLLER_ACTOR, actor_kind="MODEL",
        reason=f"executor exit code {exit_code}; a report is not an observation",
        occurred_at=ledger.timestamp(finished), inputs=inputs, outputs=outputs,
        effect_class=decl.effect_class, outcome=outcome,
    ))
    return RunResult(run_id, "REPORTED", outcome, exit_code=exit_code, command=command,
                     capture_path=capture, report_paths=[f"reports/{n}" for n in new_reports])
