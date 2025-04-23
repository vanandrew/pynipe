"""Serial executor for sequential execution."""

import logging
from collections.abc import Callable
from typing import Any

from ..core.task import Task
from .base import Executor

logger = logging.getLogger(__name__)


class SerialExecutor(Executor):
    """Execute tasks sequentially in a single thread."""

    def __init__(self):
        """Initialize serial executor."""
        pass

    def execute(
        self,
        tasks: list[Task],
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        """
        Execute tasks sequentially with dependency resolution.

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
        results = {}
        pending = list(tasks)
        completed: set[Task] = set()

        logger.info(f"Executing {len(tasks)} tasks with SerialExecutor")

        while pending:
            # Find ready tasks (all dependencies satisfied)
            ready = [task for task in pending if all(dep in completed for dep in task.dependencies)]

            if not ready:
                if not completed:
                    raise ValueError("Circular dependencies detected")
                raise ValueError("Unable to resolve dependencies")

            # Execute one task at a time
            task = ready[0]
            logger.info(f"Executing task: {task.name}")

            try:
                task_result = task.run()
                results[task.name] = task_result
                completed.add(task)
                pending.remove(task)
                logger.info(f"Task {task.name} completed successfully")

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(task.name, "COMPLETE")
            except Exception as e:
                logger.error(f"Task {task.name} failed: {e}")
                raise

        logger.info("All tasks completed successfully")
        return results
