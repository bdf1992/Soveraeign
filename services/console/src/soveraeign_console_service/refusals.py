"""The Console Service refusal vocabulary, in one place.

`contracts/kernel-parity.json` checks a participant's refusals against the kernel
refusals they realize, by driving both sides on the same fact. That check reads a
declared vocabulary, so the vocabulary is a module rather than exception classes
scattered across the transitions that raise them.

Every refusal carries a `reason_code`. A receipt records the code, never the
message, so a caller matches on a stable value instead of parsing prose.
"""

from __future__ import annotations


class ConsoleRefusal(Exception):
    """A refused console transition."""

    reason_code = "REFUSED"


class AuthorityRefused(ConsoleRefusal):
    """No live grant with the required capability, scoped to the target."""

    reason_code = "NO_LIVE_GRANT"


class ModelClaimWithoutProposal(ConsoleRefusal):
    """A MODEL post that claims must enter the kernel as a Proposal first."""

    reason_code = "CLAIM_WITHOUT_PROPOSAL"


class SessionClosed(ConsoleRefusal):
    """The operator session is CLOSED; a closed session is a read position, not a writer."""

    reason_code = "SESSION_CLOSED"


class ThreadArchived(ConsoleRefusal):
    """The thread is ARCHIVED; a new thread carries the work forward."""

    reason_code = "THREAD_ARCHIVED"


class PinIncomplete(ConsoleRefusal):
    """A pinned thread needs both an address and the digest of what it pinned."""

    reason_code = "PIN_INCOMPLETE"


class ForeignNodeRecord(ConsoleRefusal):
    """The transition would write a record belonging to a node this console does not serve."""

    reason_code = "FOREIGN_NODE_RECORD"


class StandingClaim(ConsoleRefusal):
    """A console record claimed standing above RECORDED."""

    reason_code = "STANDING_NOT_OWNED"


class UnknownRecord(KeyError):
    """The named console record is not in the journal."""
