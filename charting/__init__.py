"""Experimental typed-contract charting substrate.

This package is a provisional implementation target for issue #40. It owns no
canonical policy; governing documents remain authoritative.
"""

from .model import ChartingError, ContractGraph

__all__ = ["ChartingError", "ContractGraph"]
