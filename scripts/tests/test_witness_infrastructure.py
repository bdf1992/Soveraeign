from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "witness_observe", ROOT / "scripts" / "witness_observe.py"
)
assert SPEC and SPEC.loader
observe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observe)
PINNED_IMAGE = "registry.example/soveraeign@sha256:" + "a" * 64
CUSTODY_CLAIM = "witness-owned-custody"


class WitnessProtocolTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
