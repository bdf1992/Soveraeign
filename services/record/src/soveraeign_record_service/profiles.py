"""Which chain profile a store writes, and the deliberate act of changing it.

A chain profile is a property of the store, not of the code that opens it. That
reads like a detail and is not. `append` used to write whichever profile the
library named as current, so opening an existing journal with a newer service
upgraded it from the next row onward. Every reader that implements only the older
profile then stops verifying at that row - not because anything was tampered
with, but because a library moved underneath a store other readers share.

That is not hypothetical. It happened to `.local/console`, the live operator
journal: six `record-chain/v3` rows written by this branch's service landed on
top of 406 `record-chain/v1` rows, and every session running the older checkout
now gets `BrokenChain` at the first of them. The journal is intact and verifies
completely under a v3-aware reader. The readers are what broke.

So a store keeps writing what it already writes, and moving it forward is an act
somebody performs. ``adopt_profile`` appends the first entry under the new
profile, which puts the exact row where older readers stop inside the journal
rather than leaving it to be discovered by whoever opens the store next.
"""

from __future__ import annotations

from typing import Any

from .digest import (
    BOUND_DIGEST_PROFILE, CURRENT_PROFILE, DIGEST_PROFILE, LEGACY_DIGEST_PROFILE,
    digest_for_profile,
)
from .errors import BrokenChain, ProfileNotAdopted

#: Chain profiles oldest to newest. Position is what lets a downgrade be named
#: rather than merely rejected: adoption compares indices, so a profile added
#: later needs only to be appended here.
PROFILE_ORDER = (LEGACY_DIGEST_PROFILE, DIGEST_PROFILE, BOUND_DIGEST_PROFILE)


def digest_for_row(
    profile: str, previous: str, kind: str, subject: str, actor: str, payload: Any,
    *, entry_id: str | None = None, source_address: str | None = None,
    recorded_at: float | None = None,
) -> str:
    """Recompute one stored entry's digest under its own profile, or refuse it.

    The keyword arguments are what record-chain/v3 binds beyond v2. They are
    optional in the signature so a v1 or v2 caller is unchanged, and required by
    the v3 branch, which raises rather than grading an entry under a weaker
    profile than the one it was written with.

    A profile the reader does not implement is a broken chain rather than a bad
    argument: the row exists and cannot be verified, so the caller reading a
    journal gets the refusal it can act on.
    """
    try:
        return digest_for_profile(
            profile, previous, kind, subject, actor, payload, entry_id=entry_id,
            source_address=source_address, recorded_at=recorded_at,
        )
    except ValueError as error:
        raise BrokenChain(str(error)) from error


class ProfileSurface:
    """The profile a store writes, and the recorded transition that changes it.

    Mixed into `RecordService`, which owns the connection and the append path.
    """

    def writing_profile(self) -> str:
        """The profile this store writes, which is the one its newest entry uses.

        An empty store has no readers and no history to protect, so it starts at
        the strongest profile available. A store that already holds entries keeps
        its own, whatever the library currently considers current.
        """
        row = self.db.execute(
            "SELECT digest_profile FROM journal ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return row["digest_profile"] if row else CURRENT_PROFILE

    def adopt_profile(self, profile: str, actor: str) -> dict[str, Any]:
        """Move this store onto a newer chain profile, recording the move as an entry.

        Returns the entry that performs it. That entry is the first row under the
        new profile and therefore the exact point an older reader stops, which is
        why the transition is written into the journal instead of held beside it.

        Refuses a profile it does not implement, and refuses standing still or
        going backwards: both would record a transition that is not happening,
        and a journal that says a move occurred when none did is worse than one
        that never mentions the question.
        """
        if profile not in PROFILE_ORDER:
            raise ValueError(f"unknown record digest profile {profile!r}")
        current = self.writing_profile()
        if PROFILE_ORDER.index(profile) <= PROFILE_ORDER.index(current):
            raise ProfileNotAdopted(
                f"this store writes {current}; adopting {profile} would not move it forward"
            )
        return self._append(
            profile,
            "EVENT",
            f"record-chain-profile:{profile}",
            actor,
            {
                "adopted": profile,
                "superseded": current,
                "consequence": f"a reader implementing only {current} stops verifying "
                               "at this entry; every entry before it still verifies",
            },
        )
