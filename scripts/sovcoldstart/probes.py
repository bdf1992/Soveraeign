"""The probe kinds a corpus entry may name, and the dispatch table that runs them.

There is no eval: an entry can only reach behaviour this module already implements, so
reading `corpus.json` is enough to know exactly what a run will execute. Where each value
is read from - a pinned commit, the working tree, or a subprocess - belongs to `source`.
"""

from __future__ import annotations

import glob as globmod
import json
import re
from pathlib import Path
from typing import Any

from sovcoldstart.commands import (
    p_ahead_behind,
    p_cmd_exit,
    p_cmd_grep_count,
    p_cmd_out,
    p_git_count,
    p_git_lines,
    p_git_out,
    p_verify_failures,
)
from sovcoldstart.source import (
    _glob_regex,
    _pinned_glob,
    DEFAULT_TIMEOUT,
    ROOT,
    ProbeError,
    _doc,
    _git,
    _matches,
    tracked_paths,
    _run,
    _text,
    _sort_key,
    pin,
)

__all__ = ["COST", "FAST_COSTS", "PROBES", "ProbeError", "cost_of", "execute", "pin"]


# --- probe kinds -----------------------------------------------------------------


def p_glob_count(spec: dict[str, Any]) -> int:
    """Files matching a glob. `scope: tracked` counts the commit instead of the disk scan.

    A scan sees every sibling session's unsaved work. One untracked draft under decisions/
    made three separate questions report drift that no landing caused.
    """
    if spec.get("scope") == "tracked":
        names = _pinned_glob(spec["pattern"])
        if spec.get("exclude"):
            drop = re.compile(spec["exclude"])
            names = [n for n in names if not drop.match(Path(n).name)]
        return len(names)
    hits = globmod.glob(str(ROOT / spec["pattern"]), recursive=True)
    want = Path.is_dir if spec.get("dirs") else Path.is_file
    kept = [h for h in hits if want(Path(h))]
    if spec.get("exclude"):
        drop = re.compile(spec["exclude"])
        kept = [h for h in kept if not drop.search(Path(h).name)]
    return len(kept)


def p_git_ls_count(spec: dict[str, Any]) -> int:
    """Files tracked at HEAD matching a pathspec. Committed state, not the working tree.

    The `:(glob)` prefix matters: in a bare git pathspec `*` crosses a `/`, so
    `scripts/*.py` matches every module in every subpackage. Under `:(glob)` it does not,
    which is what every corpus pattern was written to mean.
    """
    return len(_pinned_glob(spec["pattern"]))





def p_json_len(spec: dict[str, Any]) -> int:
    return len(_doc(spec["file"], spec.get("path"), spec.get("scope") == "tracked"))


def p_json_get(spec: dict[str, Any]) -> Any:
    return _doc(spec["file"], spec.get("path"), spec.get("scope") == "tracked")


def p_json_keys(spec: dict[str, Any]) -> list[str]:
    return sorted(_doc(spec["file"], spec.get("path"), spec.get("scope") == "tracked"))


def p_json_field_set(spec: dict[str, Any]) -> list[str]:
    """Collect one field from every element of a list-valued JSON path."""
    items = _doc(spec["file"], spec.get("path"), spec.get("scope") == "tracked")
    return sorted({str(item[spec["field"]]) for item in items})


def p_regex_count(spec: dict[str, Any]) -> int:
    return len(_matches(spec))


def p_regex_unique(spec: dict[str, Any]) -> list[str]:
    return sorted(set(_matches(spec)), key=_sort_key)


def p_regex_first(spec: dict[str, Any]) -> str:
    hits = _matches(spec)
    if not hits:
        raise ProbeError(f"pattern {spec['pattern']!r} not found in {spec['file']}")
    return hits[0].strip()


