"""Work leases over the live-session store.

The session registry already knows which participants are running, in which tree, on
which branch, and whether their process still exists. It does not know what any of them
is holding, under what envelope, or what would count as done. This package adds those
three without adding a second execution model: same store, same identity source, same
liveness rule.
"""
