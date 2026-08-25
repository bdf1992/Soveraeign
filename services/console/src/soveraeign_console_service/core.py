"""Console Service: the operator continuity record path.

`services/console/CHARTER.md` describes five operator surfaces. This module
implements the one the others stand on: the threaded record path through which
a human operator and a model operator reach the same conversation, in the same
authoritative state, across separate sessions.

Nothing here stores state of its own except immutable post payloads. Every
console record is appended to the Record Service journal as an `EVENT` followed
by a terminal `RECEIPT`; the console read path is a projection rebuilt from that
journal alone (`continuity.py`). A projection is never authoritative.

The parity requirement in `conformance/006-thread-post-parity.yaml` is
structural rather than promised: `post` takes one operation type and checks one
capability regardless of `actor_kind`, and the binding an operator reached
through appears only as `interface_id` on the receipt.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, Sequence
import hashlib
import re
import time
import uuid

from soveraeign_console_service import append, authority, publication, reads
from soveraeign_console_service.authority import (
    ENFORCED_AUTHORITY,
    POST_CAPABILITY,
    PUBLISH_CAPABILITY,
)
from soveraeign_console_service.refusals import (
    ConsoleRefusal,
    ForeignNodeRecord,
    ModelClaimWithoutProposal,
    PinIncomplete,
    SessionClosed,
    ThreadArchived,
)
from soveraeign_record_service import RecordService

# A console record enters at RECORDED and never above it. Admission, ratification
# and effectiveness are kernel transitions this service does not own.
ENTRY_STANDING = "RECORDED"
POST_OPERATION = "console.post"
# The node identifier shape `contracts/node-identity.schema.json` declares. Checked
# here so a malformed node reaches the constructor rather than the journal.
NODE_ID = re.compile(r"^node:[a-z0-9][a-z0-9-]*$")


def _identifier(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


class ConsoleService:
    """Operator sessions, channels, threads and posts over an append-preserving journal.

    The journal is injected rather than owned. The Record Service declares a
    `console-projection` port; the console writes through it instead of keeping a
    second semantic authority beside it.
    """

    def __init__(self, record: RecordService, root: str | Path, node_id: str,
                 clock: Callable[[], float] | None = None):
        """`node_id` is the node this console serves, per contracts/node-identity.schema.json.

        It has no default. A console that could run without naming its node would
        emit records that do not say where they came from, and a crossing would then
        have no way to tell a peer's thread from a local one (decisions/0039).
        """
        if not NODE_ID.match(node_id):
            raise ValueError(f"node_id {node_id!r} is not a node identifier")
        self.record = record
        self.node_id = node_id
        self.root = Path(root)
        self.posts = self.root / "posts"
        self.posts.mkdir(parents=True, exist_ok=True)
        self._clock = clock or time.time

    # ---- authority ---------------------------------------------------------

    def grant(self, operator_id: str, capability: str, scope: str,
              granted_by: str = "Bdo") -> dict[str, Any]:
        """Record a live grant in the journal, where it outlives this process."""
        payload = authority.grant_payload(operator_id, capability, scope,
                                          granted_by, self._stamp())
        return self._emit(authority.GRANT_KIND, payload["grant_id"], granted_by,
                          payload, "console.grant")

    def revoke(self, grant_id: str, revoked_by: str = "Bdo") -> dict[str, Any]:
        """Withdraw a grant by appending. It refuses the next operation, not past ones."""
        payload = authority.revocation_payload(grant_id, revoked_by, self._stamp())
        return self._emit(authority.REVOCATION_KIND, grant_id, revoked_by,
                          payload, "console.revoke")

    def grants(self, operator_id: str | None = None) -> list[dict[str, Any]]:
        """Every grant that is live right now, optionally for one operator."""
        live = authority.live_grants(self.record.reconstruct()).values()
        return sorted((record for record in live
                       if operator_id is None or record["operator_id"] == operator_id),
                      key=lambda record: record["grant_id"])

    def _grant_id(self, operator_id: str, capability: str, scope: str, event: str,
                  subject: str, entries: list[dict[str, Any]] | None = None) -> str:
        """The live grant admitting this operation, or a refusal written to the journal."""
        return authority.require(self.record, self._entries(entries), operator_id,
                                 capability, scope, event, subject)

    # ---- append path -------------------------------------------------------

    def _emit(self, kind: str, subject: str, actor: str, payload: dict[str, Any],
              event: str, grant_ids: Sequence[str] = ()) -> dict[str, Any]:
        return append.emit(self.record, kind, subject, actor, payload, event, grant_ids)

    def _refuse(self, error: ConsoleRefusal, event: str, subject: str,
                actor: str) -> ConsoleRefusal:
        return append.refuse(self.record, error, event, subject, actor)

    # ---- transitions -------------------------------------------------------

    def open_channel(self, operator_id: str, name: str, domain: str) -> dict[str, Any]:
        """Open a named domain container for threads."""
        channel_id = _identifier("channel")
        grant = self._grant_id(operator_id, ENFORCED_AUTHORITY["console.open-channel"],
                               domain, "console.open-channel", channel_id)
        return self._emit("channel", channel_id, operator_id, {
            "node_id": self.node_id,
            "channel_id": channel_id, "name": name, "domain": domain,
            "opened_by": operator_id, "opened_at": self._stamp(),
            "standing": ENTRY_STANDING,
        }, "console.open-channel", [grant])

    def open_thread(self, operator_id: str, channel_id: str, title: str,
                    pinned_address: str | None = None,
                    pinned_digest: str | None = None) -> dict[str, Any]:
        """Open a bounded conversation, optionally pinned to an exact record address."""
        thread_id = _identifier("thread")
        if (pinned_address is None) != (pinned_digest is None):
            raise self._refuse(
                PinIncomplete("a pinned thread carries both an address and its digest"),
                "console.open-thread", thread_id, operator_id)
        grant = self._grant_id(operator_id, ENFORCED_AUTHORITY["console.open-thread"],
                               channel_id, "console.open-thread", thread_id)
        return self._emit("thread", thread_id, operator_id, {
            "node_id": self.node_id,
            "thread_id": thread_id, "channel_id": channel_id, "title": title,
            "opened_by": operator_id, "opened_at": self._stamp(), "lifecycle": "OPEN",
            "pinned_address": pinned_address, "pinned_digest": pinned_digest,
            "standing": ENTRY_STANDING,
        }, "console.open-thread", [grant])

    def archive_thread(self, operator_id: str, thread_id: str) -> dict[str, Any]:
        """Archive a thread. Its posts stay readable; no new post may land in it."""
        entries = self.record.reconstruct()
        thread = self._thread(thread_id, entries)
        channel_id = thread["channel_id"]
        foreign = publication.foreign_thread(thread, self.node_id)
        if foreign is not None:
            raise self._refuse(
                ForeignNodeRecord(f"thread {thread_id} {foreign}"),
                "console.archive-thread", thread_id, operator_id)
        grant = self._grant_id(operator_id, ENFORCED_AUTHORITY["console.archive-thread"],
                               channel_id, "console.archive-thread", thread_id, entries)
        return self._emit("thread-lifecycle", thread_id, operator_id, {
            "node_id": self.node_id,
            "thread_id": thread_id, "channel_id": channel_id, "lifecycle": "ARCHIVED",
            "standing": ENTRY_STANDING,
        }, "console.archive-thread", [grant])

    def publish_thread(self, operator_id: str, thread_id: str) -> dict[str, Any]:
        """Mark a thread readable outside the node.

        This is the record `contracts/public-projection.schema.json` renders. The
        projection decides nothing; it reads what this transition wrote, which is why
        publishing needs its own capability rather than riding on `open-thread`.
        """
        entries = self.record.reconstruct()
        foreign = publication.foreign_thread(self._thread(thread_id, entries), self.node_id)
        if foreign is not None:
            raise self._refuse(
                ForeignNodeRecord(f"thread {thread_id} {foreign}; publishing it here would "
                                  "republish a peer's record under this node's name"),
                "console.publish-thread", thread_id, operator_id)
        publication_id = _identifier("publication")
        grant = self._grant_id(operator_id, PUBLISH_CAPABILITY, thread_id,
                               "console.publish-thread", publication_id, entries)
        return self._emit("publication", publication_id, operator_id,
                          publication.publication_payload(
                              self.node_id, publication_id, thread_id, operator_id,
                              self._stamp(), ENTRY_STANDING),
                          "console.publish-thread", [grant])

    def withdraw_publication(self, operator_id: str, publication_id: str) -> dict[str, Any]:
        """Stop rendering a thread outwardly. The mark stays readable; only the view changes.

        Withdrawal appends. It never claims the thread was not public, and it never
        claims nobody read it while it was.
        """
        entries = self.record.reconstruct()
        mark = reads.publication(entries, publication_id)
        grant = self._grant_id(operator_id, PUBLISH_CAPABILITY, mark["thread_id"],
                               "console.withdraw-publication", publication_id, entries)
        return self._emit("publication-lifecycle", publication_id, operator_id,
                          publication.withdrawal_payload(
                              self.node_id, publication_id, mark["thread_id"],
                              self._stamp(), ENTRY_STANDING),
                          "console.withdraw-publication", [grant])

    def open_session(self, operator_id: str, actor_kind: str,
                     binding_id: str) -> dict[str, Any]:
        """Open one operator's continuity through a named binding.

        A binding realizes an interface and grants no authority. It is carried so a
        later reader can see which surface a post arrived through.
        """
        if actor_kind not in ("HUMAN", "MODEL"):
            raise ValueError(f"unknown actor_kind {actor_kind!r}")
        session_id = _identifier("session")
        return self._emit("operator-session", session_id, operator_id, {
            "session_id": session_id, "operator_id": operator_id,
            "actor_kind": actor_kind, "binding_id": binding_id,
            "opened_at": self._stamp(), "closed_at": None, "lifecycle": "OPEN",
            "active_thread_id": None, "unread_cursor": None,
            "standing": ENTRY_STANDING,
        }, "console.open-session")

    def close_session(self, session_id: str) -> dict[str, Any]:
        """Close a session and pin its read position to the journal head it saw."""
        session = self._session(session_id)
        return self._emit("operator-session-lifecycle", session_id, session["operator_id"], {
            "session_id": session_id, "operator_id": session["operator_id"],
            "actor_kind": session["actor_kind"], "binding_id": session["binding_id"],
            "lifecycle": "CLOSED", "closed_at": self._stamp(),
            "unread_cursor": self.record.head(), "standing": ENTRY_STANDING,
        }, "console.close-session")

    def post(self, session_id: str, thread_id: str, body: bytes,
             mentions: Iterable[str] = (), claims: bool = False,
             proposal_id: str | None = None) -> dict[str, Any]:
        """Record one attributed turn in a thread.

        A HUMAN post and a MODEL post take this same transition and check the same
        capability; they differ in `actor_kind` and in the receipt's `interface_id`.
        A MODEL post that claims anything must already carry a Proposal. Without one
        the transition is refused rather than quietly downgraded.
        """
        # One verified replay serves all three reads below. Replaying per lookup
        # made a post cost O(journal) three times over and the verification budget
        # noticed before any user would have.
        entries = self.record.reconstruct()
        session = self._session(session_id, entries)
        operator_id = session["operator_id"]
        post_id = _identifier("post")
        if session["lifecycle"] != "OPEN":
            raise self._refuse(SessionClosed(f"session {session_id} is CLOSED"),
                               POST_OPERATION, post_id, operator_id)
        if self._thread(thread_id, entries)["lifecycle"] != "OPEN":
            raise self._refuse(ThreadArchived(f"thread {thread_id} is ARCHIVED"),
                               POST_OPERATION, post_id, operator_id)
        if session["actor_kind"] == "MODEL" and claims and proposal_id is None:
            raise self._refuse(
                ModelClaimWithoutProposal(
                    "a MODEL post that claims enters the kernel as a Proposal first"),
                POST_OPERATION, post_id, operator_id)
        grant = self._grant_id(operator_id, POST_CAPABILITY, thread_id,
                               POST_OPERATION, post_id, entries)
        digest = hashlib.sha256(body).hexdigest()
        (self.posts / digest).write_bytes(body)
        return self._emit("post", post_id, operator_id, {
            "post_id": post_id, "thread_id": thread_id, "actor_id": operator_id,
            "actor_kind": session["actor_kind"], "content_address": f"posts/{digest}",
            "content_digest": f"sha256:{digest}", "mentions": sorted(set(mentions)),
            "proposal_id": proposal_id, "posted_at": self._stamp(),
            "session_id": session_id, "binding_id": session["binding_id"],
            "standing": ENTRY_STANDING,
        }, POST_OPERATION, [grant])

    def body(self, content_address: str) -> bytes:
        """Read an immutable post payload by its address. A post is never rewritten."""
        return (self.root / content_address).read_bytes()

    # ---- journal reads the transitions above depend on ---------------------

    def _stamp(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self._clock())) + "Z"

    def _thread(self, thread_id: str,
                entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return reads.thread(self._entries(entries), thread_id)

    def _session(self, session_id: str,
                 entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return reads.session(self._entries(entries), session_id)

    def _entries(self, entries: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        """A verified replay, reusing the caller's when it already has one."""
        return entries if entries is not None else self.record.reconstruct()
