"""Observe the Console Service continuity path from outside the code that built it.

`services/console/tests/` establishes `BUILT`: it imports the service, drives the
Python API, and projects records through `contract.py`. That is the builder's own
path, and `AGENTS.md` holds that a build cannot witness itself.

This module takes the other path on purpose:

- the service is reached only as a subprocess through `cli.py`, so nothing here
  imports `soveraeign_console_service`;
- the declared record shape is read out of the schema files' own `properties`,
  never out of `contract.py`, so the projection under test is reconstructed here
  rather than borrowed from the code being observed;
- the post-to-receipt join is done by scanning the journal for a `COMMITTED`
  receipt naming the post's entry, not by asking the console who committed it.

Running this establishes an independent observation. It does not establish
`WITNESSED`, which is a standing another participant proposes and only Bdo
settles, and it says nothing about the four console surfaces that remain
boundary with no implementation (`services/console/KNOWN-GAPS.md`).
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_record_service import RecordService  # noqa: E402
from sovkernel import jsonschema  # noqa: E402

CONTRACTS = ROOT / "services" / "console" / "contracts"
BODY = "one identical body, posted twice"
OWNER_BINDING = "urn:soveraeign:interface:console-owner-cli-v1"
MODEL_BINDING = "urn:soveraeign:interface:console-model-cli-v1"
# Fields two posts of identical bytes are expected to differ in. Anything else that
# differs would mean the binding an operator reached through changed the record.
ATTRIBUTION = {"post_id", "entry_id", "entry_digest", "actor_id", "actor_kind",
               "session_id", "binding_id", "posted_at"}


class Observation:
    """What was looked at, and what it did. Never a verdict about standing."""

    def __init__(self) -> None:
        self.findings: list[tuple[bool, str, str]] = []

    def note(self, held: bool, claim: str, detail: str = "") -> None:
        self.findings.append((held, claim, detail))

    def report(self) -> int:
        width = max(len(claim) for _, claim, _ in self.findings)
        for held, claim, detail in self.findings:
            print(("PASS" if held else "FAIL") + "  " + claim.ljust(width) + "  " + detail)
        failed = [f for f in self.findings if not f[0]]
        print("\n" + str(len(self.findings) - len(failed)) + "/" + str(len(self.findings))
              + " independent observations held")
        print("Standing note: an observation independent of the builder. It proposes at most "
              "BUILT -> WITNESSED and settles nothing.")
        return 1 if failed else 0


def _environment() -> dict[str, str]:
    """The subprocess environment, with the three source roots the CLI needs."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([
        str(ROOT / "services" / "console" / "src"),
        str(ROOT / "services" / "record" / "src"),
        str(ROOT / "scripts"),
    ])
    return env


def console(store: Path, *args: str, expect: int = 0) -> dict[str, Any]:
    """Run one console command as a subprocess and return the JSON it printed."""
    proc = subprocess.run(
        [sys.executable, "-m", "soveraeign_console_service.cli", "--root", str(store), *args],
        capture_output=True, text=True, env=_environment(), cwd=str(ROOT), check=False)
    if proc.returncode != expect:
        raise SystemExit(f"console exited {proc.returncode} for {args}\n{proc.stdout}{proc.stderr}")
    return json.loads(proc.stdout)


def declared_shape(payload: dict[str, Any], schema_name: str,
                   extra: dict[str, Any] | None = None) -> list[str]:
    """Validate the emitted payload against the schema's own declared properties.

    The CLI prints a journal payload, which carries the entry fields a record does
    not. The schema closes its object against exactly that, so the record is the
    projection onto the schema's `properties` keys - reconstructed here rather than
    taken from the service's own projection module.
    """
    schema = json.loads((CONTRACTS / schema_name).read_text(encoding="utf-8"))
    source = dict(payload, **(extra or {}))
    instance = {field: source.get(field) for field in schema.get("properties", {})}
    return jsonschema.validate(instance, schema)


