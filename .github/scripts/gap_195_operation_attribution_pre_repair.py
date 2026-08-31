from __future__ import annotations

from pathlib import Path


path = Path("scripts/sovnode/bindings.py")
text = path.read_text(encoding="utf-8")
old = '''    if not session_id or not session_binding_id:
        raise BindingRefusal("SESSION_IDENTITY_REQUIRED", operation_id)
    if principal_id is not None and not principal_id:
        raise BindingRefusal("SESSION_IDENTITY_REQUIRED", operation_id)
    routes = [route for route in record["reachability"] if route["policy_active"]]
    if len(routes) != 1:
        raise BindingRefusal("ROUTE_AMBIGUOUS", operation_id)
'''
new = '''    routes = [route for route in record["reachability"] if route["policy_active"]]
    if len(routes) != 1:
        raise BindingRefusal("ROUTE_AMBIGUOUS", operation_id)
    if not session_id or not session_binding_id:
        raise BindingRefusal("SESSION_IDENTITY_REQUIRED", operation_id)
    if principal_id is not None and not principal_id:
        raise BindingRefusal("SESSION_IDENTITY_REQUIRED", operation_id)
'''
if old not in text:
    raise SystemExit("expected transformed Node Interface binding block is missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
