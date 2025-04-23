"""TaskContext class for PyNipe."""

import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from .task import OutputProxy, Task
from .thread_local import get_current_workflow, set_current_task

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TaskContext:
    """Context manager for creating tasks within Python code."""

    def __init__(self, name: str, resources: dict[str, Any] | None = None):
        """
        Initialize a task context.

        Parameters:
        -----------
        name : str
            Name of the task
        resources : dict, optional
            Resource requirements
        """
        self.name = name
        self.resources = resources or {}
        self.task: Task | None = None
        self.start_time: float | None = None

    def __enter__(self) -> "TaskContext":
        """
        Enter the task context.

        Returns:
        --------
        TaskContext
            The task context instance
        """
        self.start_time = time.time()
        logger.info(f"Creating task: {self.name}")

        # Create actual task
        self.task = Task(self.name, resources=self.resources)

        # Register with current workflow
        workflow = get_current_workflow()

        # Register with workflow for later scheduling
        if workflow is not None:
            workflow.add_task(self.task)

        # Enable dependency tracking by setting thread-local task
        set_current_task(self.task)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the task context.

        Parameters:
        -----------
        exc_type : type
            Exception type if an exception was raised
        exc_val : Exception
            Exception value if an exception was raised
        exc_tb : traceback
            Exception traceback if an exception was raised

        Returns:
        --------
        bool
            False to propagate exceptions
        """
        if self.task is None:
            return False

        # Record end time for context timing
        logger.info(f"Task {self.name} Created")

        # Update task status if an exception occurred
        if exc_type:
            self.task.status = "FAILED"
            self.task.error = exc_val
            logger.error(f"Task {self.name} failed: {exc_val}")

        # Reset thread-local task
        set_current_task(None)

        # Return False to propagate exceptions
        return False

    def set_interface(self, interface: Any) -> None:
        """
        Set the nipype interface for this task.

        Parameters:
        -----------
        interface : nipype.Interface
            The interface to use for this task
        """
        if self.task is None:
            raise ValueError("Task not initialized")

        self.task.interface = interface

    def configure_interface(self, **kwargs) -> None:
        """
        Configure the interface with input parameters.

        Parameters:
        -----------
        **kwargs : dict
            Input parameters for the interface
        """
        if self.task is None:
            raise ValueError("Task not initialized")

        self.task.configure_interface(**kwargs)

    def set_python_function(self, func: Callable, outputs: list[str], *args, **kwargs) -> None:
        """
        Set a Python function to be executed by this task.

        Parameters:
        -----------
        func : callable
            The Python function to execute
        outputs : list
            List of output names that will be produced by the function
        *args : tuple
            Positional arguments to pass to the function
        **kwargs : dict
            Keyword arguments to pass to the function
        """
        if self.task is None:
            raise ValueError("Task not initialized")

        self.task.set_python_function(func, outputs, *args, **kwargs)

    def python_function(self, outputs: list[str], *args, **kwargs) -> Callable[[Callable], Callable]:
        """
        Decorator for registering a Python function to be executed by this task.

        Parameters:
        -----------
        outputs : list
            List of output names that will be produced by the function
        *args : tuple
            Positional arguments to pass to the function
        **kwargs : dict
            Keyword arguments to pass to the function

        Returns:
        --------
        callable
            Decorator function

        Example:
        --------
        @ctx.python_function(["output_file"], mask_file, output_file)
        def calculate_brain_volume(mask_file, output_file):
            # Function implementation
            return output_file
        """

        def decorator(func: Callable) -> Callable:
            # Register the function with the task
            self.set_python_function(func, outputs, *args, **kwargs)
            # Return the original function so it can still be called normally
            return func

        return decorator

    def get_output_proxy(self) -> OutputProxy:
        """
        Get a proxy for the outputs that will be available after execution.

        Returns:
        --------
        OutputProxy
            Proxy for the task's outputs
        """
        if self.task is None:
            raise ValueError("Task not initialized")

        return self.task.get_output_proxy()