def committed_receipts(store: Path) -> dict[str, str]:
    """Map each committed record address to its receipt, read from the journal."""
    roots = sorted({path.parent for path in store.rglob("*")
                    if path.is_file() and path.suffix in {".db", ".sqlite3", ".ndjson", ".jsonl"}})
    if not roots:
        return {}
    journal = RecordService(roots[0])
    try:
        index: dict[str, str] = {}
        for entry in journal.reconstruct():
            if entry["kind"] != "RECEIPT" or entry["payload"]["outcome"] != "COMMITTED":
                continue
            for address in entry["payload"]["detail"].get("emitted_record_addresses", []):
                index[address] = entry["entry_id"]
        return index
    finally:
        journal.close()


def _authority(observed: Observation, store: Path) -> dict[str, Any]:
    """An operation refuses without a live grant, and admits with one."""
    refused = console(store, "open-channel", "--operator", "nobody", "--name", "general",
                      "--domain", "governance", expect=2)
    observed.note(refused.get("outcome") == "REFUSED", "an ungranted operator is refused",
                  str(refused.get("reason_code")))
    console(store, "grant", "--operator", "Bdo", "--capability", "open:channel",
            "--scope", "governance")
    # The session lifecycle and the reads are guarded as of 2026-08-25, so the walk
    # buys what it is about to spend. Bdo is this store's root issuer by virtue of
    # the grant above, which is the first one this journal ever carried.
    for operator in ("Bdo", "sov"):
        for capability in ("open:session", "read:session"):
            console(store, "grant", "--operator", operator,
                    "--capability", capability, "--scope", operator)
    console(store, "grant", "--operator", "Bdo", "--capability", "read:authority",
            "--scope", "node:local")
    channel = console(store, "open-channel", "--operator", "Bdo", "--name", "general",
                      "--domain", "governance")
    observed.note(not declared_shape(channel, "channel.schema.json"), "a channel validates",
                  "; ".join(declared_shape(channel, "channel.schema.json")))
    return channel


def _parity(observed: Observation, store: Path, thread: dict[str, Any]) -> dict[str, Any]:
    """A human turn and a model turn are one crossing through the same record."""
    human = console(store, "open-session", "--operator", "Bdo", "--actor-kind", "HUMAN",
                    "--binding", OWNER_BINDING)
    model = console(store, "open-session", "--operator", "sov", "--actor-kind", "MODEL",
                    "--binding", MODEL_BINDING)
    for label, session in (("human", human), ("model", model)):
        errors = declared_shape(session, "operator-session.schema.json")
        observed.note(not errors, "a " + label + " session validates", "; ".join(errors))

    posts = {}
    for label, session in (("human", human), ("model", model)):
        operator = "Bdo" if label == "human" else "sov"
        posts[label] = console(store, "post", "--operator", operator, "--session",
                               session["session_id"], "--thread", thread["thread_id"],
                               "--body", BODY)
    receipts = committed_receipts(store)
    observed.note(bool(receipts), "the journal reconstructs outside the console",
                  str(len(receipts)) + " committed addresses")
    for label, post in posts.items():
        errors = declared_shape(post, "post.schema.json",
                               {"receipt_id": receipts.get(post["entry_id"], "")})
        observed.note(not errors, "a " + label + " post validates", "; ".join(errors))
        observed.note(post["entry_id"] in receipts, "a " + label + " post has a committed receipt",
                      receipts.get(post["entry_id"], "ABSENT"))

    human_post, model_post = posts["human"], posts["model"]
    stray = {key for key in set(human_post) | set(model_post)
             if human_post.get(key) != model_post.get(key)} - ATTRIBUTION
    observed.note(not stray, "identical bodies differ only in attribution", "stray=" + str(sorted(stray)))
    observed.note(human_post.get("content_digest") == model_post.get("content_digest"),
                  "both actor kinds reach one content address",
                  str(human_post.get("content_digest"))[:24])
    return human


