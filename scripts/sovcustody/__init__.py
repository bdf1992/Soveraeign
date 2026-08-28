"""Custody, the work circuit, and the estimate registry.

`circuit` judges whether a ticket may advance a stage. `estimate` grades a cost
claim against the declared dimensions. `model` grades one custody and the
collection it belongs to. `board` derives the board for a custody from the live
tree rather than storing one. `render` prints them.

Nothing here settles anything. A custody records who is on the hook; it grants
no authority, changes no standing, and a stage advanced by the participant that
drew it is a build claim like any other.
"""

from __future__ import annotations
