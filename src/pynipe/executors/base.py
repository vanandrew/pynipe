"""Base class for execution backends."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from ..core.task import Task


class Executor(ABC):
    """Base class for execution backends."""

    @abstractmethod
    def execute(
        self,
        tasks: list[Task],
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        """
        Execute tasks with dependency resolution.

        Parameters:
        -----------
        tasks : list
            List of tasks to execute
        progress_callback : callable, optional
            Callback function to report progress. Takes task name and status as arguments.

        Returns:
        --------
        dict
            Results from all tasks
        """
        pass
