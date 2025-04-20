"""TaskContext class for PyNipe."""

import time
import logging
from typing import Dict, Any, Optional, TypeVar, Generic

from .task import Task
from .thread_local import get_current_workflow, set_current_task

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskContext:
    """Context manager for creating tasks within Python code."""
    
    def __init__(self, name: str, resources: Optional[Dict[str, Any]] = None):
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
        self.task: Optional[Task] = None
        self.start_time: Optional[float] = None
        
    def __enter__(self) -> 'TaskContext':
        """
        Enter the task context.
        
        Returns:
        --------
        TaskContext
            The task context instance
        """
        self.start_time = time.time()
        logger.info(f"Starting task: {self.name}")
        
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
            
        self.task.end_time = time.time()
        if self.start_time is not None:
            self.task.elapsed_time = self.task.end_time - self.start_time
        
        # Update task status
        if exc_type:
            self.task.status = "FAILED"
            self.task.error = exc_val
            logger.error(f"Task {self.name} failed: {exc_val}")
        else:
            if self.task.status == "PENDING":
                # If the task wasn't explicitly run, mark it as complete
                self.task.status = "COMPLETE"
            logger.info(f"Completed task: {self.name} in {self.task.elapsed_time:.2f}s")
        
        # Reset thread-local task
        set_current_task(None)
        
        # Return False to propagate exceptions
        return False
