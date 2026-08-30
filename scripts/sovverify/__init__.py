"""Verification harness parts and assembly of the runner's declared check table.

The ordinary repository/participant checks live in ``sovverify.checks``. The two
machinery-integrity guards are assembled here so every import of that table sees
them, including snapshot/count readers and ``scripts/verify.py`` itself. Keeping
them outside ``scripts/tests`` is deliberate: the population or verdict path they
grade must not be able to remove the guard that catches it.
"""

from sovverify import checks as _checks
from sovverify.integrity import INTEGRITY_CHECKS


_checks.CHECKS = _checks.REPOSITORY_CHECKS + INTEGRITY_CHECKS + _checks.PARTICIPANT_CHECKS
