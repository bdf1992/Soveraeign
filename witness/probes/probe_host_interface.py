"""Independent probe of the Host Service's governed read-health vertical.

Witness-owned. It imports neither `soveraeign_host_service` nor
`local_host_adapter`. It reaches the service only as a subprocess through the
two declared command surfaces: `scripts/sov_interface.py`, which projects and
dispatches the Node Interface, and the Console Service CLI, which is the only
declared surface that records a live grant.

The claims under attack are the ones `services/host/CHARTER.md` makes: that
every call needs a live grant for its exact capability and scope, that every
mutating operation is declared but unreachable, that the boundary reported is
the process execution host and not an assumed machine, and that the host name
is not exposed. Run:

    python witness/probes/probe_host_interface.py

It writes a JSON report to stdout and exits 0 whether or not the subject
survives.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
INTERFACE = REPO / "scripts" / "sov_interface.py"
CONSOLE_SRC = REPO / "services" / "console" / "src"
RECORD_SRC = REPO / "services" / "record" / "src"
MUTATING = ("host.restart", "host.power-off", "host.suspend", "host.request-restart",
            "host.apply-driver-update", "host.install-utility", "host.remove-utility")


def run(argv: list[str], env_extra: dict[str, str] | None = None) -> tuple[int, str, Any]:
    """Run a declared command surface and return (exit code, raw text, parsed)."""
    env = dict(os.environ)
    env.update(env_extra or {})
    done = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=str(REPO),
                          timeout=300)
    raw = done.stdout + done.stderr
    try:
        return done.returncode, raw, json.loads(done.stdout)
    except json.JSONDecodeError:
        return done.returncode, raw, None


def interface(*argv: str) -> tuple[int, str, Any]:
    """Drive scripts/sov_interface.py."""
    return run([sys.executable, str(INTERFACE), *argv])


def console(root: Path, *argv: str) -> tuple[int, str, Any]:
    """Drive the Console Service CLI, the declared surface that records grants."""
    return run([sys.executable, "-m", "soveraeign_console_service.cli",
                "--root", str(root), *argv],
               {"PYTHONPATH": os.pathsep.join([str(CONSOLE_SRC), str(RECORD_SRC)])})


def check_projection_reads_the_same_under_both_bindings() -> dict[str, Any]:
    """RED: does the Human and Model projection of the operation actually agree?

    The Model binding answers JSON and the Human binding answers a rendering, so
    the comparison is on the operation digest each one carries, not on bytes.
    """
    model_code, _, model = interface("show", "host.read-health", "--binding", "MODEL")
    if model_code != 0 or model is None:
        return {"held": False, "why": f"show refused under MODEL at exit {model_code}"}
    human_code, human_raw, _ = interface("show", "host.read-health", "--binding", "HUMAN")
    if human_code != 0:
        return {"held": False, "why": f"show refused under HUMAN at exit {human_code}"}
    digest = model["record_digest"]
    agrees = any(digest.startswith(token.strip("[]")) or token.strip("[]") == digest[:12]
                 for token in human_raw.split() if token.startswith("["))
    return {"held": bool(agrees),
            "record_digest": digest,
            "human_rendering_carries_the_digest": agrees,
            "human_reports_observed": "observed=no" in human_raw,
            "required_authority": model["required_authority"],
            "effect_class": model["effect_class"],
            "standing": model["standing"],
            "facts": model["facts"],
            "observation_ids": model["observation_ids"],
            "attack": "project the operation under both bindings and compare the "
                      "operation digest each one carries"}


def check_no_grant_is_refused(work: Path) -> dict[str, Any]:
    """RED: call the built operation with no live grant at all."""
    state = work / "no-grant"
    code, raw, result = interface("invoke", "host.read-health", "--actor", "operator",
                                  "--scope", "host:local", "--binding", "MODEL",
                                  "--state-root", str(state))
    detail = {}
    if isinstance(result, dict):
        detail = result.get("payload", {}).get("detail", {})
    return {"held": detail.get("reason_code") == "AUTHORITY_REFUSED",
            "exit_code": code, "reason_code": detail.get("reason_code"),
            "stage": detail.get("stage"), "failure_class": detail.get("failure_class"),
            "refusal_was_journaled": isinstance(result, dict) and result.get("kind") == "RECEIPT",
            "attack": "invoke the only built operation with no grant recorded anywhere"}


def check_wrong_scope_is_refused(work: Path) -> dict[str, Any]:
    """RED: ask for a scope the charter says is rechecked on every dispatch.

    Read this one narrowly. With no live grant reachable from here, a foreign
    scope and a correct scope both refuse, so this shows that no scope slips
    through - not that scope is the reason any given one was refused. Isolating
    scope needs a granted call, which the grant check below shows is not
    reachable through any declared surface.
    """
    outcomes = {}
    for scope in ("host:someone-elses-machine", "*", ""):
        state = work / f"scope-{abs(hash(scope))}"
        code, _, result = interface("invoke", "host.read-health", "--actor", "operator",
                                    "--scope", scope or "empty", "--binding", "MODEL",
                                    "--state-root", str(state))
        detail = result.get("payload", {}).get("detail", {}) if isinstance(result, dict) else {}
        outcomes[scope or "empty"] = {"exit_code": code,
                                      "reason_code": detail.get("reason_code")}
    return {"held": all(o["reason_code"] == "AUTHORITY_REFUSED" for o in outcomes.values()),
            "outcomes": outcomes,
            "isolates_scope_as_the_reason": False,
            "attack": "invoke with a foreign scope, a wildcard scope, and an empty scope"}


def check_mutating_operations_unreachable(work: Path) -> dict[str, Any]:
    """RED: try to reach every declared mutating host operation."""
    outcomes = {}
    for operation in MUTATING:
        state = work / f"mutate-{operation.replace('.', '-')}"
        code, raw, result = interface("invoke", operation, "--actor", "operator",
                                      "--scope", "host:local", "--binding", "MODEL",
                                      "--state-root", str(state))
        reason = None
        if isinstance(result, dict):
            reason = result.get("payload", {}).get("detail", {}).get("reason_code")
        if reason is None and "REFUSED" in raw:
            reason = raw.strip().split()[1].rstrip(":") if len(raw.split()) > 1 else raw.strip()
        outcomes[operation] = {"exit_code": code, "reason": reason,
                               "committed": "COMMITTED" in raw}
    return {"held": all(not o["committed"] for o in outcomes.values()),
            "outcomes": outcomes,
            "attack": "invoke every declared mutating host operation through the interface"}


def check_grant_through_the_declared_console_surface(work: Path) -> dict[str, Any]:
    """RED: issue the grant the way the system declares, then use it.

    The Console CLI is the only declared surface that records a live grant. The
    Node Interface reads authority out of the record journal under its own state
    root. This check asks whether the two can be pointed at one store using only
    declared arguments - that is, whether an outside observer can ever reach the
    built operation's success path without importing the implementation.
    """
    attempts = {}
    for label, console_root_of in (
            ("console-root-is-the-state-root", lambda s: s),
            ("console-root-is-state-root-console", lambda s: s / "console"),
            ("console-root-is-state-root-record", lambda s: s / "record")):
        state = work / f"grant-{label}"
        state.mkdir(parents=True, exist_ok=True)
        console_root = console_root_of(state)
        grant_code, grant_raw, grant = console(console_root, "grant", "--operator", "operator",
                                               "--capability", "read:host-health",
                                               "--scope", "host:local")
        journal_files = sorted(str(p.relative_to(state)) for p in state.rglob("*")
                               if p.is_file())
        code, _, result = interface("invoke", "host.read-health", "--actor", "operator",
                                    "--scope", "host:local", "--binding", "MODEL",
                                    "--state-root", str(state))
        detail = result.get("payload", {}).get("detail", {}) if isinstance(result, dict) else {}
        outcome = result.get("payload", {}).get("outcome") if isinstance(result, dict) else None
        attempts[label] = {
            "console_root": str(console_root.relative_to(state)) or ".",
            "grant_exit_code": grant_code,
            "grant_recorded": isinstance(grant, dict) and grant_code == 0,
            "files_under_state_root": journal_files,
            "invoke_outcome": outcome,
            "invoke_reason_code": detail.get("reason_code"),
            "reached_the_success_path": outcome == "COMMITTED",
        }
    reached = any(a["reached_the_success_path"] for a in attempts.values())
    return {"reachable_through_declared_surfaces": reached, "attempts": attempts,
            "attack": "record the grant through the Console CLI at every state-root "
                      "placement the declared arguments allow, then invoke"}


def check_prove_vertical() -> dict[str, Any]:
    """RED: what does the interface's own proof actually exercise?"""
    code, raw, proof = interface("prove")
    if code != 0 or proof is None:
        return {"held": False, "why": f"prove refused at exit {code}"}
    reads = proof.get("host_reads", {})
    adapters = {binding: read.get("adapter_id") for binding, read in reads.items()}
    real_adapter = all("proof" not in str(a).lower() for a in adapters.values())
    return {"held": bool(reads) and proof.get("same_host_semantics") is True,
            "bindings_exercised": sorted(reads),
            "adapter_ids": adapters,
            "exercises_the_real_local_adapter": real_adapter,
            "boundary": {b: r.get("boundary") for b, r in reads.items()},
            "terminal_outcome": {b: r.get("terminal_outcome") for b, r in reads.items()},
            "standing_effect": {b: r.get("standing_effect") for b, r in reads.items()},
            "proof_self_declared_standing": proof.get("standing"),
            "attack": "run the interface's own parity proof and read which adapter it used"}


