"""Task and TaskOutput classes for PyNipe."""

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast

# Avoid circular imports
if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TaskOutput:
    """Reference to a task's output."""

    def __init__(self, task: "Task", output_name: str):
        """
        Initialize a task output reference.

        Parameters:
        -----------
        task : Task
            Source task to get output from
        output_name : str
            Name of the output parameter from source task
        """
        self.task = task
        self.output_name = output_name

    def __repr__(self) -> str:
        return f"TaskOutput(task={self.task.name}, output={self.output_name})"


class OutputProxy:
    """Proxy for outputs that will be available after task execution."""

    def __init__(self, task: "Task"):
        """
        Initialize an output proxy.

        Parameters:
        -----------
        task : Task
            The task that will produce the outputs
        """
        self.task = task
        self.outputs = type("OutputsNamespace", (), {})()

        # Create proxy attributes for all expected outputs
        if task.interface is not None:
            try:
                # Safe way to check and call output_spec
                if hasattr(task.interface, "output_spec"):
                    output_spec_method = task.interface.output_spec
                    if callable(output_spec_method):
                        output_spec = output_spec_method()
                        # Check if output_spec has a get method and call it
                        if output_spec is not None and hasattr(output_spec, "get"):
                            get_method = output_spec.get
                            if callable(get_method):
                                output_dict = get_method()
                                if isinstance(output_dict, dict):
                                    for output_name in output_dict:
                                        setattr(
                                            self.outputs,
                                            output_name,
                                            TaskOutput(task, output_name),
                                        )
            except (AttributeError, TypeError, ValueError) as e:
                logger.warning(f"Could not get output spec for task {task.name}: {e}")

        # For Python function tasks, add custom outputs
        if task.is_python_task and task.python_outputs:
            for output_name in task.python_outputs:
                setattr(self.outputs, output_name, TaskOutput(task, output_name))


