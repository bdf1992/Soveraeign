from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("deployment", ROOT / "scripts" / "deployment.py")
assert SPEC and SPEC.loader
deployment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deployment)
PINNED_IMAGE = "registry.example/soveraeign@sha256:" + "a" * 64
CUSTODY_CLAIM = "customer-soveraeign-custody"


class DeploymentTests(unittest.TestCase):
    def manifest(self) -> dict:
        path = ROOT / "infrastructure" / "phase-i.topology.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_preserves_portable_single_node_boundary(self):
        self.assertEqual(deployment.validate_manifest(self.manifest()), [])

    def test_both_profile_plans_are_observation_only(self):
        manifest = self.manifest()
        before = json.dumps(manifest, sort_keys=True)
        local = deployment.plan(manifest, "local")
        kubernetes = deployment.plan(manifest, "customer-kubernetes")
        self.assertEqual(local["gateway"]["exposure"], "LOOPBACK")
        self.assertEqual(kubernetes["gateway"]["exposure"], "CLUSTER_INTERNAL")
        self.assertEqual(json.dumps(manifest, sort_keys=True), before)

    def test_kubernetes_bundle_is_provider_neutral_and_verifiable(self):
        bundle = deployment.render_kubernetes(self.manifest(), PINNED_IMAGE, CUSTODY_CLAIM)
        self.assertEqual(deployment.verify_bundle(bundle), [])
        kinds = [item["kind"] for item in bundle["items"]]
        self.assertNotIn("Secret", kinds)
        self.assertNotIn("Ingress", kinds)
        self.assertEqual(kinds.count("Service"), 1)

    def test_mutable_or_unpinned_image_refuses(self):
        for image in ("soveraeign:latest", "soveraeign@sha256:abc", ""):
            with self.assertRaisesRegex(deployment.DeploymentRefused, "IMAGE_DIGEST"):
                deployment.render_kubernetes(self.manifest(), image, CUSTODY_CLAIM)

    def test_customer_owned_custody_claim_is_required_and_not_provisioned(self):
        with self.assertRaisesRegex(deployment.DeploymentRefused, "CUSTODY_CLAIM"):
            deployment.render_kubernetes(self.manifest(), PINNED_IMAGE, "Not Valid")
        bundle = deployment.render_kubernetes(self.manifest(), PINNED_IMAGE, CUSTODY_CLAIM)
        kinds = [item["kind"] for item in bundle["items"]]
        self.assertNotIn("PersistentVolumeClaim", kinds)
        workload = next(item for item in bundle["items"] if item["kind"] == "Deployment")
        volume = workload["spec"]["template"]["spec"]["volumes"][0]
        self.assertEqual(volume["persistentVolumeClaim"]["claimName"], CUSTODY_CLAIM)

    def test_multiple_replicas_refuse_until_write_fencing_is_earned(self):
        with self.assertRaisesRegex(deployment.DeploymentRefused, "MULTI_WRITER"):
            deployment.render_kubernetes(self.manifest(), PINNED_IMAGE, CUSTODY_CLAIM, replicas=2)

    def test_public_gateway_service_refuses(self):
        for service_type in ("LoadBalancer", "NodePort", "ExternalName"):
            with self.assertRaisesRegex(deployment.DeploymentRefused, "PUBLIC_SERVICE"):
                deployment.render_kubernetes(self.manifest(), PINNED_IMAGE, CUSTODY_CLAIM,
                                             service_type=service_type)

    def test_federation_refuses_before_two_node_crossing_case(self):
        with self.assertRaisesRegex(deployment.DeploymentRefused, "FEDERATION"):
            deployment.render_kubernetes(self.manifest(), PINNED_IMAGE, CUSTODY_CLAIM,
                                         federation=True)

    def test_queue_and_broker_cannot_claim_authority(self):
        for role in ("queue", "broker"):
            manifest = self.manifest()
            manifest["node"]["roles"][role]["authority"] = "EXECUTION"
            self.assertIn(f"ROLE_AUTHORITY_INFLATED:{role}", deployment.validate_manifest(manifest))

    def test_independent_verifier_observes_security_regression(self):
        bundle = deployment.render_kubernetes(self.manifest(), PINNED_IMAGE, CUSTODY_CLAIM)
        workload = next(item for item in bundle["items"] if item["kind"] == "Deployment")
        container = workload["spec"]["template"]["spec"]["containers"][0]
        container["securityContext"]["readOnlyRootFilesystem"] = False
        self.assertIn("CONTAINER_SECURITY_UNSAFE", deployment.verify_bundle(bundle))


if __name__ == "__main__":
    unittest.main()
