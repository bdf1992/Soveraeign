"""Assemble one row per schedule for the command and the page to share.

The row is the projection: declaration facts joined to run history and to the
judgement ``health.py`` derives from both. Two readers consume it and neither
re-derives anything, so the command and the page cannot disagree about what a
schedule's state is - which is the way the two of them go quietly out of step.

Declarations are loaded one file at a time rather than through ``load_all``.
``load_all`` raises on the first file it refuses, which would mean one dead target
blinding the reader to every other schedule - on a surface whose whole job is to
say which ones are broken. A refused file becomes a row carrying the loader's
defect, and ``DECLARATION_REFUSED`` reports it.

Times are read in one clock and the page records which. ``runner.is_due`` matches
cron in the host local time, so a read taken in UTC answers "when is it next due"
hours - sometimes a day - wrong on any host that is not on UTC. The offset is taken
once, carried on the digest, and reproduced by the staleness check, so the answer is
right for the machine the runs happen on and the page still byte-compares elsewhere.

Declarations are read from one of two places and the caller says which. The page and
its staleness check read them at HEAD, because a page derived from a tree eleven
sessions share cannot be committed correctly: another session's untracked schedule puts
a row on the page that a clean checkout cannot reproduce, and the check then refuses the
commit it shipped in. That is the referent Bdo ruled on in acceptance packet A5 for the
orientation page, applied here for the same reason. The operator command reads the
working tree, because someone asking about a schedule file in front of them wants an
answer about that file.

Reading only. Nothing here writes a declaration, the ledger, or any standing, and the
committed read materialises HEAD into a scratch directory rather than touching the tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

from sovschedule import committed, cron, health, history
from sovschedule.committed import COMMIT, WORKTREE
from sovschedule.declaration import (
    SCHEDULES_DIR, SCHEMA_NAME, DeclarationError, load_declaration, target_path,
)


@dataclass(frozen=True)
class Declared:
    """One declaration file as read, whether or not the loader accepted it."""

    name: str
    description: str
    enabled: bool
    target_kind: str
    target_name: str
    cron_expression: str
    mode: str
    effect_class: str
    timeout_seconds: int
    defect: str | None

    @property
    def target(self) -> str:
        return f"{self.target_kind}:{self.target_name}"


@dataclass(frozen=True)
class Row:
    """One schedule as both readers see it."""

    name: str
    description: str
    enabled: bool
    target: str
    target_exists: bool
    cron_expression: str
    mode: str
    effect_class: str
    timeout_seconds: int
    defect: str | None
    next_due: datetime | None
    attempts: int
    last_run_id: str | None
    last_attempted_at: datetime | None
    last_status: str | None
    last_duration_seconds: float | None
    last_reason_code: str | None
    #: The executor exit code the REPORTED event carried. 124 is a timeout and 127 is
    #: claude not being on this machine; both read as an ordinary failure without it.
    last_exit_code: int | None
    consecutive_failures: int
    reading: str
    findings: tuple[health.Finding, ...]


@dataclass(frozen=True)
class Digest:
    """The whole read: every row, the node's reading, and where the records came from."""

    rows: tuple[Row, ...]
    reading: str
    ledger: history.LedgerState
    table: dict
    counts: dict[str, int]
    rendered_at: datetime
    utc_offset: timedelta
    source: str

    @property
    def refuses(self) -> bool:
        return self.reading == "UNHEALTHY"

    @property
    def findings(self) -> list[tuple[str, health.Finding]]:
        return [(row.name, finding) for row in self.rows for finding in row.findings]


def host_offset() -> timedelta:
    """The host current offset from UTC, which is the clock the runner fires in."""
    return datetime.now(timezone.utc).astimezone().utcoffset() or timedelta(0)


def stamp(moment: datetime | None) -> str:
    """One timestamp, in whatever clock it carries, with that clock named on it."""
    if moment is None:
        return "-"
    offset = moment.utcoffset() or timedelta(0)
    if not offset:
        return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    total = int(offset.total_seconds()) // 60
    sign = "+" if total >= 0 else "-"
    return moment.strftime("%Y-%m-%dT%H:%M:%S") + f"{sign}{abs(total) // 60:02d}:{abs(total) % 60:02d}"


def _table(root: Path, source: str) -> dict:
    """The rules table from the source being read.

    Its note, its rule prose and its blocking sentence are rendered into the page, so a
    page built from the working tree copy is one a clean checkout cannot reproduce.
    """
    if source == COMMIT:
        address = health.TABLE_PATH.relative_to(root.resolve()).as_posix() \
            if health.TABLE_PATH.is_relative_to(root.resolve()) \
            else "contracts/automation-health.json"
        return committed.table_at_head(root, address)
    return health.load()


def parse_stamp(text: str) -> datetime:
    """Read back a stamp this module wrote, in UTC or in an offset clock."""
    return datetime.fromisoformat(text)


def _accepted(path: Path, root: Path) -> Declared:
    decl = load_declaration(root, path)
    return Declared(decl.name, decl.description, decl.enabled, decl.target_kind,
                    decl.target_name, decl.spec.expression, decl.mode, decl.effect_class,
                    decl.timeout_seconds, None)


