#!/usr/bin/env python3
"""Measure the shape of a real directory tree without recording its content.

The Asset Service interface work needs a corpus that behaves like a real
library: real size and age spreads, real duplicate rates, real filename
quality. Authoring one by hand only produces the states the author already
believes in, so this module measures a real tree and emits statistics a
generator can replay - the corpus inherits the mess, not the bytes.

Recorded: counts, extensions, and distributions of size, age, depth, directory
fan-out, duplicate-group size, and filename shape. Never recorded: content, a
filename verbatim, an absolute path, a content digest, or a directory name. The
rendered profile is scanned for email addresses and host paths before it is
written and a hit refuses the whole write rather than sanitizing it silently
(`history_sources.py` precedent).

Every profile declares what it left out, because a distribution that hides its
omissions is a projection nobody can rebuild.

Effect class: RECORD_LOCAL. Refusals: ROOT_UNREADABLE, PROFILE_CONTAMINATED.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import os
import re
import sys

PROFILE_FORMAT = "soveraeign-corpus-shape/1"
DEFAULT_EXCLUDES = (".git", "__pycache__", "node_modules", ".venv", "venv",
                    ".mypy_cache", ".pytest_cache", ".idea", ".vs")
HASH_CHUNK = 1 << 20
DEFAULT_MAX_HASH_BYTES = 256 << 20
DEFAULT_MAX_FILES = 2_000_000

# Shapes that must never enter a written profile. The path pattern is built
# without a literal user-path substring so repository lint never matches this
# module's own source text.
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HOST_PATH_PATTERN = re.compile(r"[/\\](?:Users|home)[/\\]")

DATE_PATTERN = re.compile(r"(?:19|20)\d{2}[-_.]?(?:0[1-9]|1[0-2])[-_.]?(?:0[1-9]|[12]\d|3[01])")
VERSION_PATTERN = re.compile(r"(?:^|[^a-z])v\d+(?:[^a-z]|$)|\(\d+\)", re.IGNORECASE)
REWORK_WORDS = ("final", "copy", "draft", "new", "old", "backup", "temp", "untitled")
NAME_FLAGS = ("has_digits", "has_date", "has_version", "all_lower")
TOKEN_SPLIT = re.compile(r"[ _\-.]+")
SIZE_BUCKETS = ((1 << 10, "<1K"), (1 << 12, "1K-4K"), (1 << 14, "4K-16K"),
                (1 << 16, "16K-64K"), (1 << 18, "64K-256K"), (1 << 20, "256K-1M"),
                (1 << 22, "1M-4M"), (1 << 24, "4M-16M"), (1 << 26, "16M-64M"),
                (1 << 28, "64M-256M"))
SIZE_OVERFLOW = ">256M"
SIZE_LABELS = tuple(label for _, label in SIZE_BUCKETS) + (SIZE_OVERFLOW,)


class ScanRefused(Exception):
    """A declared refusal, carrying the code the caller sees. Never a crash."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def size_bucket(size: int) -> str:
    """Readable label for the size band a byte count falls in."""
    for ceiling, label in SIZE_BUCKETS:
        if size < ceiling:
            return label
    return SIZE_OVERFLOW


def month_bucket(mtime: float) -> str:
    """Calendar month a modification time falls in, as `YYYY-MM`."""
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m")


def separator_style(stem: str) -> str:
    """Which separator a filename leans on, or `none` when it uses no separator."""
    counts = {"space": stem.count(" "), "underscore": stem.count("_"), "hyphen": stem.count("-")}
    leader = max(counts, key=lambda key: counts[key])
    return leader if counts[leader] else "none"


