"""Atomic local persistence for Environment state."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar
import json
import os
import tempfile

from .errors import EnvironmentRefused
from .pattern import load_json

T = TypeVar("T")


@dataclass
class StateStore:
    """Small JSON store whose mutation lock spans read, decision, and write."""

    path: Path

    @property
    def lock_path(self) -> Path:
        return self.path.with_suffix(self.path.suffix + ".lock")

    @contextmanager
    def locked(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_fd: int | None = None
        try:
            lock_fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(lock_fd, str(os.getpid()).encode())
        except FileExistsError as error:
            raise EnvironmentRefused("STATE_WRITE_BUSY") from error
        try:
            yield
        finally:
            if lock_fd is not None:
                os.close(lock_fd)
            self.lock_path.unlink(missing_ok=True)

    def read(self) -> dict[str, Any]:
        return load_json(self.path)

    def _write_unlocked(self, state: dict[str, Any]) -> None:
        fd, temp_name = tempfile.mkstemp(prefix=self.path.name + ".", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(state, handle, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(temp_name, self.path)
        finally:
            Path(temp_name).unlink(missing_ok=True)

    def write(self, state: dict[str, Any]) -> None:
        with self.locked():
            self._write_unlocked(state)

    def update(self, change: Callable[[dict[str, Any]], T]) -> T:
        """Apply one read-modify-write transition under the same process lock."""
        with self.locked():
            state = load_json(self.path)
            result = change(state)
            self._write_unlocked(state)
            return result
