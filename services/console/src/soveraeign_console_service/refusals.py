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
    """No live grant with the required capability, scoped to the target.

    The message names the capability and never the scope. A scope is an operator id,
    a channel or a thread, so saying it handed a caller holding nothing the name of
    whoever owns the record it just asked about - `close-session` answered "no live
    close:session grant scoped to Bdo" to anybody. That is a disclosure defect on its
    own and not part of the identity seam: even a perfectly authenticated caller
    holding nothing should not learn who owns a session.

    The scope is kept on the exception for a caller that already has it - the tests
    that must assert precisely, and any future in-process handler - because an
    attribute is not something the CLI or a receipt ever serialises. `cli.py` prints
    `reason_code` and `str(...)`; `append.refuse` records the same two.
    """

    reason_code = "NO_LIVE_GRANT"

    def __init__(self, message: str, capability: str = "", scope: str = "") -> None:
        super().__init__(message)
        self.capability = capability
        self.scope = scope


class ModelClaimWithoutProposal(ConsoleRefusal):
    """A MODEL post that claims must enter the kernel as a Proposal first."""

    reason_code = "CLAIM_WITHOUT_PROPOSAL"


class StaleCapabilityMap(ConsoleRefusal):
    """The capability projection discovery would answer from is behind its own sources.

    `console.discover-operations` declares `capability_map_fresh` as a precondition.
    Answering from a stale map would tell a participant it may do something the node no
    longer declares, which is worse than refusing.
    """

    reason_code = "MISSING_PRECONDITION"


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


class ActorAttributionMismatch(ConsoleRefusal):
    """The caller does not own the operator session it is acting through.

    A session identifies an operator; holding one does not make you that operator.
    `routes.py` refused this at the read route from the start and `core.post` did
    not, so a caller that knew any session id could write a post attributed to its
    owner. `contracts/capability-offices.json` declares the same actor kinds for
    both; `services/console/contracts/service.json` declares the precondition.
    """

    reason_code = "ACTOR_ATTRIBUTION_MISMATCH"


class LastIssuerStanding(ConsoleRefusal):
    """Withdrawing this grant would leave the node's permits office with no issuer.

    Revocation appends and the bootstrap is once-ever, so a node whose last live
    `grant:authority` is withdrawn can never issue another grant and no console
    operation can restore it. A legitimate operator could brick the office by
    accident. Carries `MISSING_PRECONDITION` rather than a new code: the precondition
    `another_issuer_remains` is what failed, and inventing vocabulary for it would
    add a refusal the kernel does not know.
    """

    reason_code = "MISSING_PRECONDITION"