class Task:
    """A task representing a unit of neuroimaging processing work."""

    def __init__(
        self,
        name: str,
        interface: Any | None = None,
        inputs: dict[str, Any] | None = None,
        resources: dict[str, Any] | None = None,
    ):
        """
        Initialize a task.

        Parameters:
        -----------
        name : str
            Name of the task
        interface : nipype.Interface, optional
            Nipype interface to execute
        inputs : dict, optional
            Input parameters for the interface
        resources : dict, optional
            Resource requirements (e.g., {"cpu": 4, "memory": "8GB"})
        """
        self.name = name
        self.interface = interface
        self.inputs = inputs or {}
        self.resources = resources or {}
        self.outputs: dict[str, Any] = {}
        self.status = "PENDING"
        self.dependencies: set[Task] = set()
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.elapsed_time: float | None = None
        self.error: Exception | None = None
        self.command: str | None = None

        # For Python function tasks
        self.python_function: Callable | None = None
        self.python_args: list[Any] = []
        self.python_kwargs: dict[str, Any] = {}
        self.python_outputs: list[str] = []
        self.is_python_task: bool = False

    def connect_input(self, input_name: str, source_task: "Task", output_name: str) -> None:
        """
        Connect an input to an output from another task.

        Parameters:
        -----------
        input_name : str
            Name of the input parameter
        source_task : Task
            Source task to get output from
        output_name : str
            Name of the output parameter from source task
        """
        self.inputs[input_name] = TaskOutput(source_task, output_name)
        self.dependencies.add(source_task)

    def configure_interface(self, **kwargs) -> None:
        """
        Configure the interface with input parameters.

        Parameters:
        -----------
        **kwargs : dict
            Input parameters for the interface
        """
        if self.interface is None:
            raise ValueError(f"Task {self.name} has no interface to configure")

        for key, value in kwargs.items():
            if isinstance(value, TaskOutput):
                # Record dependency
                self.dependencies.add(value.task)

            # Store in inputs for later resolution
            self.inputs[key] = value

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
        self.python_function = func
        self.python_outputs = outputs
        self.python_args = list(args)
        self.python_kwargs = kwargs
        self.is_python_task = True

        # Check for TaskOutput in args and kwargs to track dependencies
        for arg in args:
            if isinstance(arg, TaskOutput):
                self.dependencies.add(arg.task)

        for _key, value in kwargs.items():
            if isinstance(value, TaskOutput):
                self.dependencies.add(value.task)

    def get_output_proxy(self) -> OutputProxy:
        """
        Get a proxy for the outputs that will be available after execution.

        Returns:
        --------
        OutputProxy
            Proxy for the task's outputs
        """
        return OutputProxy(self)

    def run(self, executor=None) -> dict[str, Any]:
        """
        Execute the task.

        Parameters:
        -----------
        executor : Executor, optional
            Execution backend (default: local execution)

        Returns:
        --------
        dict
            Task outputs
        """
        # Resolve inputs (replace TaskOutput references with actual values)
        resolved_inputs = self._resolve_inputs()

        # Set status to running
        self.status = "RUNNING"
        self.start_time = time.time()

        try:
            logger.info(f"Running task: {self.name}")

            if self.is_python_task and self.python_function is not None:
                # Execute Python function
                self._run_python_function(resolved_inputs)
            elif self.interface is not None:
                # Execute nipype interface
                self._run_interface(resolved_inputs)
            else:
                raise ValueError(f"Task {self.name} has no interface or Python function to execute")

            self.status = "COMPLETE"

        except Exception as e:
            self.status = "FAILED"
            self.error = e
            logger.error(f"Task {self.name} failed: {e}")
            raise
        finally:
            self.end_time = time.time()
            self.elapsed_time = self.end_time - self.start_time
            logger.info(f"Task {self.name} completed in {self.elapsed_time:.2f}s")

        return self.outputs

    def _run_interface(self, resolved_inputs: dict[str, Any]) -> None:
        """
        Execute the nipype interface.

        Parameters:
        -----------
        resolved_inputs : dict
            Resolved input values
        """
        if self.interface is None:
            raise ValueError(f"Task {self.name} has no interface to execute")

        # Set interface inputs
        if hasattr(self.interface, "inputs"):
            interface_inputs = self.interface.inputs
            for key, value in resolved_inputs.items():
                setattr(interface_inputs, key, value)

        # Execute interface
        interface = cast(Any, self.interface)
        result = interface.run()

        # Store command for debugging
        if hasattr(result, "runtime") and hasattr(result.runtime, "cmdline"):
            self.command = result.runtime.cmdline
            logger.debug(f"Command: {self.command}")

        # Store outputs
        if hasattr(self.interface, "output_spec"):
            output_spec_method = self.interface.output_spec
            if callable(output_spec_method):
                output_spec = output_spec_method()
                if output_spec is not None and hasattr(output_spec, "get"):
                    get_method = output_spec.get
                    if callable(get_method):
                        output_dict = get_method()
                        if isinstance(output_dict, dict):
                            for output_name in output_dict:
                                if hasattr(result.outputs, output_name):
                                    self.outputs[output_name] = getattr(result.outputs, output_name)

    def _run_python_function(self, resolved_inputs: dict[str, Any]) -> None:
        """
        Execute the Python function.

        Parameters:
        -----------
        resolved_inputs : dict
            Resolved input values
        """
        if self.python_function is None:
            raise ValueError(f"Task {self.name} has no Python function to execute")

        # Prepare args and kwargs
        args = []
        for arg in self.python_args:
            if isinstance(arg, TaskOutput):
                # Get the resolved value
                source_task = arg.task
                output_name = arg.output_name
                args.append(source_task.outputs[output_name])
            else:
                args.append(arg)

        kwargs = {}
        for key, value in self.python_kwargs.items():
            if isinstance(value, TaskOutput):
                # Get the resolved value
                source_task = value.task
                output_name = value.output_name
                kwargs[key] = source_task.outputs[output_name]
            else:
                kwargs[key] = value

        # Execute function
        self.command = f"Python function: {self.python_function.__name__}"
        result = self.python_function(*args, **kwargs)

        # Store outputs
        if isinstance(result, dict):
            # If the function returns a dict, use it as outputs
            for key, value in result.items():
                self.outputs[key] = value
        elif isinstance(result, tuple) and len(result) == len(self.python_outputs):
            # If the function returns a tuple with the same length as python_outputs,
            # map the values to the output names
            for i, output_name in enumerate(self.python_outputs):
                self.outputs[output_name] = result[i]
        elif len(self.python_outputs) == 1:
            # If there's only one output name, use the result as is
            self.outputs[self.python_outputs[0]] = result
        else:
            # Otherwise, store the result as 'result'
            self.outputs["result"] = result

    def _resolve_inputs(self) -> dict[str, Any]:
        """
        Resolve inputs that reference outputs from other tasks.

        Returns:
        --------
        dict
            Resolved input values

        Raises:
        -------
        ValueError
            If a dependency task is not complete or output not found
        """
        resolved = {}

        for key, value in self.inputs.items():
            if isinstance(value, TaskOutput):
                # Get output from dependency task
                source_task = value.task
                output_name = value.output_name

                # Ensure dependency is complete
                if source_task.status != "COMPLETE":
                    raise ValueError(f"Dependency {source_task.name} not complete")

                if output_name not in source_task.outputs:
                    raise ValueError(f"Output {output_name} not found in task {source_task.name}")

                resolved[key] = source_task.outputs[output_name]
            else:
                # Pass through regular values
                resolved[key] = value

        return resolved

    def __repr__(self) -> str:
        return f"Task(name={self.name}, status={self.status})"