def check_host_name_not_disclosed(work: Path) -> dict[str, Any]:
    """RED: does this machine's name leak through any declared surface?

    The charter says the operation does not expose the host name. The check
    scans every byte the declared surfaces printed for the real node name, the
    real user name, and the repository's absolute path.
    """
    secrets = {"node_name": platform.node(), "user_name": os.environ.get("USERNAME") or "",
               "home": os.environ.get("USERPROFILE") or ""}
    corpus = []
    _, raw, _ = interface("show", "host.read-health", "--binding", "MODEL")
    corpus.append(("show", raw))
    _, raw, _ = interface("prove")
    corpus.append(("prove", raw))
    state = work / "disclose"
    _, raw, _ = interface("invoke", "host.read-health", "--actor", "operator",
                          "--scope", "host:local", "--binding", "MODEL",
                          "--state-root", str(state))
    corpus.append(("invoke-refused", raw))
    leaks = {}
    for name, value in secrets.items():
        if not value or len(value) < 3:
            continue
        hits = [surface for surface, text in corpus if value.lower() in text.lower()]
        if hits:
            leaks[name] = {"value_length": len(value), "surfaces": hits}
    return {"held": not leaks, "leaks": leaks,
            "secrets_searched_for": sorted(k for k, v in secrets.items() if v and len(v) >= 3),
            "surfaces_scanned": [name for name, _ in corpus],
            "attack": "scan every declared surface's output for this machine's node "
                      "name, user name, and home path"}


