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
import re
import time
import uuid

from soveraeign_console_service import append, authority, permits, posts, publication
from soveraeign_console_service import reads, sessions
from soveraeign_console_service.authority import ENFORCED_AUTHORITY
from soveraeign_console_service.refusals import (
    ConsoleRefusal,
    ForeignNodeRecord,
    PinIncomplete,
    UnknownRecord,
)
from soveraeign_record_service import RecordService

# A console record enters at RECORDED and never above it. Admission, ratification
# and effectiveness are kernel transitions this service does not own.
ENTRY_STANDING = "RECORDED"
# The node identifier shape `contracts/node-identity.schema.json` declares. Checked
# here so a malformed node reaches the constructor rather than the journal.
# `fullmatch`, because `$` also matches before a trailing newline: `.match` admitted a
# second node whose name printed identically to the first. It reached no other node's
# grants - `authority.check` compares identifiers byte for byte - but a name nothing
# can tell apart from another is worth refusing.
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
        if not NODE_ID.fullmatch(node_id):
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
        """Record a live grant in the journal, where it outlives this process.

        The issuer must hold `grant:authority` over this node, except on a journal
        where this node's permits office has never been opened, in which case the
        issuer becomes its recorded root. `permits.py` owns both rules.
        """
        return permits.issue(self, operator_id, capability, scope, granted_by)

    def revoke(self, grant_id: str, revoked_by: str = "Bdo") -> dict[str, Any]:
        """Withdraw a grant by appending. It refuses the next operation, not past ones."""
        return permits.withdraw(self, grant_id, revoked_by)

    def grants(self, *, reader_id: str,
               operator_id: str | None = None) -> list[dict[str, Any]]:
        """Every grant that is live right now, optionally for one operator.

        Keyword-only because the reader and the operator read about are different
        participants, and a single positional argument silently meant the second one
        before the read was guarded.
        """
        return permits.listing(self, reader_id, operator_id)

    def authorize(self, operator_id: str, capability: str, scope: str, event: str,
                  subject: str, entries: list[dict[str, Any]] | None = None) -> str:
        """The live grant admitting this operation on this node, or a written refusal.

        The node comes from this service, never from the caller of the operation: a
        check that took the node as an argument would let a caller pick the namespace
        its own grant was matched in.
        """
        return authority.require(self.record, self._entries(entries), self.node_id,
                                 operator_id, capability, scope, event, subject)

    # ---- append path -------------------------------------------------------

    def _emit(self, kind: str, subject: str, actor: str, payload: dict[str, Any],
              event: str, grant_ids: Sequence[str] = ()) -> dict[str, Any]:
        return append.emit(self.record, kind, subject, actor, payload, event, grant_ids)

    def refusal(self, error: ConsoleRefusal, event: str, subject: str,
                actor: str) -> ConsoleRefusal:
        return append.refuse(self.record, error, event, subject, actor)

    # ---- transitions -------------------------------------------------------

    def open_channel(self, operator_id: str, name: str, domain: str) -> dict[str, Any]:
        """Open a named domain container for threads."""
        channel_id = _identifier("channel")
        grant = self.authorize(operator_id, ENFORCED_AUTHORITY["console.open-channel"],
                               domain, "console.open-channel", channel_id)
        return self._emit("channel", channel_id, operator_id, {
            "node_id": self.node_id,
            "channel_id": channel_id, "name": name, "domain": domain,
            "opened_by": operator_id, "opened_at": self.stamp(),
            "standing": ENTRY_STANDING,
        }, "console.open-channel", [grant])

    def open_thread(self, operator_id: str, channel_id: str, title: str,
                    pinned_address: str | None = None,
                    pinned_digest: str | None = None) -> dict[str, Any]:
        """Open a bounded conversation, optionally pinned to an exact record address."""
        thread_id = _identifier("thread")
        if (pinned_address is None) != (pinned_digest is None):
            raise self.refusal(
                PinIncomplete("a pinned thread carries both an address and its digest"),
                "console.open-thread", thread_id, operator_id)
        entries = self.record.reconstruct()
        # Authority first: the grant's scope is the channel id the caller supplied, so
        # nothing has to be read to check it, and an ungranted caller learns nothing
        # about which channels exist. The manifest declares `channel_exists` and this
        # took the id on trust, so a thread could open into another node's channel, or
        # into no channel at all.
        grant = self.authorize(operator_id, ENFORCED_AUTHORITY["console.open-thread"],
                               channel_id, "console.open-thread", thread_id, entries)
        self.channel(channel_id, entries, "console.open-thread", operator_id)
        return self._emit("thread", thread_id, operator_id, {
            "node_id": self.node_id,
            "thread_id": thread_id, "channel_id": channel_id, "title": title,
            "opened_by": operator_id, "opened_at": self.stamp(), "lifecycle": "OPEN",
            "pinned_address": pinned_address, "pinned_digest": pinned_digest,
            "standing": ENTRY_STANDING,
        }, "console.open-thread", [grant])

    def archive_thread(self, operator_id: str, thread_id: str) -> dict[str, Any]:
        """Archive a thread. Its posts stay readable; no new post may land in it."""
        entries = self.record.reconstruct()
        # The grant's scope is this thread's channel, which cannot be known without
        # reading the thread, so the read comes first and answers an unearned caller
        # the way a missing record does.
        thread = self.held_thread(thread_id, entries)
        channel_id = thread["channel_id"]
        grant = self.authorize(operator_id, ENFORCED_AUTHORITY["console.archive-thread"],
                               channel_id, "console.archive-thread", thread_id, entries)
        return self._emit("thread-lifecycle", thread_id, operator_id, {
            "node_id": self.node_id,
            "thread_id": thread_id, "channel_id": channel_id, "lifecycle": "ARCHIVED",
            "standing": ENTRY_STANDING,
        }, "console.archive-thread", [grant])

    def publish_thread(self, operator_id: str, thread_id: str) -> dict[str, Any]:
        """Mark a thread readable outside the node. `publication.py` owns it."""
        return publication.publish_thread(self, operator_id, thread_id,
                                          _identifier("publication"), ENTRY_STANDING)

    def withdraw_publication(self, operator_id: str, publication_id: str) -> dict[str, Any]:
        """Stop rendering a thread outwardly. `publication.py` owns it."""
        return publication.withdraw_publication(self, operator_id, publication_id,
                                                ENTRY_STANDING)

    def open_session(self, operator_id: str, actor_kind: str,
                     binding_id: str) -> dict[str, Any]:
        """Open one operator's continuity through a named binding. `sessions.py` owns it."""
        return sessions.open_session(self, operator_id, actor_kind, binding_id,
                                     _identifier("session"), ENTRY_STANDING)

    def close_session(self, operator_id: str, session_id: str) -> dict[str, Any]:
        """Close a session and pin its read position. `sessions.py` owns it.

        `operator_id` is who is closing it, which is not always whose session it is.
        """
        return sessions.close_session(self, operator_id, session_id, ENTRY_STANDING)

    def post(self, operator_id: str, session_id: str, thread_id: str, body: bytes,
             mentions: Iterable[str] = (), claims: bool = False,
             proposal_id: str | None = None) -> dict[str, Any]:
        """Record one attributed turn in a thread. `posts.py` owns it."""
        return posts.post(self, operator_id, session_id, thread_id, body,
                          _identifier("post"), ENTRY_STANDING, mentions, claims,
                          proposal_id)

    def body(self, content_address: str) -> bytes:
        """Read an immutable post payload by its address. A post is never rewritten."""
        return (self.root / content_address).read_bytes()

    # ---- journal reads the transitions above depend on ---------------------

    def stamp(self) -> str:
        """The service clock as an ISO-8601 UTC timestamp."""
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self._clock())) + "Z"

    def owned(self, record: dict[str, Any], subject: str, event: str,
              actor: str) -> dict[str, Any]:
        """The record, or a written `FOREIGN_NODE_RECORD` refusal naming why not.

        For a lookup that runs *after* this operation's authority check. The caller
        has shown a live grant over the subject, so telling it the record exists and
        is not this node's costs nothing it has not already earned.

        Binding a grant to the node that minted it stops a permit crossing between
        nodes; it does nothing about a node reading and writing another node's
        records under a permit of its own, and a node identifier is unbounded, so
        anyone refused one office simply opens another. This is the check that
        closes that.
        """
        foreign = reads.foreign(record, self.node_id)
        if foreign is not None:
            raise self.refusal(ForeignNodeRecord(f"{subject} {foreign}"), event,
                               subject, actor)
        return record

    def held_record(self, record: dict[str, Any], subject: str) -> dict[str, Any]:
        """The record, or `UnknownRecord` - the same answer a missing one gets.

        For a lookup that runs *before* this operation's authority check, either
        because the grant's scope is read off the record itself or because the grant
        is over something else. Two refusals told those callers apart: a record that
        does not exist answered `UNKNOWN_RECORD` and one belonging to another node
        answered `FOREIGN_NODE_RECORD`, so anyone holding nothing could sweep ids and
        learn which existed and whose they were. Collapsed 2026-08-25 because the
        distinction is not earned until a grant has been shown.
        """
        if reads.foreign(record, self.node_id) is not None:
            raise UnknownRecord(subject)
        return record

    def channel(self, channel_id: str, entries: list[dict[str, Any]] | None,
                event: str, actor: str) -> dict[str, Any]:
        """A channel, after the caller has shown its grant over it."""
        return self.owned(reads.channel(self._entries(entries), channel_id),
                          channel_id, event, actor)

    def thread(self, thread_id: str, entries: list[dict[str, Any]] | None,
               event: str, actor: str) -> dict[str, Any]:
        """A thread, after the caller has shown its grant over it."""
        return self.owned(reads.thread(self._entries(entries), thread_id),
                          thread_id, event, actor)

    def held_thread(self, thread_id: str,
                    entries: list[dict[str, Any]] | None) -> dict[str, Any]:
        """A thread, for a caller that has shown nothing yet."""
        return self.held_record(reads.thread(self._entries(entries), thread_id),
                                thread_id)

    def held_session(self, session_id: str,
                     entries: list[dict[str, Any]] | None) -> dict[str, Any]:
        """A session, for a caller that has shown nothing yet."""
        return self.held_record(reads.session(self._entries(entries), session_id),
                                session_id)

    def _entries(self, entries: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        """A verified replay, reusing the caller's when it already has one."""
        return entries if entries is not None else self.record.reconstruct()