def name_shape(stem: str) -> dict[str, object]:
    """Structural facts about one filename. Carries no substring of the name itself."""
    lowered = stem.lower()
    tokens = [token for token in TOKEN_SPLIT.split(stem) if token]
    return {
        "length": len(stem),
        "tokens": len(tokens),
        "has_digits": any(character.isdigit() for character in stem),
        "has_date": bool(DATE_PATTERN.search(stem)),
        "has_version": bool(VERSION_PATTERN.search(stem)),
        "rework_word": next((word for word in REWORK_WORDS if word in lowered), None),
        "separator": separator_style(stem),
        "all_lower": stem.islower(),
    }


class Scan:
    """One read-only walk and the counters it fills."""

    def __init__(self, excludes: frozenset[str], max_files: int) -> None:
        self.excludes = excludes
        self.max_files = max_files
        self.files = 0
        self.directories = 0
        self.total_bytes = 0
        self.extensions: Counter[str] = Counter()
        self.sizes: Counter[str] = Counter()
        self.months: Counter[str] = Counter()
        self.depths: Counter[int] = Counter()
        self.fanout: Counter[int] = Counter()
        self.name_lengths: Counter[int] = Counter()
        self.name_tokens: Counter[int] = Counter()
        self.separators: Counter[str] = Counter()
        self.rework: Counter[str] = Counter()
        self.name_flags: Counter[str] = Counter()
        self.basenames: Counter[str] = Counter()
        self.by_size: defaultdict[int, list[str]] = defaultdict(list)
        self.excluded_directories = 0
        self.unreadable = 0
        self.truncated = False

    def walk(self, root: Path) -> None:
        """Fill every counter from one tree. Directory names are read, never stored."""
        try:
            os.scandir(root).close()
        except OSError as error:
            raise ScanRefused("ROOT_UNREADABLE") from error
        for current, subdirectories, filenames in os.walk(root, onerror=self._unreadable):
            kept = [name for name in subdirectories if name not in self.excludes]
            self.excluded_directories += len(subdirectories) - len(kept)
            subdirectories[:] = kept
            self.directories += 1
            self.fanout[len(kept) + len(filenames)] += 1
            depth = len(Path(current).relative_to(root).parts)
            for filename in filenames:
                if self.files >= self.max_files:
                    self.truncated = True
                    return
                self._record(Path(current) / filename, depth)

    def _unreadable(self, _error: OSError) -> None:
        self.unreadable += 1

    def _record(self, path: Path, depth: int) -> None:
        try:
            stat = path.stat()
        except OSError:
            self.unreadable += 1
            return
        self.files += 1
        self.total_bytes += stat.st_size
        self.extensions[path.suffix.lower() or "<none>"] += 1
        self.sizes[size_bucket(stat.st_size)] += 1
        self.months[month_bucket(stat.st_mtime)] += 1
        self.depths[depth] += 1
        self.basenames[path.name.lower()] += 1
        shape = name_shape(path.stem)
        self.name_lengths[int(shape["length"])] += 1
        self.name_tokens[int(shape["tokens"])] += 1
        self.separators[str(shape["separator"])] += 1
        if shape["rework_word"]:
            self.rework[str(shape["rework_word"])] += 1
        self.name_flags.update(flag for flag in NAME_FLAGS if shape[flag])
        if stat.st_size:
            self.by_size[stat.st_size].append(str(path))


def digest_file(path: Path, chunk: int = HASH_CHUNK) -> str:
    """SHA-256 of one file, read in bounded chunks. The digest never leaves this run."""
    accumulator = sha256()
    with open(path, "rb") as handle:
        block = handle.read(chunk)
        while block:
            accumulator.update(block)
            block = handle.read(chunk)
    return accumulator.hexdigest()


