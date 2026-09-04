"""Verification harness parts and assembly of the runner's declared check table.

The ordinary repository/participant checks live in ``sovverify.checks``. The two
machinery-integrity guards are assembled here so every import of that table sees
them, including snapshot/count readers and ``scripts/verify.py`` itself. Keeping
them outside ``scripts/tests`` is deliberate: the population or verdict path they
grade must not be able to remove the guard that catches it.
"""

from sovverify import checks as _checks
from sovverify.integrity import INTEGRITY_CHECKS


# Splice the guards in ahead of the participant tail rather than re-listing the
# groups. Naming them here once meant a group added in `checks.py` was dropped
# from every run while `checks.py` still read as though it composed the table:
# the split into `projections.py` lost five checks that way, and the loss was
# visible only as a count nobody expected. The tail is the only position this
# assembly needs to know, so a new group now flows through untouched.
_ordinary = _checks.CHECKS
_tail = len(_checks.PARTICIPANT_CHECKS)
_checks.CHECKS = _ordinary[:len(_ordinary) - _tail] + INTEGRITY_CHECKS + _ordinary[-_tail:]
