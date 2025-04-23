"""Workflow class for PyNipe."""

import logging
from collections.abc import Callable
from typing import Any

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from .task import Task
from .thread_local import set_current_workflow

logger = logging.getLogger(__name__)


class Workflow:
    """A collection of tasks with dependency tracking."""

    def __init__(self, name: str):
        """
        Initialize a workflow.

        Parameters:
        -----------
        name : str
            Name of the workflow
        """
        self.name = name
        self.tasks: list[Task] = []
        self.functions: list[dict[str, Any]] = []

    def add_task(self, task: Task) -> None:
        """
        Add a task to the workflow.

        Parameters:
        -----------
        task : Task
            Task to add
        """
        self.tasks.append(task)

    def get_task_by_name(self, name: str) -> Task | None:
        """
        Get a task by its name.

        Parameters:
        -----------
        name : str
            Name of the task to find

        Returns:
        --------
        Optional[Task]
            The task with the given name, or None if not found
        """
        for task in self.tasks:
            if task.name == name:
                return task
        return None

    def add_function(
        self,
        function: Callable,
        inputs: dict[str, Any] | None = None,
        name: str | None = None,
    ) -> None:
        """
        Add a processing function to the workflow.

        Parameters:
        -----------
        function : callable
            Processing function to add
        inputs : dict, optional
            Input parameters for the function
        name : str, optional
            Name for this function instance
        """
        name = name or function.__name__
        self.functions.append({"name": name, "function": function, "inputs": inputs or {}})

    def run(self, executor=None) -> dict[str, Any]:
        """
        Execute the workflow.

        Parameters:
        -----------
        executor : Executor, optional
            Execution backend

        Returns:
        --------
        dict
            Results from all tasks and functions
        """
        # Import here to avoid circular imports
        from ..executors.local import LocalExecutor

        executor = executor or LocalExecutor()

        logger.info(f"Running workflow: {self.name}")

        # Create a progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            # First pass: execute functions to generate tasks
            function_results = {}
            if self.functions:
                functions_progress = progress.add_task("[cyan]Executing functions...", total=len(self.functions))

                for _, func_info in enumerate(self.functions):
                    # Set current workflow for task collection
                    set_current_workflow(self)

                    # Update progress description
                    progress.update(
                        functions_progress,
                        description=f"[cyan]Executing function: {func_info['name']}",
                    )

                    # Execute function
                    try:
                        logger.info(f"Executing function: {func_info['name']}")
                        result = func_info["function"](**func_info["inputs"])
                        function_results[func_info["name"]] = result
                    except Exception as e:
                        logger.error(f"Function {func_info['name']} failed: {e}")
                        progress.update(
                            functions_progress,
                            description=f"[red]Function {func_info['name']} failed",
                        )
                        raise
                    finally:
                        set_current_workflow(None)

                    # Update progress
                    progress.update(functions_progress, advance=1)

                # Mark functions as complete
                progress.update(functions_progress, description="[green]Functions completed")

            # Second pass: execute only tasks that haven't been run yet
            tasks_to_run = [task for task in self.tasks if task.status == "PENDING"]
            if tasks_to_run:
                # Add a task progress for the executor
                tasks_progress = progress.add_task("[cyan]Executing tasks...", total=len(tasks_to_run))

                # Create a callback for the executor to update progress
                def progress_callback(task_name, status):
                    if status == "COMPLETE":
                        progress.update(tasks_progress, advance=1)
                        progress.update(
                            tasks_progress,
                            description=f"[cyan]Tasks completed: {progress.tasks[tasks_progress].completed}/{len(tasks_to_run)}",
                        )

                # Execute tasks with progress tracking
                task_results = executor.execute(tasks_to_run, progress_callback=progress_callback)

                # Mark tasks as complete
                progress.update(tasks_progress, description="[green]Tasks completed")
            else:
                task_results = {}

        # Combine results
        return {
            "functions": function_results,
            "tasks": task_results,
            "workflow": self,  # Include the workflow object for access to tasks and dependencies
        }

    def to_airflow(
        self,
        dag_file: str,
        schedule: str | None = None,
        default_args: dict[str, Any] | None = None,
    ) -> None:
        """
        Export the workflow to an Airflow DAG.

        Parameters:
        -----------
        dag_file : str
            Path to output DAG file
        schedule : str, optional
            Airflow schedule expression
        default_args : dict, optional
            Default arguments for Airflow tasks
        """
        # This will be implemented in a later phase
        raise NotImplementedError("Airflow export not yet implemented")

    def __repr__(self) -> str:
        return f"Workflow(name={self.name}, tasks={len(self.tasks)}, functions={len(self.functions)})"
