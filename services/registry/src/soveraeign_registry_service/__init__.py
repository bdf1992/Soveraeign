"""Public boundary of the reference Registry participant."""

from .core import RegistryService
from .index import RegistryIndexError, build_operation_index
from .routes import RegistryRoutes

__all__ = ["RegistryIndexError", "RegistryRoutes", "RegistryService",
           "build_operation_index"]