def duplicate_reading(scan: Scan, max_hash_bytes: int) -> dict[str, object]:
    """Duplicate-group sizes by content, hashing only files whose byte length collides."""
    groups: Counter[int] = Counter()
    redundant_files = 0
    redundant_bytes = 0
    unhashed = 0
    for size, paths in scan.by_size.items():
        if len(paths) < 2:
            continue
        if size > max_hash_bytes:
            unhashed += len(paths)
            continue
        by_digest: defaultdict[str, int] = defaultdict(int)
        for path in paths:
            try:
                by_digest[digest_file(Path(path))] += 1
            except OSError:
                unhashed += 1
        for count in by_digest.values():
            if count > 1:
                groups[count] += 1
                redundant_files += count - 1
                redundant_bytes += size * (count - 1)
    return {
        "group_sizes": {str(key): value for key, value in sorted(groups.items())},
        "groups": sum(groups.values()),
        "redundant_files": redundant_files,
        "redundant_bytes": redundant_bytes,
        "unhashed_files": unhashed,
    }


def build_profile(scan: Scan, duplicates: dict[str, object], label: str,
                  max_hash_bytes: int) -> dict[str, object]:
    """Render the counters as the profile a corpus generator replays."""
    collisions = sum(1 for count in scan.basenames.values() if count > 1)
    return {
        "profile_format": PROFILE_FORMAT,
        "scan_label": label,
        "captured_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "effect_class": "RECORD_LOCAL",
        "counts": {"files": scan.files, "directories": scan.directories,
                   "total_bytes": scan.total_bytes},
        "extensions": dict(scan.extensions.most_common()),
        "size_buckets": {name: scan.sizes[name] for name in SIZE_LABELS if scan.sizes[name]},
        "month_buckets": dict(sorted(scan.months.items())),
        "depth": {str(key): value for key, value in sorted(scan.depths.items())},
        "directory_fanout": {str(key): value for key, value in sorted(scan.fanout.items())},
        "name_shape": {
            "length": {str(key): value for key, value in sorted(scan.name_lengths.items())},
            "tokens": {str(key): value for key, value in sorted(scan.name_tokens.items())},
            "separator": dict(scan.separators.most_common()),
            "rework_words": dict(scan.rework.most_common()),
            "flags": dict(scan.name_flags.most_common()),
            "repeated_basenames": collisions,
        },
        "duplicates": duplicates,
        "omissions": {
            "excluded_directory_names": sorted(scan.excludes),
            "excluded_directories": scan.excluded_directories,
            "unreadable_entries": scan.unreadable,
            "max_hash_bytes": max_hash_bytes,
            "truncated": scan.truncated,
        },
    }


def refuse_contaminated(rendered: str) -> None:
    """Refuse the whole write when a rendered profile carries an address it must not."""
    if EMAIL_PATTERN.search(rendered) or HOST_PATH_PATTERN.search(rendered):
        raise ScanRefused("PROFILE_CONTAMINATED")


def build_parser() -> argparse.ArgumentParser:
    """Command surface for one scan."""
    parser = argparse.ArgumentParser(prog="corpus-shape")
    parser.add_argument("root")
    parser.add_argument("--label", required=True, help="what this tree is, for the profile")
    parser.add_argument("--out", help="where to write the profile; stdout when absent")
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--no-default-excludes", action="store_true")
    parser.add_argument("--max-hash-bytes", type=int, default=DEFAULT_MAX_HASH_BYTES)
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Scan, aggregate, refuse or write. Returns the process exit code."""
    args = build_parser().parse_args(argv)
    excludes = set(args.exclude)
    if not args.no_default_excludes:
        excludes |= set(DEFAULT_EXCLUDES)
    scan = Scan(frozenset(excludes), args.max_files)
    try:
        scan.walk(Path(args.root).resolve())
        duplicates = duplicate_reading(scan, args.max_hash_bytes)
        profile = build_profile(scan, duplicates, args.label, args.max_hash_bytes)
        rendered = json.dumps(profile, indent=2, sort_keys=True) + "\n"
        refuse_contaminated(rendered)
    except ScanRefused as refused:
        print(json.dumps({"refused": refused.code}))
        return 2
    if args.out:
        destination = Path(args.out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8", newline="\n")
        print(json.dumps({"written": args.out, "files": scan.files}, indent=2))
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
