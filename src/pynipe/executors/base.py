"""Base class for execution backends."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from ..core.task import Task


class Executor(ABC):
    """Base class for execution backends."""
    
    @abstractmethod
    def execute(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Execute tasks with dependency resolution.
        
        Parameters:
        -----------
        tasks : list
            List of tasks to execute
            
        Returns:
        --------
        dict
            Results from all tasks
        """
        pass