def p_file_exists(spec: dict[str, Any]) -> bool:
    """Whether a path is there. `scope: tracked` asks the commit, which is the default.

    It had no scope at all and answered from a disk scan, so it reported True for another
    session's untracked draft. That is the hazard `glob_count` was already fixed for, in the
    one probe kind whose whole answer is a yes or a no.
    """
    if spec.get("scope", "tracked") == "tracked":
        return spec["path"] in set(tracked_paths())
    return (ROOT / spec["path"]).exists()


def p_manifest_ops(spec: dict[str, Any]) -> int:
    """Sum declared operations across service manifests, in the working tree or at HEAD."""
    pattern = "services/*/contracts/service.json"
    if spec.get("scope") == "tracked":
        docs = [json.loads(_text(p, True)) for p in _pinned_glob(pattern)]
    else:
        found = sorted(globmod.glob(str(ROOT / pattern)))
        docs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in found]
    return sum(len(doc.get("operations") or []) for doc in docs)


def p_number_gaps(spec: dict[str, Any]) -> list[str]:
    """Missing integers in a zero-padded numbered file series, e.g. decisions/0043.

    Reads the commit by default: an unlanded draft would otherwise invent phantom gaps
    above it, and a gap that means `reserved but not written` is a different fact from a
    gap that means `allocated twice on branches that never merged`.
    """
    if spec.get("scope", "tracked") == "tracked":
        found = _pinned_glob(spec["pattern"])
    else:
        found = globmod.glob(str(ROOT / spec["pattern"]))
    numbers = sorted(int(m.group(1)) for m in (re.match(r"(\d+)", Path(p).name) for p in found) if m)
    if not numbers:
        raise ProbeError(f"no numbered files matched {spec['pattern']}")
    width = spec.get("width", 4)
    return [str(n).zfill(width) for n in range(min(numbers), max(numbers) + 1) if n not in numbers]




def p_region_tokens(spec: dict[str, Any]) -> list[str]:
    """Every token inside a region located by its surroundings, not by the tokens.

    The difference matters and a witness had to point it out. A probe whose pattern is an
    alternation of the answers - `RECORD_LOCAL|RESOURCE_CONSUMPTION|EXTERNAL_WORLD` - can
    report one of the three vanishing and can never report a fourth being added, so it
    cannot detect the change that would matter most. Four questions were written that way,
    two of them tier 0 and FATAL.

    Here `region` is matched against the prose or structure around the list, and `token`
    takes whatever is inside it. Adding a twelfth protected boundary or an eighth distinct
    state changes the answer without anyone editing the probe.
    """
    text = _text(spec["file"], spec.get("scope", "tracked") == "tracked")
    region = re.search(spec["region"], text, re.MULTILINE | re.DOTALL)
    if not region:
        raise ProbeError(f"no region matching {spec['region']!r} in {spec['file']}")
    inside = region.group(spec.get("region_group", 0))
    found = [m.group(spec.get("group", 1)) for m in
             re.finditer(spec["token"], inside, re.MULTILINE)]
    if not found:
        raise ProbeError(f"region matched but no {spec['token']!r} inside it")
    return sorted(set(found))


def p_yaml_block_count(spec: dict[str, Any]) -> int:
    """Count the list items under one top-level YAML key.

    Counting `  - id: O<n>` across the whole file matched on indentation and key order, so
    renumbering a hold, or writing `reason:` after `blocks:`, silently returned zero - and
    zero here reads as `nothing waits on the owner`. Anchoring to the block makes the count
    a reading of that block and of nothing else.
    """
    text = _text(spec["file"], spec.get("scope", "tracked") == "tracked")
    head = re.escape(spec["key"])
    block = re.search(rf"^{head}:[^\n]*\n((?:[ \t]+[^\n]*\n|\n)*)", text, re.MULTILINE)
    if not block:
        raise ProbeError(f"no top-level key {spec['key']!r} in {spec['file']}")
    return len(re.findall(r"^  - ", block.group(1), re.MULTILINE))



