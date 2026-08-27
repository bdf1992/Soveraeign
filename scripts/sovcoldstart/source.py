"""Where a probe reads from: a pinned commit, the working tree, or a spawned process.

Split out of `probes.py` so that one module owns *where a value comes from* and the other
owns *what values there are to take*. The two change for different reasons: a new question
adds a probe kind, while the concurrency and freshness rules here are settled by traps T6
and by how an exit code may be read.
"""

from __future__ import annotations

import json
import re
import subprocess
from hashlib import sha256
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIMEOUT = 600
BROKEN = ("Traceback (most recent call last)", "No such file or directory", "can't open file")

PINNED = ""
_SPAWNS: dict[tuple[str, ...], subprocess.CompletedProcess[str]] = {}


class ProbeError(RuntimeError):
    """A probe could not produce a value; the question is UNRESOLVED, never PASS."""


def pin(commit: str = "") -> str:
    """Freeze the commit that `scope: tracked` probes read.

    Five sessions write this tree. Without a pin, probe 1 and probe 177 can read different
    trees inside one run, and the scorecard reports a state that never existed. Trap T6
    says freeze a commit before measuring; this is that.
    """
    global PINNED
    PINNED = commit or _git(["rev-parse", "HEAD"]).strip()
    return PINNED


def _text(rel: str, tracked: bool = False) -> str:
    if tracked:
        return _git(["show", f"{PINNED or 'HEAD'}:{rel}"])
    return (ROOT / rel).read_text(encoding="utf-8")


def tracked_paths() -> list[str]:
    """Every path in the pinned commit.

    `git ls-files` reads the index, not a commit, so a staged-but-uncommitted file moved a
    count that claimed to describe the commit. A witness put `PINNED` thirty commits back
    and watched one probe answer for the pin and the next answer for the index inside one
    run. `pin()` exists precisely so that cannot happen, and four probe kinds were reaching
    around it.
    """
    return [line for line in
            _git(["ls-tree", "-r", "--name-only", PINNED or "HEAD"]).splitlines() if line]


def _walk(doc: Any, path: list[Any]) -> Any:
    for key in path:
        if isinstance(doc, dict):
            doc = doc[key]
        else:
            doc = doc[int(key)]
    return doc


def _doc(rel: str, path: list[Any] | None = None, tracked: bool = False) -> Any:
    return _walk(json.loads(_text(rel, tracked)), path or [])


