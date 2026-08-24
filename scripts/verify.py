#!/usr/bin/env python3
"""Run every repository-owned structural, oracle, and reference check.

Each check declares how it avoids relying on the thing it checks, and the run
emits one `Observation` per check against `contracts/observation.schema.json`.
Emitting records rather than prose is the point: a claim about what verification
found can then be checked against a record instead of trusted as a paragraph.

An observation settles nothing. `AGENTS.md`: a test may establish `BUILT`; it
may never claim `WITNESSED` or `RATIFIED`.

Checks are independent and run concurrently. Output is buffered and printed in
declared order so a parallel run reads exactly like a serial one.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import NamedTuple
import argparse
import json
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".venv", "__pycache__", ".local"}
BUDGET_SECONDS = 3.0
# Starting every repository check at once became slower as the suite grew: the
# hosted runner spent its budget context-switching between 20+ Python processes.
# Keep enough independent work in flight to hide startup/I/O without allowing
# process count itself to become the critical path.
MAX_CHECK_WORKERS = 8


class Check(NamedTuple):
    name: str
    command: list[str]
    cwd: Path
    relation: str
    observes: tuple[str, ...]


CHECKS = (
    Check("repository hygiene", [sys.executable, "scripts/lint.py"], ROOT,
          "reads repository bytes directly with read_bytes, never a build report, and never "
          "Path.read_text whose newline translation would hide the defect it looks for",
          (".gitattributes", "scripts/lint.py")),
    Check("bootstrap and locked evidence", [sys.executable, "scripts/verify_bootstrap.py"], ROOT,
          "re-digests locked evidence from disk rather than trusting a recorded digest",
          ("scripts/verify_bootstrap.py",)),
    Check("signpost reconciliation", [sys.executable, "scripts/sov_next.py", "--strict"], ROOT,
          "re-reads STATUS.yaml, ROADMAP.md and the epic projection at the moment of the "
          "check; it does not consult any prior reconciliation",
          ("ROADMAP.md", "STATUS.yaml", ".claude/epic/tree.json")),
    Check("conformance oracle controls", [sys.executable, "conformance/run.py"], ROOT,
          "the oracle derives every defect from observation records and never reads a "
          "participant verdict field, and never imports participant implementation code",
          ("conformance/oracle-controls.json", "conformance/run.py")),
    Check("conformance oracle tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "conformance/tests", "-v"], ROOT,
          "tests the oracle from outside itself, including cases proving it refuses reports "
          "it cannot read",
          ("conformance/tests",)),
    Check("kernel transition contract", [sys.executable, "scripts/sov_kernel.py", "selfcheck"],
          ROOT,
          "judges a declared corpus of positive and defeating requests against the "
          "authored table; it reads no participant verdict and asks the table nothing "
          "about whether it is correct, only what it admits",
          ("contracts/kernel-transitions.json",
           "conformance/fixtures/kernel/transition-cases.json")),
    Check("kernel contract against SPEC.md", [sys.executable, "scripts/sov_kernel.py", "drift"],
          ROOT,
          "re-reads SPEC.md bytes and derives the transition set and refusal codes from "
          "the governing document rather than trusting the authored table it is checking",
          ("SPEC.md", "contracts/kernel-transitions.json")),
    Check("kernel participant parity", [sys.executable, "scripts/sov_kernel.py", "parity"],
          ROOT,
          "compares each participant's declared refusal vocabulary against the kernel "
          "contract, so a participant cannot vouch for its own correspondence",
          ("contracts/kernel-parity.json", "contracts/kernel-transitions.json")),
    Check("service manifest contract", [sys.executable, "scripts/sov_service.py", "check"],
          ROOT,
          "derives the refusal vocabulary and transition ids from the kernel table and the "
          "requirement ids from PRD.md at check time, and rebuilds each logical endpoint from "
          "the manifest's own service and operation id rather than trusting the address it "
          "declares",
          ("contracts/service-manifest.schema.json",
           "contracts/fixtures/service-manifest.fixtures.json")),
    Check("specification traceability", [sys.executable, "scripts/sov_spec.py", "trace"], ROOT,
          "walks from SPEC.md requirements to the evidence records that claim them and "
          "refuses a standing whose predecessor standing is unreached",
          ("SPEC.md", "PRD.md")),
    Check("semantic cold-start task", [sys.executable, "scripts/sov_witness.py", "semantic"],
          ROOT,
          "judges the custody round trip by digests the witness computes itself rather than "
          "by any value the participant reported",
          ("conformance/founding-scenarios/010-semantic-custody-round-trip.yaml",)),
    Check("participant against its baseline", [sys.executable, "scripts/sov_baseline.py"], ROOT,
          "runs the participant in a separate process and grades it through the frozen "
          "oracle, which never imports participant code; the participant does not report its "
          "own verdict",
          ("services/asset/conformance/BASELINE.md", "conformance/scenarios.json")),
    Check("ticket contract corpora", [sys.executable, "scripts/sov_ticket.py", "selfcheck"],
          ROOT,
          "reads checked-in transition, metadata, and issue-body corpora and never contacts the "
          "coordination surface it describes; the issue-body cases start from bytes a person could "
          "paste into GitHub, so a shape the schema admits but no ticket body can express fails here",
          ("contracts/ticket-transitions.json", "conformance/fixtures/tickets/body-cases.json")),
    Check("acceptance routing", [sys.executable, "scripts/sov_docket.py", "check"], ROOT,
          "reads the decision records and the two declared contracts and proves the crosswalk "
          "is total, no routing names a record that does not exist, and every claim that "
          "STATUS.yaml already answers a record is true of the file; it grades no decision as "
          "right and settles none of them",
          ("contracts/decision-standing.json", "contracts/acceptance-routing.json",
           "decisions", "STATUS.yaml")),
    Check("node registry", [sys.executable, "scripts/sov_node.py", "validate"], ROOT,
          "reads the checked-in registry and the seat topology and grades one against the "
          "other; it contacts no peer and opens no socket, so the check cannot pass or fail "
          "because of what another node happened to be doing",
          ("contracts/fixtures/node-registry.reference.json",
           "contracts/node-identity.schema.json")),
    Check("Sov context profile",
          [sys.executable, "-m", "unittest", "discover", "-s", "bindings/sov/tests", "-v"], ROOT,
          "invokes the profile checker over declared fixtures, including one defeating "
          "declaration, rather than asking the profile whether it is valid",
          ("bindings/sov",)),
    Check("local model adapter",
          [sys.executable, "-m", "unittest", "discover", "-s", "adapters/ollama/tests", "-v"],
          ROOT,
          "grades declared bindings and invocation records against a recorded runtime "
          "inventory rather than a live daemon, so the result cannot depend on whether a "
          "model server happens to be running on the checking machine",
          ("adapters/ollama", "contracts/model-binding.schema.json")),
    Check("Record Service reference tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "services" / "record",
          "the participant's own tests; these establish BUILT evidence about local mechanics "
          "and are explicitly NOT independent of the code they exercise",
          ("services/record/tests",)),
    Check("Console Service reference tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "services" / "console",
          "the participant's own tests; these establish BUILT evidence about local mechanics "
          "and are explicitly NOT independent of the code they exercise. The contract-shape "
          "cases are the exception worth naming: they validate the records the service emits "
          "against the schema files in services/console/contracts/, which were written before "
          "the implementation existed and are not edited to accommodate it",
          ("services/console/tests", "services/console/contracts")),
    Check("Asset Service reference tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "services" / "asset",
          "the participant's own tests; these establish BUILT evidence about local mechanics "
          "and are explicitly NOT independent of the code they exercise",
          ("services/asset/tests",)),
    Check("operation surface page",
          [sys.executable, "scripts/sov_surface.py", "check"], ROOT,
          "rebuilds the page from the capability map, the service manifests and the gateway "
          "manifest at the moment of the check and compares bytes, so a page edited by hand "
          "or left behind by a manifest change fails rather than misinforming a reader",
          ("docs/surface.html", "contracts/fixtures/capability-map.reference.json",
           "bindings/mcp/manifest.json")),
    Check("MCP gateway binding",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "bindings" / "mcp",
          "drives the gateway through its declared JSON-RPC surface rather than calling the "
          "services behind it, and reads its evidence back out of the Record Service journal "
          "instead of trusting the gateway's return value",
          ("bindings/mcp", "bindings/mcp/manifest.json")),
    Check("repository tooling tests", [sys.executable, "scripts/run_tooling_tests.py"], ROOT,
          "the harness's own tests; independent of the repository content they check, but "
          "not of the harness itself; the runner partitions the complete discovered module "
          "population and fails if any shard fails",
          ("scripts/tests", "scripts/run_tooling_tests.py")),
)


def digest(address: str) -> str:
    """sha256 of a file, or of a sorted manifest of the files beneath a directory."""
    target = ROOT / address
    if target.is_file():
        return "sha256:" + sha256(target.read_bytes()).hexdigest()
    manifest = sha256()
    for path in sorted(target.rglob("*")) if target.is_dir() else []:
        if not path.is_file() or SKIP_PARTS & set(path.parts):
            continue
        manifest.update(path.relative_to(target).as_posix().encode("utf-8"))
        manifest.update(b"\0")
        manifest.update(sha256(path.read_bytes()).hexdigest().encode("ascii"))
        manifest.update(b"\n")
    return "sha256:" + manifest.hexdigest()


def observe(check: Check, run_id: str, exit_code: int, elapsed: float, when: str) -> dict:
    """One Observation of one check, per contracts/observation.schema.json."""
    addresses = [address for address in check.observes if (ROOT / address).exists()]
    identity = sha256(f"{run_id}\0{check.name}".encode("utf-8")).hexdigest()[:32]
    return {
        "observation_id": f"observation_{identity}",
        "run_id": run_id,
        "observer_id": f"scripts/verify.py@{digest('scripts/verify.py').split(':', 1)[1][:16]}",
        "observer_relation": check.relation,
        "observed_state_addresses": addresses,
        "observed_state_digests": [digest(address) for address in addresses],
        "predicate_results": {
            "exit_code": exit_code,
            "outcome": "PASS" if exit_code == 0 else "FAIL",
            "elapsed_seconds": round(elapsed, 3),
        },
        "observed_at": when,
        "subject": check.name,
    }


def run_check(check: Check) -> tuple[Check, int, float, str]:
    started = time.perf_counter()
    result = subprocess.run(check.command, cwd=check.cwd, check=False,
                            capture_output=True, text=True)
    return check, result.returncode, time.perf_counter() - started, result.stdout + result.stderr


def main(argv: list[str] | None = None, run_id: str | None = None,
         now: str | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--observe", type=Path, metavar="PATH",
                        help="write the run's Observation records to PATH as JSON")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="print the Observation records instead of the human report")
    args = parser.parse_args(argv)

    run_id = run_id or f"run_{uuid.uuid4().hex}"
    when = now or datetime.now(timezone.utc).isoformat(timespec="seconds")

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=min(MAX_CHECK_WORKERS, len(CHECKS))) as pool:
        results = list(pool.map(run_check, CHECKS))
    wall = time.perf_counter() - started

    observations = [observe(check, run_id, code, elapsed, when)
                    for check, code, elapsed, _ in results]
    work = sum(elapsed for _, _, elapsed, _ in results)
    failed = [check.name for check, code, _, _ in results if code]

    if args.observe:
        args.observe.parent.mkdir(parents=True, exist_ok=True)
        args.observe.write_bytes(
            (json.dumps(observations, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    if args.as_json:
        print(json.dumps(observations, indent=2, sort_keys=True))
        return 1 if failed else 0

    for check, _, elapsed, output in results:
        print(f"\n== {check.name} ==", flush=True)
        print(output.rstrip("\n"), flush=True)
        print(f"TIME: {check.name}: {elapsed:.3f}s", flush=True)

    if wall > BUDGET_SECONDS:
        failed.append(f"verification budget ({wall:.3f}s > {BUDGET_SECONDS:.3f}s)")
    if failed:
        print(f"\nFAIL: {', '.join(failed)}")
        return 1
    print(f"\nPASS: {len(CHECKS)} checks in {wall:.3f}s wall, {work:.3f}s of work")
    print("Standing note: self-tests establish BUILT evidence only; no independent witness "
          "or owner ratification is implied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
