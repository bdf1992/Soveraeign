from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "witness_observe", ROOT / "scripts" / "witness_observe.py"
)
assert SPEC and SPEC.loader
observe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observe)
NO_POSIX = ("Permission drift is drift in POSIX mode bits, which this platform does not "
            "have. The observer reports no permission defect here because it cannot see "
            "one, not because none exists; custody receipts written on this platform say "
            "identity_enforcement UNAVAILABLE_ON_THIS_PLATFORM for the same reason.")
PINNED_IMAGE = "registry.example/soveraeign@sha256:" + "a" * 64
CUSTODY_CLAIM = "witness-owned-custody"


class WitnessProtocolTests(unittest.TestCase):
    @unittest.skipUnless(observe.custody_posix.available, NO_POSIX)
    def test_independent_local_observer_detects_permission_drift(self):
        manifest = json.loads(
            (ROOT / "infrastructure" / "phase-i.local.json").read_text(encoding="utf-8")
        )
        with TemporaryDirectory() as temporary:
            node = Path(temporary) / "node"
            node.mkdir(mode=0o700)
            for relative in manifest["custody"]["paths"].values():
                (node / relative).mkdir(parents=True, mode=0o700)
            receipt = {
                "manifest_digest": observe.sha256(observe.canonical_bytes(manifest)).hexdigest(),
                "effect_class": "RECORD_LOCAL",
            }
            (node / ".soveraeign-infrastructure.json").write_text(
                json.dumps(receipt), encoding="utf-8"
            )
            os.chmod(node / "record", 0o755)
            self.assertIn("PATH_BOUNDARY:record", observe.independent_local_defects(node, manifest))

    def test_independent_bundle_observer_detects_public_gateway(self):
        bundle = {
            "kind": "List",
            "items": [
                {"kind": "Service", "spec": {"type": "LoadBalancer"}},
                {
                    "kind": "Deployment",
                    "spec": {
                        "replicas": 1,
                        "strategy": {"type": "Recreate"},
                        "template": {
                            "spec": {
                                "automountServiceAccountToken": False,
                                "containers": [{
                                    "image": PINNED_IMAGE,
                                    "securityContext": {
                                        "readOnlyRootFilesystem": True,
                                        "runAsNonRoot": True,
                                        "capabilities": {"drop": ["ALL"]},
                                    },
                                }],
                                "volumes": [{
                                    "name": "custody",
                                    "persistentVolumeClaim": {"claimName": CUSTODY_CLAIM},
                                }],
                            }
                        },
                    },
                },
                {"kind": "ConfigMap", "data": {
                    "SOVERAEIGN_FEDERATION_MODE": "DISABLED",
                    "SOVERAEIGN_GATEWAY_PATROL_MODE": "OBSERVE_ONLY",
                }},
                {"kind": "NetworkPolicy", "spec": {"egress": []}},
            ],
        }
        self.assertIn(
            "PUBLIC_GATEWAY", observe.independent_bundle_defects(bundle, CUSTODY_CLAIM)
        )

    def test_independent_observer_detects_substituted_local_contract(self):
        import deployment

        topology = json.loads((ROOT / "infrastructure" / "phase-i.topology.json").read_text(
            encoding="utf-8"))
        local = json.loads((ROOT / "infrastructure" / "phase-i.local.json").read_text(
            encoding="utf-8"))
        bundle = deployment.render_kubernetes(topology, PINNED_IMAGE, CUSTODY_CLAIM)
        expected = json.loads(json.dumps(local))
        expected["custody"]["paths"]["work"] = "expected-work"
        self.assertIn("LOCAL_CONTRACT_SUBSTITUTED",
                      observe.independent_bundle_defects(bundle, CUSTODY_CLAIM, expected))


def activation_stage() -> tuple[object, object]:
    """Load whichever scripts/ module currently defines the activation stage.

    The stage moved out of witness_infrastructure.py into witness_stages.py, so the
    case binds to the function rather than to a file name and reads the same before
    and after that split.
    """
    for name in ("witness_stages", "witness_infrastructure"):
        module_path = ROOT / "scripts" / f"{name}.py"
        if not module_path.exists():
            continue
        spec = importlib.util.spec_from_file_location(name, module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attribute in ("exercise_activation", "_exercise_activation"):
            stage = getattr(module, attribute, None)
            if stage is not None:
                return module, stage
    raise AssertionError("no module under scripts/ defines the activation stage")


def resolve_as_the_body_would(function, name: str):
    """Resolve a global name exactly as the function body resolves it, or raise NameError.

    Calling the stage does not reach the name on every host: the activation stage
    refuses with HOST_CANNOT_ENFORCE_CUSTODY on its first line where os.geteuid is
    absent, so a Windows run goes green with an undefined name still in the body.
    Resolving the name through the function's own globals reaches it on every platform.
    """
    namespace = function.__globals__
    if name in namespace:
        return namespace[name]
    builtins = namespace.get("__builtins__")
    if isinstance(builtins, dict) and name in builtins:
        return builtins[name]
    if builtins is not None and hasattr(builtins, name):
        return getattr(builtins, name)
    raise NameError(f"name '{name}' is not defined")


class ActivationStageResolvesCustody(unittest.TestCase):
    """The custody lookup the activation stage performs must actually resolve.

    This is platform-independent by construction: it never calls os.geteuid and never
    runs the stage, so a host without POSIX identity still observes the binding.
    """

    def test_custody_posix_is_bound_where_the_activation_stage_reads_it(self):
        _, stage = activation_stage()
        custody = resolve_as_the_body_would(stage, "custody_posix")
        uid, gid = custody.effective()
        self.assertIsInstance(uid, int)
        self.assertIsInstance(gid, int)

    def test_the_witness_entry_point_keeps_its_refusal_codes(self):
        """The split must not move the CLI or rename a refusal reason."""
        spec = importlib.util.spec_from_file_location(
            "witness_infrastructure", ROOT / "scripts" / "witness_infrastructure.py"
        )
        assert spec and spec.loader
        entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entry)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = entry.main(["--witness-id", "probe", "--expected-commit", "0" * 40])
        self.assertEqual(code, 2)
        self.assertEqual(
            json.loads(buffer.getvalue()),
            {"outcome": "REFUSED", "reason": "INDEPENDENCE_DECLARATION_REQUIRED"},
        )


if __name__ == "__main__":
    unittest.main()
