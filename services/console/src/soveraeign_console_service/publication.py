"""The outward surface's authoritative half: what marks a thread readable outside.

`core.py` owns the transitions an operator drives inside the node. Publishing points
the other way, so its record shape and its guard live here rather than growing the
transition module: this is the only console concern whose effect is visible to people
who are not members of anything.

Nothing here writes. `ConsoleService.publish_thread` and
`ConsoleService.withdraw_publication` append what these functions build, so the guard
runs before the journal is touched rather than after.

`contracts/publication.schema.json` owns the shape; `contracts/public-projection.schema.json`
renders it. A projection never decides what is public - it reads what was recorded here.
"""

from __future__ import annotations

from typing import Any

VISIBILITY = "PUBLIC"
PUBLISHED = "PUBLISHED"
WITHDRAWN = "WITHDRAWN"


def foreign_thread(thread: dict[str, Any], node_id: str) -> str | None:
    """The reason this thread belongs to another node, or None when it is ours.

    Returned rather than raised so a caller names the operation it was refusing. The
    same fact refuses an archive and a publish for different reasons: one would close
    a peer's thread, the other would republish a peer's record under this node's name.
    """
    owner = thread.get("node_id")
    if owner == node_id:
        return None
    return f"belongs to {owner}; this console serves {node_id}"


def publication_payload(node_id: str, publication_id: str, thread_id: str,
                        published_by: str, published_at: str,
                        standing: str) -> dict[str, Any]:
    """The record marking one thread readable outside the node."""
    return {"node_id": node_id, "publication_id": publication_id, "thread_id": thread_id,
            "visibility": VISIBILITY, "lifecycle": PUBLISHED, "published_by": published_by,
            "published_at": published_at, "withdrawn_at": None, "standing": standing}


def withdrawal_payload(node_id: str, publication_id: str, thread_id: str,
                       withdrawn_at: str, standing: str) -> dict[str, Any]:
    """The record ending one publication.

    It carries no `published_by` and no `published_at`. Those belong to the mark this
    entry folds onto, and restating them here would let a withdrawal quietly rewrite
    who published a thread and when.
    """
    return {"node_id": node_id, "publication_id": publication_id, "thread_id": thread_id,
            "lifecycle": WITHDRAWN, "withdrawn_at": withdrawn_at, "standing": standing}
