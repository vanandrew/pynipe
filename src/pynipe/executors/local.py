"""Local executor for parallel execution."""

import concurrent.futures
import logging
from collections.abc import Callable
from typing import Any

from ..core.task import Task
from .base import Executor

logger = logging.getLogger(__name__)


class LocalExecutor(Executor):
    """Execute tasks locally with parallel execution."""

    def __init__(self, max_workers: int | None = None):
        """
        Initialize local executor.

        Parameters:
        -----------
        max_workers : int, optional
            Maximum number of concurrent tasks
        """
        self.max_workers = max_workers

    def execute(
        self,
        tasks: list[Task],
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        """
        Execute tasks locally with dependency resolution.

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

        logger.info(f"Executing {len(tasks)} tasks with LocalExecutor")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while pending:
                # Find ready tasks (all dependencies satisfied)
                ready = [task for task in pending if all(dep in completed for dep in task.dependencies)]

                if not ready:
                    if not completed:
                        raise ValueError("Circular dependencies detected")
                    raise ValueError("Unable to resolve dependencies")

                logger.info(f"Submitting {len(ready)} ready tasks")

                # Submit ready tasks
                futures = {executor.submit(task.run): task for task in ready}

                # Remove from pending
                for task in ready:
                    pending.remove(task)

                # Wait for completed tasks
                for future in concurrent.futures.as_completed(futures):
                    task = futures[future]
                    try:
                        task_result = future.result()
                        results[task.name] = task_result
                        completed.add(task)
                        logger.info(f"Task {task.name} completed successfully")

                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(task.name, "COMPLETE")
                    except Exception as e:
                        logger.error(f"Task {task.name} failed: {e}")
                        raise

        logger.info("All tasks completed successfully")
        return results
