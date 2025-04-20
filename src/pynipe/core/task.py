"""Task and TaskOutput classes for PyNipe."""

import time
import logging
from typing import Dict, Any, Optional, Set, Union, TYPE_CHECKING

# Avoid circular imports
if TYPE_CHECKING:
    from nipype.interfaces.base import Interface

logger = logging.getLogger(__name__)


class TaskOutput:
    """Reference to a task's output."""
    
    def __init__(self, task: 'Task', output_name: str):
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


class Task:
    """A task representing a unit of neuroimaging processing work."""
    
    def __init__(
        self, 
        name: str, 
        interface: Optional['Interface'] = None, 
        inputs: Optional[Dict[str, Any]] = None, 
        resources: Optional[Dict[str, Any]] = None
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
        self.outputs: Dict[str, Any] = {}
        self.status = "PENDING"
        self.dependencies: Set['Task'] = set()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_time: Optional[float] = None
        self.error: Optional[Exception] = None
        self.command: Optional[str] = None
        
    def connect_input(self, input_name: str, source_task: 'Task', output_name: str) -> None:
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
        
    def run(self, executor=None) -> Dict[str, Any]:
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
        if self.interface is None:
            raise ValueError(f"Task {self.name} has no interface to execute")
            
        # Resolve inputs (replace TaskOutput references with actual values)
        resolved_inputs = self._resolve_inputs()
        
        # Set interface inputs
        for key, value in resolved_inputs.items():
            setattr(self.interface.inputs, key, value)
        
        # Execute interface
        self.status = "RUNNING"
        self.start_time = time.time()
        
        try:
            logger.info(f"Running task: {self.name}")
            result = self.interface.run()
            self.status = "COMPLETE"
            
            # Store command for debugging
            self.command = result.runtime.cmdline
            logger.debug(f"Command: {self.command}")
            
            # Store outputs
            for output_name in self.interface.output_spec().get().keys():
                if hasattr(result.outputs, output_name):
                    self.outputs[output_name] = getattr(result.outputs, output_name)
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
    
    def _resolve_inputs(self) -> Dict[str, Any]:
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
