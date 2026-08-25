"""Independent reconstruction of Asset Service derivative recordings."""

from __future__ import annotations

import json
from typing import Any

from .recording import (
    ReaderMaterials,
    ReaderUndeclared,
    RecordingChanged,
    SourceChanged,
)
from .store import PayloadIntegrityError, Store


class RecordingReconstructor:
    """Resolve and verify every material named by a derivative recording."""

    def __init__(self, store: Store, readers: ReaderMaterials):
        self.store = store
        self.db = store.db
        self.readers = readers

    def reconstruct(self, recording_or_version_id: str) -> dict[str, Any]:
        """Reconstruct one recording and independently verify all addressed inputs."""
        recording = self.db.execute(
            "SELECT * FROM recordings WHERE id=? OR output_version_id=?",
            (recording_or_version_id, recording_or_version_id),
        ).fetchone()
        if recording is None:
            raise KeyError(recording_or_version_id)
        run = self.db.execute(
            "SELECT * FROM runs WHERE id=?", (recording["run_id"],)
        ).fetchone()
        if run is None:
            raise KeyError(recording["run_id"])
        plan = self.db.execute(
            "SELECT * FROM derivative_plans WHERE run_id=?", (recording["run_id"],)
        ).fetchone()
        if plan is None:
            raise ReaderUndeclared(recording["run_id"])
        self._verify_links(recording, run, plan)
        self._verify_source(recording)
        reader_materials = self.readers.resolve(recording)
        self._verify_output(recording)
        try:
            omissions = json.loads(recording["omissions_json"])
        except (TypeError, json.JSONDecodeError) as error:
            raise RecordingChanged(recording["id"]) from error
        if not isinstance(omissions, list):
            raise RecordingChanged(recording["id"])
        return {
            "recording_id": recording["id"],
            "run_id": recording["run_id"],
            "operation": run["kind"],
            "output_version_id": recording["output_version_id"],
            "source_id": recording["source_id"],
            "source_digest": recording["source_digest"],
            "reader_id": recording["reader_id"],
            "reader_version": recording["reader_version"],
            "reader_address": recording["reader_address"],
            "reader_digest": recording["reader_digest"],
            "reader_artifact_address": reader_materials["reader_artifact_address"],
            "reader_artifact_digest": reader_materials["reader_artifact_digest"],
            "configuration_address": recording["configuration_address"],
            "configuration_digest": recording["configuration_digest"],
            "output_role": recording["output_role"],
            "payload_address": recording["payload_address"],
            "payload_digest": recording["payload_digest"],
            "fidelity": recording["fidelity"],
            "omissions": omissions,
            "produced_at": recording["produced_at"],
            "produced_by": recording["produced_by"],
            "standing": recording["standing"],
        }

    @staticmethod
    def _verify_links(recording: Any, run: Any, plan: Any) -> None:
        if (
            RecordingReconstructor._run_source(run) != recording["source_id"]
            or run["output_version_id"] != recording["output_version_id"]
        ):
            raise RecordingChanged(recording["id"])

    @staticmethod
    def _run_source(run: Any) -> str:
        """Resolve the one source of a reconstructable recording."""
        stored = run["input_version_id"]
        if stored.startswith("["):
            try:
                inputs = json.loads(stored)
            except json.JSONDecodeError as error:
                raise RecordingChanged(run["id"]) from error
            if not isinstance(inputs, list) or len(inputs) != 1:
                raise RecordingChanged(run["id"])
            return inputs[0]
        return stored
        recorded_plan_fields = (
            "source_id",
            "source_digest",
            "reader_id",
            "reader_version",
            "reader_address",
            "reader_digest",
            "configuration_address",
            "configuration_digest",
            "output_role",
            "fidelity",
            "omissions_json",
        )
        if any(recording[field] != plan[field] for field in recorded_plan_fields):
            raise RecordingChanged(recording["id"])

    def _verify_source(self, recording: Any) -> None:
        try:
            source, _ = self.store.verified_version(recording["source_id"])
        except PayloadIntegrityError as error:
            raise SourceChanged(recording["source_id"]) from error
        if f"sha256:{source['digest']}" != recording["source_digest"]:
            raise SourceChanged(recording["source_id"])

    def _verify_output(self, recording: Any) -> None:
        if recording["payload_address"] != f"cas:{recording['payload_digest']}":
            raise RecordingChanged(recording["output_version_id"])
        try:
            output, _ = self.store.verified_version(recording["output_version_id"])
        except PayloadIntegrityError as error:
            raise RecordingChanged(recording["output_version_id"]) from error
        if f"sha256:{output['digest']}" != recording["payload_digest"]:
            raise RecordingChanged(recording["output_version_id"])
