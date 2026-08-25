#!/usr/bin/env python3
"""Execute ``invoke_model`` against the local runtime and emit the invocation record.

Commands:
  ``run BINDING_ID``            one invocation under one declared binding
  ``parity BINDING_A BINDING_B``  the same operation under two materially different models

Exit codes: 0 accepted, 2 refused with a reason code, 1 the input could not be read.
An accepted result is not a grant, a witness, or a ratification. It says the run happened,
the record accounts for it, and the adapter's own checks admit that record.

This command consumes resources on owner-owned hardware (effect class
``RESOURCE_CONSUMPTION``). It writes no authoritative state: the record goes to stdout,
or to a path the caller names, and nothing else in the repository moves.

``parity`` refuses unless both runs reached ``COMMITTED``. Two models that were both cut
off mid-thought agree about nothing, and a portability claim resting on that would be
reporting the harness rather than the models.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import argparse
import json
import sys

ADAPTER = Path(__file__).resolve().parent
sys.path.insert(0, str(ADAPTER))
sys.path.insert(0, str(ADAPTER.parents[1] / "scripts"))

from adapter import Refusal, check_parity  # noqa: E402
from invoke import DEFAULT_ENDPOINT, HttpTransport, invoke  # noqa: E402

DEFAULT_CAPABILITY = "completion"


def _identity(operation_id: str, binding_id: str, prompt: str) -> str:
    """Address an invocation by what it is, so the same run names itself the same way."""
    seed = "\0".join((operation_id, binding_id, prompt)).encode("utf-8")
    return f"urn:soveraeign:invocation:{sha256(seed).hexdigest()[:24]}"


def _prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if args.prompt is None:
        raise SystemExit("FAIL: give --prompt or --prompt-file")
    return args.prompt


def _transport(args: argparse.Namespace) -> HttpTransport:
    return HttpTransport(args.endpoint, timeout=args.timeout)


def _options(args: argparse.Namespace) -> dict | None:
    return {"num_predict": args.num_predict} if args.num_predict else None


def _emit(payload: object, out: str | None) -> None:
    text = json.dumps(payload, indent=2) + "\n"
    if out:
        target = Path(out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {target.as_posix()}")
    else:
        print(text, end="")


def _refused(subject: str, refusal: Refusal) -> int:
    print(json.dumps({"outcome": "REFUSED", "subject": subject,
                      "reason_code": refusal.reason_code,
                      "detail": refusal.detail}, indent=2))
    return 2


def _one(args: argparse.Namespace, binding_id: str, prompt: str) -> tuple[dict, str]:
    return invoke(
        binding_id,
        prompt,
        operation_id=args.operation,
        actor_id=f"urn:soveraeign:actor:model:ollama:{binding_id.rsplit(':', 1)[-1]}",
        required_authority=args.authority,
        invocation_id=_identity(args.operation, binding_id, prompt),
        capability=args.capability,
        transport=_transport(args),
        options=_options(args),
    )


def command_run(args: argparse.Namespace) -> int:
    """Run one model under one binding and print the record it produced."""
    prompt = _prompt(args)
    try:
        record, text = _one(args, args.binding_id, prompt)
    except Refusal as refusal:
        return _refused(args.binding_id, refusal)
    _emit(record, args.out)
    if args.show_output:
        print("--- output ---")
        print(text)
    return 0


def command_parity(args: argparse.Namespace) -> int:
    """Run one operation under two bindings and check the pair for portability."""
    prompt = _prompt(args)
    records, outputs = [], []
    for binding_id in (args.binding_a, args.binding_b):
        try:
            record, text = _one(args, binding_id, prompt)
        except Refusal as refusal:
            return _refused(binding_id, refusal)
        records.append(record)
        outputs.append(text)

    incomplete = [r["invocation_id"] for r in records if r["outcome"] != "COMMITTED"]
    if incomplete:
        return _refused(
            "parity",
            Refusal("PROVENANCE_INCOMPLETE",
                    f"parity needs two completed runs; {', '.join(incomplete)} did not "
                    f"reach COMMITTED"))
    try:
        result = check_parity(records[0], records[1])
    except Refusal as refusal:
        return _refused("parity", refusal)

    _emit({"parity": result, "invocations": records}, args.out)
    if args.show_output:
        for record, text in zip(records, outputs):
            print(f"--- {record['executed']['model_id']} ---")
            print(text)
    return 0


def _shared(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompt", help="the input to project and send")
    parser.add_argument("--prompt-file", help="read the input from a UTF-8 file")
    parser.add_argument("--operation", required=True, help="the operation this run serves")
    parser.add_argument("--authority", required=True,
                        help="the grant this run is claimed under; it is recorded, not checked")
    parser.add_argument("--capability", default=DEFAULT_CAPABILITY,
                        help=f"requested capability (default {DEFAULT_CAPABILITY})")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                        help=f"runtime endpoint (default {DEFAULT_ENDPOINT})")
    parser.add_argument("--timeout", type=float, default=300.0, help="seconds to wait")
    parser.add_argument("--num-predict", type=int,
                        help="cap the model's output tokens; a cap it hits is UNRESOLVED")
    parser.add_argument("--out", help="write the record to this path instead of stdout")
    parser.add_argument("--show-output", action="store_true",
                        help="print the model's text after the record")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="one invocation under one binding")
    run.add_argument("binding_id")
    _shared(run)
    run.set_defaults(handler=command_run)

    parity = sub.add_parser("parity", help="one operation under two bindings")
    parity.add_argument("binding_a")
    parity.add_argument("binding_b")
    _shared(parity)
    parity.set_defaults(handler=command_parity)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