def check_refusal_exit_codes() -> dict[str, Any]:
    """RED: does a refusal on this surface look like a success to a caller?"""
    work = Path(tempfile.mkdtemp(prefix="witness-host-exit-"))
    code_unreachable, _, _ = interface("invoke", "host.power-off", "--actor", "operator",
                                       "--scope", "host:local", "--binding", "MODEL",
                                       "--state-root", str(work / "a"))
    code_refused, _, _ = interface("invoke", "host.read-health", "--actor", "operator",
                                   "--scope", "host:local", "--binding", "MODEL",
                                   "--state-root", str(work / "b"))
    shutil.rmtree(work, ignore_errors=True)
    return {"held": code_unreachable != 0 and code_refused != 0,
            "power_off_unreachable_exit_code": code_unreachable,
            "read_health_authority_refused_exit_code": code_refused,
            "note": "the Record Service CLI answers a refusal with exit 2; a caller "
                    "that reads exit status rather than parsing stdout learns nothing "
                    "here if these are 0",
            "attack": "read the process exit status of two different refusals"}


def main() -> int:
    """Run every check and report what each returned."""
    work = Path(tempfile.mkdtemp(prefix="witness-host-"))
    report: dict[str, Any] = {
        "probe": "witness/probes/probe_host_interface.py",
        "subject": "services/host + adapters/host",
        "reached_through": "scripts/sov_interface.py and the Console Service CLI, "
                           "both as subprocesses",
        "checks": {},
    }
    plan = [
        ("projection_reads_the_same_under_both_bindings",
         lambda: check_projection_reads_the_same_under_both_bindings()),
        ("no_grant_is_refused", lambda: check_no_grant_is_refused(work)),
        ("wrong_scope_is_refused", lambda: check_wrong_scope_is_refused(work)),
        ("mutating_operations_unreachable",
         lambda: check_mutating_operations_unreachable(work)),
        ("grant_through_the_declared_console_surface",
         lambda: check_grant_through_the_declared_console_surface(work)),
        ("prove_vertical", check_prove_vertical),
        ("host_name_not_disclosed", lambda: check_host_name_not_disclosed(work)),
        ("refusal_exit_codes", check_refusal_exit_codes),
    ]
    for name, function in plan:
        try:
            report["checks"][name] = function()
        except Exception as failure:  # a probe that dies is a result, not a crash
            report["checks"][name] = {"held": None, "probe_error": repr(failure)}
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
