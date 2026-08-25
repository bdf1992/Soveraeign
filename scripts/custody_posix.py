"""POSIX custody enforcement, and an honest answer where the platform has none.

Custody is enforced with POSIX ownership and mode bits: the node directory is
owned by the effective user and readable by nobody else. Windows has neither
``os.geteuid`` nor meaningful mode bits, so the checks cannot run there.

The wrong repair is to let them pass. A receipt saying custody ownership was
verified, written on a platform that cannot verify it, is a claim with no
evidence behind it -- the green-build-as-authority failure ``AGENTS.md``
refuses. So the checks are skipped and every receipt records that they were
skipped and why. A reader can then tell an enforced custody from an unenforced
one without reading the code that wrote the receipt.
"""

from __future__ import annotations

import os
import stat

ENFORCED = "POSIX"
UNENFORCED = "UNAVAILABLE_ON_THIS_PLATFORM"

available = hasattr(os, "geteuid") and hasattr(os, "fchmod")


def enforcement() -> str:
    """What a receipt written on this platform may claim about custody identity."""
    return ENFORCED if available else UNENFORCED


def effective() -> tuple[int, int]:
    """Effective uid and gid, or (-1, -1) where the platform has no such identity."""
    if not available:
        return (-1, -1)
    return (os.geteuid(), os.getegid())


def identity_matches(info: os.stat_result, expected_uid: int, expected_gid: int) -> bool:
    """Whether a path is owned by the expected identity, or True where unknowable."""
    if not available:
        return True
    return info.st_uid == expected_uid and info.st_gid == expected_gid


def mode_is_unsafe(info: os.stat_result, mask: int = 0o077) -> bool:
    """Whether a path is readable beyond its owner, or False where mode bits are inert.

    Windows reports 0o666 or 0o777 for everything, so masking there would refuse
    every path rather than the unsafe ones.
    """
    if not available:
        return False
    return bool(stat.S_IMODE(info.st_mode) & mask)


def set_descriptor_mode(descriptor: int, mode: int) -> None:
    """Apply a mode to an open descriptor where the platform supports it."""
    if available:
        os.fchmod(descriptor, mode)


def set_path_mode(path, mode: int) -> None:
    """Apply a mode to a path where the platform supports it."""
    if available:
        os.chmod(path, mode)