def _run(argv: list[str], timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess[str]:
    """Spawn once per argv per run, and refuse to return a value from a crashed command.

    Five probes read `sov_traps.py` and four read `verify.py`. Spawning each separately
    let them observe five different trees and put four disagreeing answers on one card,
    and `verify.py` alone was most of the benchmark's wall time.

    A command that crashed used to be indistinguishable from one that found nothing: a
    grep count over a traceback returns 0, so a broken import read as `2 traps became 0`
    rather than as a broken probe.
    """
    key = (*argv, timeout)
    if key in _SPAWNS:
        return _SPAWNS[key]
    try:
        done = subprocess.run(
            argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError as exc:
        raise ProbeError(f"executable not found: {argv[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProbeError(f"timed out after {timeout}s: {' '.join(argv)}") from exc
    if done.returncode != 0 and any(mark in done.stderr for mark in BROKEN):
        raise ProbeError(f"{' '.join(argv)} crashed: {done.stderr.strip().splitlines()[-1]}")
    _SPAWNS[key] = done
    return done


def _git(args: list[str]) -> str:
    done = _run(["git", *args])
    if done.returncode != 0:
        raise ProbeError(f"git {' '.join(args)} exited {done.returncode}: {done.stderr.strip()}")
    return done.stdout


def _blob_at(commit: str, rel: str) -> bytes:
    """The exact bytes of one tracked file at one commit.

    Separate from `_git` on purpose. `_git` decodes stdout to text, and a digest taken over
    decoded text is not the digest of the file: newline translation and the codec both move
    bytes. A provenance check that compares a re-encoded reading against a stored digest is
    checking its own round trip.
    """
    done = subprocess.run(["git", "cat-file", "blob", f"{commit}:{rel}"], cwd=ROOT,
                          capture_output=True, timeout=DEFAULT_TIMEOUT)
    if done.returncode != 0:
        raise ProbeError(f"git cat-file blob {commit[:8]}:{rel} exited {done.returncode}: "
                         f"{done.stderr.decode('utf-8', 'replace').strip()}")
    return done.stdout


def _matches(spec: dict[str, Any]) -> list[str]:
    pattern = re.compile(spec["pattern"], re.MULTILINE)
    group = spec.get("group", 0)
    text = _text(spec["file"], spec.get("scope") == "tracked")
    return [m.group(group) for m in pattern.finditer(text)]


def _sort_key(value: str) -> tuple[int, str]:
    digits = re.findall(r"\d+", value)
    return (int(digits[0]) if digits else 0, value)


def digest_of(path: Path) -> str:
    """sha256 of a file's bytes, prefixed so a reader can tell what kind of digest it is."""
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def run_identity(commit: str, corpus_digest: str, observed_at: str, mode: str,
                 participant: str = "") -> str:
    """A run's identity, derived from what made it rather than assigned.

    Two runs of the same corpus at the same commit and instant in the same mode are the
    same run. Randomness here would make a replay produce a different record and make the
    id unrecomputable by anyone checking it.
    """
    material = f"{commit}\x00{corpus_digest}\x00{observed_at}\x00{mode}\x00{participant}"
    return sha256(material.encode("utf-8")).hexdigest()[:32]


def _glob_regex(pattern: str) -> re.Pattern[str]:
    """Compile one `:(glob)` pathspec: `*` and `?` stop at a `/`, `**` crosses them.

    Written out rather than delegated to `PurePosixPath.match`, which is not this: it treats
    `**` as a single non-crossing `*` and matches from the right rather than from the
    repository root. A witness measured the difference on the shipped corpus - question C07
    asks how many files sit under `reports/` and the matcher answered 23 where git answers
    47, so the question reported drift about the world in every run and a rebase would have
    written the matcher's error into the answer key as the truth.

    A sixth witness then found seven more disagreements in the replacement, so this is a
    second attempt and `scripts/tests/test_pinned_glob.py` grades it against git over an
    enumerated grammar rather than over the patterns the corpus happens to use today. What
    it got wrong the first time: a trailing `/` matched nothing where git matches the whole
    subtree, an empty pattern matched nothing where git matches everything, `//` was not
    collapsed, a `]` first in a class ended it, `[!…]` raised `re.error` out of the probe
    loop rather than recording ERROR, and `[[:digit:]]` warned about a nested set.
    """
    # No `.strip()`: git reads a leading or trailing space as part of the path, so
    # `  decisions/*.md  ` matches nothing there and must match nothing here. A corpus
    # pattern with stray whitespace is a typo to surface, not one to forgive.
    if "\\" in pattern:
        # git-on-Windows and git-on-Linux disagree about a backslash in a pathspec, so a
        # pattern containing one means different things on different machines. A benchmark
        # that asserts counts cannot carry one, and refusing is better than being right on
        # the machine it was written on.
        raise ProbeError(f"backslash in glob pattern {pattern!r}: its meaning is "
                         f"platform-dependent, so no count from it is comparable")
    text = pattern
    while "//" in text:
        text = text.replace("//", "/")
    while text.startswith("./"):
        text = text[2:]
        while "//" in text:
            text = text.replace("//", "/")
    if not text or text == "/":
        # git treats an empty pathspec as the whole tree.
        return re.compile(".*", re.DOTALL)
    if text.endswith("/"):
        # A *literal* directory prefix takes everything under it. Generalising that to any
        # pattern was wrong: git matches nothing for `**/` and `*/`, because a wildcard
        # segment before the slash names no directory. A witness measured 989 against 0.
        head = text.rstrip("/")
        if any(ch in head.split("/")[-1] for ch in "*?["):
            return re.compile(r"(?!)")
        text = head + "/**"
    # `.` as an interior segment is the same path, which git resolves and this did not.
    parts = [part for part in text.split("/") if part != "."]
    text = "/".join(parts)
    if not text:
        return re.compile(".*", re.DOTALL)
    segments = text.split("/")
    out = ["^"]
    for index, segment in enumerate(segments):
        last = index == len(segments) - 1
        if segment == "**":
            out.append(".*" if last else "(?:[^/]+/)*")
            continue
        out.append(_segment_regex(segment))
        if not last:
            out.append("/")
    return re.compile("".join(out) + "$", re.DOTALL)


def _segment_regex(segment: str) -> str:
    """One path segment, where `*` and `?` never cross a `/`."""
    out: list[str] = []
    cursor = 0
    while cursor < len(segment):
        char = segment[cursor]
        if char == "*":
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        elif char == "\\" and cursor + 1 < len(segment):
            out.append(re.escape(segment[cursor + 1]))
            cursor += 2
            continue
        elif char == "[":
            body, cursor = _class_body(segment, cursor)
            if body is None:
                out.append(re.escape(char))
                cursor += 1
                continue
            out.append(body)
            continue
        else:
            out.append(re.escape(char))
        cursor += 1
    return "".join(out)


def _class_body(segment: str, cursor: int) -> tuple[str | None, int]:
    """A bracket expression, or None when the `[` never closes and is a literal.

    `decisions/[0-9][0-9][0-9][0-9]*.md` is how the corpus asks for a numbered series. The
    fiddly parts are all real shell-glob rules: `!` negates, a `]` immediately after the
    opening (or after `!`) is a literal `]`, and a `[` with no close is itself a literal.
    """
    index = cursor + 1
    negate = index < len(segment) and segment[index] in "!^"
    if negate:
        index += 1
    if index < len(segment) and segment[index] == "]":
        index += 1
    close = segment.find("]", index)
    if close == -1:
        return None, cursor
    body = segment[cursor + 1:close]
    if body.startswith(("!", "^")):
        body = "^" + body[1:]
    # A literal `]` first stays first, and `[` inside a class is a literal in glob but the
    # start of a nested set in Python; escaping it keeps both readings the same.
    body = body.replace("[", "\\[")
    try:
        re.compile("[" + body + "]")
    except re.error:
        return None, cursor
    return "[" + body + "]", close + 1


def _pinned_glob(pattern: str) -> list[str]:
    """Paths in the pinned commit matching a `:(glob)` pathspec, anchored at the root.

    `git ls-files` reads the index rather than a commit, so every probe that used it
    reached around `pin()` and could answer for a different tree than its neighbours. That
    is the failure trap T6 names, and the pin exists to stop it.

    `:(glob)` semantics matter because a bare git pathspec lets `*` cross a `/`, so
    `scripts/*.py` matches every module in every subpackage - 228 files for a question about
    20. `scripts/tests/test_pinned_glob.py` grades this against git itself.
    """
    matcher = _glob_regex(pattern)
    return sorted(name for name in tracked_paths() if matcher.match(name))
