"""Base class for execution backends."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable

from ..core.task import Task


class Executor(ABC):
    """Base class for execution backends."""
    
    @abstractmethod
    def execute(self, tasks: List[Task], progress_callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, Any]:
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