def _refusals(observed: Observation, store: Path, thread: dict[str, Any],
              human: dict[str, Any]) -> None:
    """A revoked grant stops admitting, without reaching back into what it admitted."""
    live = console(store, "grants", "--reader", "Bdo",
                   "--operator", "Bdo")["live_grants"]
    observed.note(bool(live), "live grants are readable", str(len(live)) + " live")
    posting = [grant["grant_id"] for grant in live if grant["capability"] == "post:message"]
    if not posting:
        observed.note(False, "a revoked grant refuses the next post", "no post grant found")
        return
    before = console(store, "read-thread", "--operator", "Bdo",
                     "--thread", thread["thread_id"])
    console(store, "revoke", "--grant", posting[0])
    after = console(store, "post", "--operator", "Bdo", "--session",
                    human["session_id"], "--thread", thread["thread_id"],
                    "--body", "after revocation", expect=2)
    observed.note(after.get("outcome") == "REFUSED", "a revoked grant refuses the next post",
                  str(after.get("reason_code")))
    still = console(store, "read-thread", "--operator", "Bdo",
                    "--thread", thread["thread_id"])
    observed.note(len(still["posts"]) == len(before["posts"]),
                  "revocation does not unmake committed posts",
                  str(len(still["posts"])) + " posts remain")


def _projection(observed: Observation, store: Path, thread: dict[str, Any]) -> None:
    """The read path says it is a projection and rebuilds to the same answer."""
    view = console(store, "read-thread", "--operator", "Bdo",
                   "--thread", thread["thread_id"])
    observed.note(view.get("authoritative") is False
                  and view.get("rebuilt_from") == "record-service-journal",
                  "the read path declares itself a projection", str(view.get("rebuilt_from")))
    observed.note(view == console(store, "read-thread", "--operator", "Bdo",
                                  "--thread", thread["thread_id"]),
                  "the projection is stable across rebuilds")
    context = console(store, "session-context", "--reader", "Bdo")
    observed.note(set(context) >= {"unseen_posts", "cursor", "omissions", "rebuilt_from"},
                  "session-context carries what landed while away",
                  ", ".join(sorted(context))[:90])


def observe() -> int:
    """Drive one full continuity walk through the CLI and grade what came back."""
    observed = Observation()
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = Path(tmp) / "console"
        channel = _authority(observed, store)
        console(store, "grant", "--operator", "Bdo", "--capability", "open:thread",
                "--scope", channel["channel_id"])
        thread = console(store, "open-thread", "--operator", "Bdo", "--channel",
                         channel["channel_id"], "--title", "independent observation")
        observed.note(not declared_shape(thread, "thread.schema.json"), "a thread validates",
                      "; ".join(declared_shape(thread, "thread.schema.json")))
        for operator in ("Bdo", "sov"):
            console(store, "grant", "--operator", operator, "--capability", "post:message",
                    "--scope", thread["thread_id"])
        console(store, "grant", "--operator", "Bdo", "--capability", "read:thread",
                "--scope", thread["thread_id"])
        human = _parity(observed, store, thread)
        model_claim = console(store, "post", "--operator", "sov", "--session",
                              _model_session(store), "--thread", thread["thread_id"],
                              "--body", "a model claim", "--claims", expect=2)
        observed.note(model_claim.get("outcome") == "REFUSED",
                      "a model claim without a proposal is refused",
                      str(model_claim.get("reason_code")))
        admitted = console(store, "post", "--operator", "Bdo", "--session",
                           human["session_id"], "--thread", thread["thread_id"],
                           "--body", "a human claim", "--claims")
        observed.note("post_id" in admitted, "the same claim from a human is admitted")
        _refusals(observed, store, thread, human)
        _projection(observed, store, thread)
    return observed.report()


def _model_session(store: Path) -> str:
    """Open a fresh MODEL session and return its id."""
    return console(store, "open-session", "--operator", "sov", "--actor-kind", "MODEL",
                   "--binding", MODEL_BINDING)["session_id"]


MAIN: Callable[[], int] = observe

if __name__ == "__main__":
    raise SystemExit(observe())
