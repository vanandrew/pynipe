"""Serial executor for sequential execution."""

import logging
from typing import List, Dict, Any, Set, Optional

from .base import Executor
from ..core.task import Task

logger = logging.getLogger(__name__)


class SerialExecutor(Executor):
    """Execute tasks sequentially in a single thread."""
    
    def __init__(self):
        """Initialize serial executor."""
        pass
        
    def execute(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Execute tasks sequentially with dependency resolution.
        
        Parameters:
        -----------
        tasks : list
            List of tasks to execute
            
        Returns:
        --------
        dict
            Results from all tasks
        """
        results = {}
        pending = list(tasks)
        completed: Set[Task] = set()
        
        logger.info(f"Executing {len(tasks)} tasks with SerialExecutor")
        
        while pending:
            # Find ready tasks (all dependencies satisfied)
            ready = [task for task in pending 
                     if all(dep in completed for dep in task.dependencies)]
            
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
            except Exception as e:
                logger.error(f"Task {task.name} failed: {e}")
                raise
        
        logger.info(f"All tasks completed successfully")
        return results