def _refused(path: Path, defect: str) -> Declared:
    """A file the loader would not take, read for whatever a reader can still be shown."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raw = {}
        defect = f"{defect or error}"
    if not isinstance(raw, dict):
        raw = {}
    target = raw.get("target") if isinstance(raw.get("target"), dict) else {}
    limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    return Declared(
        name=str(raw.get("name") or path.stem),
        description=str(raw.get("description", "")),
        enabled=bool(raw.get("enabled")),
        target_kind=str(target.get("kind", "")),
        target_name=str(target.get("name", "")),
        cron_expression=str(raw.get("cron", "")),
        mode=str(raw.get("mode", "")),
        effect_class=str(raw.get("effect_class", "")),
        timeout_seconds=int(limits.get("timeout_seconds") or 0),
        defect=defect,
    )


def _load_one(path: Path, root: Path) -> Declared:
    try:
        return _accepted(path, root)
    except DeclarationError as error:
        return _refused(path, str(error))


def declarations(root: Path, source: str = WORKTREE) -> list[Declared]:
    """Every declaration, sorted by name, refused ones included."""
    if source == COMMIT:
        return committed.declarations_at_head(root, _load_one)
    directory = root / SCHEDULES_DIR
    paths = sorted(p for p in directory.glob("*.json") if p.name != SCHEMA_NAME)
    return [_load_one(path, root) for path in paths]


def _target_present(root: Path, declared: Declared, source: str) -> bool:
    """Whether the declared target exists in the source being read, not on disk.

    Asking the working tree while reading declarations at HEAD is what let a moved
    workflow file put a `missing` cell and a TARGET_MISSING row into a page that a
    clean checkout re-derives without them.
    """
    if declared.target_kind not in ("workflow", "skill") or not declared.target_name:
        return False
    address = target_path(Path("."), declared.target_kind, declared.target_name).as_posix()
    if source == COMMIT:
        return committed.tracked_at_head(root, address)
    return (root / address).is_file()


def _facts(root: Path, declared: Declared, runs: list[history.Run],
           now: datetime, source: str) -> health.Facts:
    return health.Facts(
        name=declared.name,
        enabled=declared.enabled,
        target_exists=_target_present(root, declared, source),
        cron_expression=declared.cron_expression,
        timeout_seconds=declared.timeout_seconds,
        now=now,
        runs=tuple(runs),
        declaration_defect=declared.defect,
    )


def _next_due(declared: Declared, now: datetime, scan_days: int) -> datetime | None:
    try:
        spec = cron.parse(declared.cron_expression)
    except ValueError:
        return None
    return cron.next_after(spec, now, scan_days)


def _row(facts: health.Facts, declared: Declared, reading: health.Reading,
         scan_days: int) -> Row:
    last = history.newest(list(facts.runs))
    return Row(
        name=declared.name,
        description=declared.description,
        enabled=declared.enabled,
        target=declared.target,
        target_exists=facts.target_exists,
        cron_expression=declared.cron_expression,
        mode=declared.mode,
        effect_class=declared.effect_class,
        timeout_seconds=declared.timeout_seconds,
        defect=declared.defect,
        next_due=_next_due(declared, facts.now, scan_days),
        attempts=len(facts.runs),
        last_run_id=last.run_id if last else None,
        last_attempted_at=last.attempted_at.astimezone(facts.now.tzinfo) if last else None,
        last_status=reading.statuses[-1] if reading.statuses else None,
        last_duration_seconds=last.duration_seconds if last else None,
        last_reason_code=last.reason_code if last else None,
        last_exit_code=last.exit_code if last else None,
        consecutive_failures=health.consecutive_failures(facts),
        reading=reading.reading,
        findings=reading.findings,
    )


def assemble(root: Path, now: datetime | None = None, table: dict | None = None,
             utc_offset: timedelta | None = None, source: str = WORKTREE) -> Digest:
    """Read declarations and history at this instant, in this clock, and judge each schedule.

    ``now`` and ``utc_offset`` are both injectable because a surface whose output
    depends on an unnamed clock cannot be tested and cannot be byte-compared. The page
    records the instant and the offset it used and the check re-renders with both, so
    an unchanged tree reproduces the page on any host while the clock stays visible.
    """
    offset = host_offset() if utc_offset is None else utc_offset
    moment = ((now or datetime.now(timezone.utc)).astimezone(timezone(offset))
              .replace(second=0, microsecond=0))
    declared_table = table or _table(root, source)
    scan_days = declared_table["thresholds"]["scan_days"]
    rows = []
    for declared in declarations(root, source):
        runs = history.runs_for(root, declared.name)
        facts = _facts(root, declared, runs, moment, source)
        rows.append(_row(facts, declared, health.judge(facts, declared_table), scan_days))
    counts = {
        "declared": len(rows),
        "enabled": sum(1 for row in rows if row.enabled),
        "with_history": sum(1 for row in rows if row.attempts),
        "findings": sum(len(row.findings) for row in rows),
        "refusing": sum(1 for row in rows if row.reading == "UNHEALTHY"),
    }
    return Digest(tuple(rows), health.worst([row.reading for row in rows], declared_table),
                  history.ledger_state(root), declared_table, counts, moment, offset, source)
