"""Rebuild the Kernel closure from its authored and governing inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from sovkernel.kernel_binding import build, load_manifests
from sovkernel.kernel_sources import closure_source_addresses, load_source_digests


def _rebuild_once(root: Path) -> tuple[
        dict[str, Any], dict[str, dict[str, Any]], dict[str, Any],
        dict[str, Any], list[dict[str, str]], list[str]]:
    manifests, manifest_sources = load_manifests(root)
    transitions = json.loads(
        (root / "contracts" / "kernel-transitions.json").read_text("utf-8"))
    paradigms = json.loads(
        (root / "contracts" / "kernel-paradigms.json").read_text("utf-8"))
    addresses = closure_source_addresses(manifest_sources, paradigms)
    source_digests, defects = load_source_digests(root, addresses)
    closure = build(
        manifests, transitions, paradigms, source_digests=source_digests)
    return closure, manifests, transitions, paradigms, source_digests, defects


def rebuild(root: Path) -> tuple[
        dict[str, Any], dict[str, dict[str, Any]], dict[str, Any],
        dict[str, Any], list[dict[str, str]], list[str]]:
    """Return a stable fresh closure and every input used to derive it.

    This is a loader, not a cache: callers cannot accidentally treat the checked-in
    closure fixture as an authority source or feed it back into Kernel declarations.
    Two complete reads defeat a source that moves between semantic parsing and raw-byte
    addressing; an unstable snapshot is visible as a defect rather than accepted.
    """
    first = _rebuild_once(root)
    second = _rebuild_once(root)
    defects = sorted(set(first[-1] + second[-1]))
    if first[:-1] != second[:-1]:
        defects.append(
            "SOURCE_SNAPSHOT_UNSTABLE: Kernel inputs changed while closure was rebuilt")
    closure, manifests, transitions, paradigms, source_digests, _ = second
    return closure, manifests, transitions, paradigms, source_digests, defects


__all__ = ["rebuild"]
