#!/usr/bin/env python3
"""CLI for the local Environment / Trunk / Deployment reference vertical.

Proposal, workspace, history, and selector operations are executable. Promotion
admission deliberately fails closed until the root admits the minimal Environment
authority aperture tracked by #12/#190; a caller-supplied authority label is not a
grant and cannot cross that boundary.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

from sovenv import (
    EnvironmentRefused,
    StateStore,
    bind_workspace,
    instantiate_environment,
    instantiate_trunk,
    land_crossing,
    load_json,
    new_state,
    propose_crossing,
    release_workspace,
    resolve_selector,
    validate_pattern,
)
from sovenv.model import digest

AUTHORITY_APERTURE_REFUSAL = (
    "AUTHORITY_REFUSED:ENVIRONMENT_AUTHORITY_APERTURE_UNADMITTED"
)


def required(value: str | None, name: str) -> str:
    if not value:
        raise EnvironmentRefused(f"{name}_REQUIRED")
    return value


def _pattern_matches(state: dict[str, object], pattern: dict[str, object]) -> None:
    if state.get("pattern_digest") != digest(pattern):
        raise EnvironmentRefused("PATTERN_CHANGED_REINSTANTIATION_REQUIRED")


def _mutate(args: argparse.Namespace, pattern: dict[str, object], state: dict) -> object:
    _pattern_matches(state, pattern)
    if args.operation == "env-add":
        return instantiate_environment(
            state,
            pattern,
            required(args.definition, "DEFINITION"),
            required(args.instance, "INSTANCE"),
        )
    if args.operation == "trunk-add":
        return instantiate_trunk(
            state,
            pattern,
            required(args.definition, "DEFINITION"),
            required(args.instance, "INSTANCE"),
        )
    if args.operation == "workspace-bind":
        if args.lease is None:
            raise EnvironmentRefused("LEASE_REQUIRED")
        return bind_workspace(
            state,
            load_json(args.lease),
            workspace=required(args.workspace, "WORKSPACE"),
            branch=required(args.branch, "BRANCH"),
            base_revision=required(args.base_revision, "BASE_REVISION"),
        )
    if args.operation == "workspace-release":
        if args.lease is None:
            raise EnvironmentRefused("LEASE_REQUIRED")
        return release_workspace(
            state,
            load_json(args.lease),
            reason=required(args.reason, "REASON"),
        )
    if args.operation == "propose":
        return propose_crossing(
            state,
            pattern,
            trunk_instance=required(args.trunk, "TRUNK"),
            source_instance=required(args.source, "SOURCE"),
            target_instance=required(args.target, "TARGET"),
            revision=required(args.revision, "REVISION"),
            artifact_digest=required(args.artifact_digest, "ARTIFACT_DIGEST"),
            config_digest=required(args.config_digest, "CONFIG_DIGEST"),
            actor=required(args.actor, "ACTOR"),
            integration_base=required(args.integration_base, "INTEGRATION_BASE"),
            evidence=args.evidence,
        )
    if args.operation == "admit":
        # The transition model accepts an authority type so the generalized gate can be
        # tested independently. The operator surface must not turn that model input into
        # permission. The repository AuthorityGrant contract is currently path-scoped and
        # no Environment crossing capability/resource scope has been root-admitted yet.
        # Until that aperture exists, every CLI admission attempt fails closed through the
        # kernel's existing authority refusal vocabulary, even if --authority is supplied.
        raise EnvironmentRefused(AUTHORITY_APERTURE_REFUSAL)
    if args.operation == "land":
        return land_crossing(
            state,
            required(args.crossing, "CROSSING"),
            landing_revision=required(args.revision, "REVISION"),
        )
    raise EnvironmentRefused(f"MUTATION_OPERATION_UNKNOWN:{args.operation}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=(
            "validate",
            "init",
            "env-add",
            "trunk-add",
            "workspace-bind",
            "workspace-release",
            "propose",
            "admit",
            "land",
            "waiting",
            "resolve",
            "history",
            "show",
        ),
    )
    parser.add_argument("--pattern", type=Path, required=True)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--definition")
    parser.add_argument("--instance")
    parser.add_argument("--selector")
    parser.add_argument("--lease", type=Path)
    parser.add_argument("--workspace")
    parser.add_argument("--branch")
    parser.add_argument("--base-revision")
    parser.add_argument("--reason")
    parser.add_argument("--trunk")
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--revision")
    parser.add_argument("--artifact-digest")
    parser.add_argument("--config-digest")
    parser.add_argument("--actor")
    parser.add_argument("--integration-base")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--crossing")
    parser.add_argument("--witness")
    parser.add_argument(
        "--authority",
        help="model input only; cannot authorize CLI admission until the authority aperture is admitted",
    )
    parser.add_argument("--accepted", action="store_true")
    args = parser.parse_args(argv)
    try:
        pattern = load_json(args.pattern)
        defects = validate_pattern(pattern)
        if args.operation == "validate":
            result = {"outcome": "FAIL" if defects else "PASS", "defects": defects}
            print(json.dumps(result, indent=2, sort_keys=True))
            return 1 if defects else 0
        if defects:
            raise EnvironmentRefused("; ".join(defects))
        if args.state is None:
            raise EnvironmentRefused("STATE_REQUIRED")
        store = StateStore(args.state)
        if args.operation == "init":
            result = new_state(pattern)
            store.write(result)
        elif args.operation in {
            "env-add",
            "trunk-add",
            "workspace-bind",
            "workspace-release",
            "propose",
            "admit",
            "land",
        }:
            result = store.update(lambda state: _mutate(args, pattern, state))
        else:
            state = store.read()
            _pattern_matches(state, pattern)
            if args.operation == "waiting":
                result = [
                    item for item in state["crossing_records"] if item["status"] == "PROPOSED"
                ]
            elif args.operation == "resolve":
                result = resolve_selector(state, pattern, required(args.selector, "SELECTOR"))
            elif args.operation == "history":
                result = {
                    "crossings": state["crossing_records"],
                    "deployments": state["deployments"],
                    "receipts": state.get("receipts", []),
                    "workspace_bindings": state["workspace_bindings"],
                }
            else:
                result = state
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (EnvironmentRefused, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"outcome": "REFUSED", "reason": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
