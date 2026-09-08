"""Verification harness parts and assembly of the runner's declared check table.

The ordinary repository/participant checks live in ``sovverify.checks``. The two
machinery-integrity guards are assembled here so every import of that table sees
them, including snapshot/count readers and ``scripts/verify.py`` itself. Keeping
them outside ``scripts/tests`` is deliberate: the population or verdict path they
grade must not be able to remove the guard that catches it.
"""

from sovverify import checks as _checks
from sovverify.commissioning import COMMISSIONING_CHECKS
from sovverify.harness import HARNESS_CHECKS
from sovverify.integrity import INTEGRITY_CHECKS


#: Every group is named here explicitly. A group added to `checks.py` but not to
#: this tuple is imported, registered and never run, which reads as a passing
#: check that does not exist; `sovverify.harness` was in exactly that state
#: between its split and 2026-09-08.
_checks.CHECKS = (_checks.REPOSITORY_CHECKS + HARNESS_CHECKS + INTEGRITY_CHECKS
                  + COMMISSIONING_CHECKS + _checks.PARTICIPANT_CHECKS)
