from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from soveraeign_asset_service import (
    AssetService,
    ReaderDeclaration,
    digest_configuration,
)


with TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = root / "example.txt"
    source.write_text("Soveraeign example asset\n", encoding="utf-8")
    service = AssetService(root / "state")
    service.grant("Bdo", "Bdo", "operate:derive")
    result = service.ingest(source, "Example Asset", "Bdo")
    reader = ReaderDeclaration(
        reader_id="asset.metadata-card",
        reader_version="1.0.0",
        configuration_digest=digest_configuration(
            {"format": "json", "schema": "card-v1"}
        ),
        fidelity="LOSSY",
        omissions=("binary-payload",),
    )
    run = service.request_derivative(
        result["asset_id"], result["version_id"], "Bdo", reader=reader
    )
    fence = service.claim(run, "local-worker")
    service.report_derivative(
        run,
        "local-worker",
        fence,
        json.dumps({"summary": "Example Asset"}).encode(),
    )
    service.observe(run, "independent-observer")
    service.rebuild_projections()
    print(json.dumps({"asset": result, "receipts": service.receipts()}, indent=2))
    service.close()
