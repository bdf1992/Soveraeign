from __future__ import annotations

from pathlib import Path

path = Path("services/asset/tests/test_operational_record.py")
text = path.read_text(encoding="utf-8")
old = '''            self.assertEqual(asset.history(result["asset_id"])[0]["version_id"],
                             result["version_id"])
'''
new = '''            self.assertEqual(asset.history(result["asset_id"])[0]["id"],
                             result["version_id"])
'''
if old not in text:
    raise SystemExit("expected Asset history assertion not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
