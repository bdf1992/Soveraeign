"""Build a real console store from the repository's actual state.

Every record this writes goes through ConsoleService, so the store it produces
is one the service itself would accept - grants checked at each boundary, posts
appended as EVENT plus RECEIPT, nothing written behind the service's back.

Re-running drops the store and rebuilds it. The journal is append-preserving
within a run; a rebuild is a new journal, not a rewritten one.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_console_service import ConsoleService  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402

import content  # noqa: E402

STORE = ROOT / ".local" / "console"
NODE = "node:local"
HUMAN_BINDING = "binding:console-surface"
MODEL_BINDING = "binding:mcp-stdio"


def open_service(store: Path) -> ConsoleService:
    """Open the Console Service over its journal, creating the store if absent."""
    return ConsoleService(RecordService(store / "journal"), store, NODE)


def seed(store: Path = STORE) -> dict[str, object]:
    """Write channels, threads, sessions and posts. Returns a small summary."""
    if store.exists():
        shutil.rmtree(store)
    console = open_service(store)

    operators = {op[0]: op for op in content.OPERATORS}

    # Channel grants are scoped to a domain; thread grants to a channel; post
    # grants to a thread. The seeder grants exactly what the next call needs and
    # nothing wider, because a seed that over-grants teaches the wrong shape.
    channels: dict[str, str] = {}
    for domain, name, _purpose in content.CHANNELS:
        console.grant(content.CLAUDE, "open-channel", domain)
        channels[domain] = console.open_channel(content.CLAUDE, name, domain)["channel_id"]

    sessions: dict[str, str] = {}
    for operator_id, actor_kind, _display, _role in content.OPERATORS:
        binding = HUMAN_BINDING if actor_kind == "HUMAN" else MODEL_BINDING
        sessions[operator_id] = console.open_session(operator_id, actor_kind, binding)["session_id"]

    threads = 0
    posts = 0
    for domain, title, pinned, turns in content.THREADS:
        channel_id = channels[domain]
        console.grant(content.CLAUDE, "open-thread", channel_id)
        address, digest = _pin(pinned)
        thread_id = console.open_thread(content.CLAUDE, channel_id, title, address,
                                    digest)["thread_id"]
        threads += 1
        for actor_id, claims, body in turns:
            console.grant(actor_id, "post", thread_id)
            proposal = f"proposal_{thread_id[-8:]}" if claims else None
            console.post(sessions[actor_id], thread_id, body.encode("utf-8"),
                         mentions=(content.BDO,) if domain == "judgement" else (),
                         claims=claims, proposal_id=proposal)
            posts += 1

    # Bdo needs a post grant in every thread so the surface can actually answer,
    # and a live session to answer through.
    for thread_id in _thread_ids(console):
        console.grant(content.BDO, "post", thread_id)

    # One closed model session gives session_context a read cursor to work from;
    # without a closed session every post reads as unseen and the view says so.
    console.close_session(sessions[content.WITNESS])

    return {"store": str(store), "channels": len(channels), "threads": threads,
            "posts": posts, "operators": len(operators)}


def _pin(pinned: str | None) -> tuple[str | None, str | None]:
    """A pinned thread carries both an address and a digest, or neither.

    The repository path is the address. The digest here is the address's own
    sha256, not the file's: this seed pins where a thread points, and pinning a
    working-tree file's bytes would claim a fixity the working tree does not have.
    """
    if pinned is None:
        return None, None
    import hashlib
    return pinned, "sha256:" + hashlib.sha256(pinned.encode("utf-8")).hexdigest()


def _thread_ids(console: ConsoleService) -> list[str]:
    from soveraeign_console_service import Projection
    return sorted(Projection(console).thread)


if __name__ == "__main__":
    summary = seed()
    print(f"seeded {summary['channels']} channels, {summary['threads']} threads, "
          f"{summary['posts']} posts for {summary['operators']} operators")
    print(f"store: {summary['store']}")
