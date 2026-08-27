"""Read the schedule declarations as they stand at HEAD, not as they stand on disk.

Eleven sessions share this checkout. A page derived from the working tree carries
whatever any of them has written and not committed, so it cannot be reproduced by
anyone who clones the commit it ships in - and the staleness check then refuses that
commit. Bdo ruled the same class on acceptance packet A5 for the orientation page:
the counted state is the committed state.

HEAD is materialised into a scratch directory and the ordinary loader is pointed at
that, so every check it runs - the schema, the file stem, the declared target - is
answered by the commit rather than by whatever is on disk at that instant. Nothing
here writes inside the repository.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar
import json
import subprocess
import tempfile

from sovschedule.declaration import SCHEDULES_DIR, SCHEMA_NAME, target_path

Declared = TypeVar("Declared")
Loader = Callable[[Path, Path], "Declared"]

#: Where a declaration is read from. WORKTREE is what is on disk now; COMMIT is what is
#: tracked at HEAD, which is the only source a page can be committed against.
WORKTREE = "WORKTREE"
COMMIT = "COMMIT"


class SourceUnavailable(RuntimeError):
    """The declarations could not be read from the source that was asked for."""


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                              encoding="utf-8", check=False)
    except OSError as error:
        raise SourceUnavailable(f"git could not be run: {error}") from None


def _committed_paths(root: Path) -> list[str]:
    """Declaration files tracked at HEAD, sorted, the schema excluded."""
    result = _git(root, "ls-tree", "--name-only", "HEAD", f"{SCHEDULES_DIR.as_posix()}/")
    if result.returncode != 0:
        raise SourceUnavailable(f"git ls-tree refused: {result.stderr.strip()}")
    return sorted(name for name in result.stdout.splitlines()
                  if name.endswith(".json") and not name.endswith(SCHEMA_NAME))


def _committed_text(root: Path, address: str) -> str:
    result = _git(root, "show", f"HEAD:{address}")
    if result.returncode != 0:
        raise SourceUnavailable(f"git show refused {address}: {result.stderr.strip()}")
    return result.stdout


def _tracked_at_head(root: Path, address: str) -> bool:
    return _git(root, "cat-file", "-e", f"HEAD:{address}").returncode == 0


def declarations_at_head(root: Path, load_one: Loader) -> list[Declared]:
    """Load the declarations at HEAD against a scratch tree that mirrors HEAD.

    A scratch tree rather than the real one, because every check the loader runs -
    the schema, the file stem, the target - would otherwise be answered by whatever
    eleven sessions have on disk at that instant, and the page would stop
    reproducing. Nothing here writes inside the repository.
    """
    addresses = _committed_paths(root)
    with tempfile.TemporaryDirectory() as name:
        scratch = Path(name)
        (scratch / SCHEDULES_DIR).mkdir(parents=True)
        (scratch / ".claude" / "workflows").mkdir(parents=True)
        (scratch / ".claude" / "skills").mkdir(parents=True)
        (scratch / SCHEDULES_DIR / SCHEMA_NAME).write_text(
            (root / SCHEDULES_DIR / SCHEMA_NAME).read_text(encoding="utf-8"),
            encoding="utf-8", newline="")
        out = []
        for address in addresses:
            local = scratch / SCHEDULES_DIR / Path(address).name
            local.write_text(_committed_text(root, address), encoding="utf-8", newline="")
            _mirror_target(root, scratch, local)
            out.append(load_one(local, scratch))
        return out


def _mirror_target(root: Path, scratch: Path, local: Path) -> None:
    """Create a stub for the declared target iff that target is tracked at HEAD."""
    try:
        raw = json.loads(local.read_text(encoding="utf-8"))
        target = raw["target"]
        address = target_path(Path("."), target["kind"], target["name"]).as_posix()
    except (json.JSONDecodeError, KeyError, TypeError):
        return
    if not _tracked_at_head(root, address):
        return
    stub = scratch / address
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text("", encoding="utf-8")
