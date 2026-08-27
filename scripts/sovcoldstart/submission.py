"""Everything about the file a participant submits and the record its grading produces.

Split from `scoring.py` when that module crossed the line ceiling. The cut is the one the
code already had: `scoring` owns running probes and rendering a card, and this owns where a
submission comes from, who is allowed to have graded it, and what gets written down.

Both halves of that second responsibility were defeated by witnesses. The verdict file was
bound to its answers by basename and then not at all; the digest that binds them was
required by the record and never computed by the producer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from sovcoldstart import records

def _inside(path: Path) -> str | None:
    """A record cites files by repository-relative path, or it cites nothing anyone can find.

    An absolute path passed to `ROOT / rel` wins, so a digest recorded against one resolved
    on the producing host and was unresolvable everywhere else. A witness recorded a run
    citing a Windows temp directory.
    """
    try:
        return path.resolve().relative_to(records.ROOT).as_posix()
    except ValueError:
        return None


def _graded_by(args: argparse.Namespace, manual: list[dict[str, Any]]) -> dict[str, Any]:
    """Who graded the prose, digested. The digest was required and never computed here.

    `refusals` asks the record for `owner_verdicts_digest`, this built the block without it,
    and every owner-graded run raised `SELF_GRADED` out of `write` rather than recording.
    The one fixture proving an owner-graded record admissible hand-wrote a digest no code
    path produced, which is the defect class this contract exists to refuse, in the contract.
    """
    block: dict[str, Any] = {
        "owner_verdicts": None,
        "manual_asked": len(manual),
        "manual_graded": sum(1 for s in manual if s["verdict"] in ("RIGHT", "WRONG")),
    }
    if not args.owner_verdicts:
        return block
    inside = _inside(args.owner_verdicts)
    if inside is None:
        raise SystemExit(
            f"{args.owner_verdicts} is outside the repository; a run record cites files by "
            f"repository-relative path so another reader can resolve them"
        )
    block["owner_verdicts"] = inside
    block["owner_verdicts_digest"] = records.digest_of(args.owner_verdicts)
    return block


def load_verdicts(args: argparse.Namespace) -> dict[str, str]:
    """Owner verdicts on the manual questions, from a file the participant did not write.

    These used to be read out of the answers file. Since an unmeasured tier 0 question
    blocks ADMISSIBLE, that made self-certification the only route to a clean card: 41
    answers of `banana banana banana`, each carrying `owner_verdict: RIGHT`, scored tier 0
    at 100%. `AGENTS.md`, Evidence and standing: no seat settles its own output.

    The verdicts file binds to the answers it graded by digest, and a file that states no
    binding is refused rather than applied. Both were looser: the binding was optional, so
    omitting it skipped the check entirely, and when present it compared basenames, so any
    two files called `answers.json` graded each other. A witness found both.
    """
    if not args.owner_verdicts:
        return {}
    doc = json.loads(args.owner_verdicts.read_text(encoding="utf-8"))
    graded = doc.get("grades_answer_digest")
    if not graded:
        raise SystemExit(
            f"{args.owner_verdicts} states no grades_answer_digest, so nothing says which "
            f"answers it graded; refusing to apply it"
        )
    actual = records.digest_of(args.answers)
    if graded != actual:
        raise SystemExit(
            f"verdict file grades {graded}, and {args.answers} digests to {actual}; "
            f"refusing to apply it"
        )
    return {v["id"]: v["verdict"] for v in doc.get("verdicts", [])}

def keep(args: argparse.Namespace, results: list[dict[str, Any]], key: str, good: str,
         doc: dict[str, Any], mode: str, **extra: Any) -> None:
    """Write the run record, or say why the run was not worth recording.

    A card printed to a terminal is an anecdote. Two records a day apart are a measurement
    of drift, which is the only reading that tells anyone whether the orientation layer is
    getting better or worse.
    """
    if not args.record:
        return
    record = records.build(
        results, key, good, mode=mode, observed_at=args.at, corpus=args.corpus,
        questions=len(doc["questions"]),
        coverage={"fast": args.fast, "offline": args.offline,
                  "sections": sorted(args.section or [])},
        **extra,
    )
    try:
        written = records.write(record)
    except ValueError as refused:
        # A refused record is a result, not a crash. Printing a traceback here read as the
        # tool being broken, when what it was saying is that this run cannot be recorded.
        print(f"REFUSED to record this run: {refused}")
        raise SystemExit(1)
    print(f"recorded {written.relative_to(records.ROOT).as_posix()}")

