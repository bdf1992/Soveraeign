"""Load the Gateway vertical-slice participant cases into the repository test gate.

The canonical tests live beside the Gateway service. This loader keeps the root
verification path aware of them without duplicating their assertions.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "services" / "gateway" / "tests" / "test_gateway_slice.py"
spec = spec_from_file_location("gateway_vertical_slice", TEST)
assert spec is not None and spec.loader is not None
module = module_from_spec(spec)
spec.loader.exec_module(module)

GatewayVerticalSlice = module.GatewayVerticalSlice
