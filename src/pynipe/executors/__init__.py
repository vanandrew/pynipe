"""Execution backends for PyNipe."""

from .base import Executor
from .local import LocalExecutor

__all__ = [
    "Executor",
    "LocalExecutor",
]
