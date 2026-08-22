from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from soveraeign_asset_service import AssetService


with TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = root / "example.txt"
    source.write_text("Soveraeign example asset\n", encoding="utf-8")
    service = AssetService(root / "state")
    service.grant("Bdo", "Bdo", "operate:derive")
    result = service.ingest(source, "Example Asset", "Bdo")
    run = service.request_derivative(result["asset_id"], result["version_id"], "Bdo")
    fence = service.claim(run, "local-worker")
    service.report_derivative(run, "local-worker", fence,
                            json.dumps({"summary": "Example Asset"}).encode())
    service.observe(run, "independent-observer")
    service.rebuild_projections()
    print(json.dumps({"asset": result, "receipts": service.receipts()}, indent=2))
    service.close()
