"""OutputProxy class for automatic dependency tracking."""

from typing import Any, Generic, TypeVar

from ..core.task import Task
from ..core.thread_local import get_current_task

T = TypeVar("T")


class OutputProxy(Generic[T]):
    """Proxy for task outputs that tracks dependencies."""

    def __init__(self, task: Task, output_name: str, value: T):
        """
        Initialize an output proxy.

        Parameters:
        -----------
        task : Task
            Source task that produced the output
        output_name : str
            Name of the output parameter
        value : Any
            The actual output value
        """
        self.task = task
        self.output_name = output_name
        self.value = value

    def __repr__(self) -> str:
        return f"OutputProxy({repr(self.value)})"

    def __getattr__(self, name: str) -> Any:
        """
        Get attribute from the underlying value and track dependency.

        Parameters:
        -----------
        name : str
            Name of the attribute to get

        Returns:
        --------
        Any
            The attribute value
        """
        # Record dependency if used in another task
        current_task = get_current_task()
        if current_task is not None and current_task != self.task:
            # Use the attribute name as the input name
            current_task.connect_input(name, self.task, self.output_name)

        # Get attribute from the underlying value
        return getattr(self.value, name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Call the underlying value and track dependency.

        Parameters:
        -----------
        *args : Any
            Positional arguments
        **kwargs : Any
            Keyword arguments

        Returns:
        --------
        Any
            The result of the call
        """
        # Record dependency if used in another task
        current_task = get_current_task()
        if current_task is not None and current_task != self.task:
            # This is a bit of a hack since we don't know what input name to use
            # We'll use a generated name based on the output name
            input_name = f"{self.output_name}_func_result"
            current_task.connect_input(input_name, self.task, self.output_name)

        # Call the underlying value
        return self.value(*args, **kwargs)

    def __getitem__(self, key: Any) -> Any:
        """
        Get item from the underlying value and track dependency.

        Parameters:
        -----------
        key : Any
            The key to lookup

        Returns:
        --------
        Any
            The item value
        """
        # Record dependency if used in another task
        current_task = get_current_task()
        if current_task is not None and current_task != self.task:
            # Similar hack as above
            input_name = f"{self.output_name}_item_{key}"
            current_task.connect_input(input_name, self.task, self.output_name)

        return self.value[key]