PROBES = {
    "glob_count": p_glob_count,
    "git_ls_count": p_git_ls_count,
    "git_count": p_git_count,
    "git_out": p_git_out,
    "git_lines": p_git_lines,
    "cmd_exit": p_cmd_exit,
    "cmd_out": p_cmd_out,
    "cmd_grep_count": p_cmd_grep_count,
    "json_len": p_json_len,
    "json_get": p_json_get,
    "json_keys": p_json_keys,
    "json_field_set": p_json_field_set,
    "regex_count": p_regex_count,
    "regex_unique": p_regex_unique,
    "regex_first": p_regex_first,
    "file_exists": p_file_exists,
    "manifest_ops": p_manifest_ops,
    "number_gaps": p_number_gaps,
    "ahead_behind": p_ahead_behind,
    "verify_failures": p_verify_failures,
    "region_tokens": p_region_tokens,
    "yaml_block_count": p_yaml_block_count,
}


COST = {
    "glob_count": "PURE", "json_len": "PURE", "json_get": "PURE", "json_keys": "PURE",
    "json_field_set": "PURE", "regex_count": "PURE", "regex_unique": "PURE",
    "regex_first": "PURE", "file_exists": "PURE", "number_gaps": "PURE",
    "region_tokens": "GIT",
    "yaml_block_count": "GIT",
    "git_ls_count": "GIT", "git_count": "GIT", "git_out": "GIT", "git_lines": "GIT",
    "ahead_behind": "GIT", "manifest_ops": "GIT",
    "cmd_exit": "SHELL", "cmd_out": "SHELL", "cmd_grep_count": "SHELL",
    "verify_failures": "SHELL",
}
FAST_COSTS = ("PURE", "GIT")


#: Executables that reach nothing outside this repository. Anything else is graded NET, so
#: `--offline` skips it: a probe shelling to a model runtime or an HTTP client stayed in an
#: offline run because it was kept out by a hand-written `network: true` on the question,
#: and nothing checked that the flag was there. The old test was `"gh" in argv[0]`, which is
#: trap T3's shape - it graded `highlight` as reaching the network.
LOCAL_EXECUTABLES = ("python", "python3", "git")


def _reaches_out(argv: list[str]) -> bool:
    """Whether this command can touch anything beyond the repository."""
    name = Path((argv or [""])[0]).name.lower()
    for suffix in (".exe", ".cmd", ".bat"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name not in LOCAL_EXECUTABLES


#: Probe kinds whose body reads the commit unless told otherwise. `cost_of` used to read
#: the `scope` key as written, so a probe that inherits `tracked` was graded PURE - "reads
#: files" - while spawning git. C17 is the live instance.
TRACKED_BY_DEFAULT = ("file_exists", "number_gaps", "region_tokens", "yaml_block_count")


def _scoped(spec: dict[str, Any], base: str) -> str:
    """`scope: tracked` means the probe spawns git, whatever its kind says it reads."""
    if base != "PURE":
        return base
    default = "tracked" if spec.get("kind") in TRACKED_BY_DEFAULT else "worktree"
    return "GIT" if spec.get("scope", default) == "tracked" else base


def cost_of(spec: dict[str, Any] | None) -> str:
    """PURE reads files, GIT shells to git in milliseconds, SHELL runs a repository gate.

    A SHELL probe can take forty seconds - `verify.py` alone does - so a session-start or
    pre-commit run selects PURE and GIT only, and says how much of each tier that left
    unmeasured rather than quietly scoring a smaller corpus.
    """
    if spec is None:
        return "NONE"
    if spec.get("kind") in ("cmd_exit", "cmd_out", "cmd_grep_count") and _reaches_out(spec.get("argv") or [""]):
        return "NET"
    return _scoped(spec, COST.get(spec.get("kind", ""), "SHELL"))


def execute(spec: dict[str, Any]) -> Any:
    """Run one declarative probe. Raises ProbeError rather than returning a wrong value."""
    kind = spec.get("kind")
    if kind not in PROBES:
        raise ProbeError(f"unknown probe kind {kind!r}")
    return PROBES[kind](spec)
