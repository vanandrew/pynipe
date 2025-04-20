"""Thread-local storage for tracking current workflow and task."""

import threading
from typing import Any, Optional, TypeVar

T = TypeVar('T')

# Thread-local storage for current workflow and task
_thread_local = threading.local()


def get_current_workflow() -> Optional[Any]:
    """
    Get the current workflow for this thread.
    
    Returns:
    --------
    Optional[Workflow]
        The current workflow or None if not set
    """
    return getattr(_thread_local, 'workflow', None)


def set_current_workflow(workflow: Optional[Any]) -> None:
    """
    Set the current workflow for this thread.
    
    Parameters:
    -----------
    workflow : Optional[Workflow]
        The workflow to set as current or None to clear
    """
    _thread_local.workflow = workflow


def get_current_task() -> Optional[Any]:
    """
    Get the current task for this thread.
    
    Returns:
    --------
    Optional[Task]
        The current task or None if not set
    """
    return getattr(_thread_local, 'task', None)


def set_current_task(task: Optional[Any]) -> None:
    """
    Set the current task for this thread.
    
    Parameters:
    -----------
    task : Optional[Task]
        The task to set as current or None to clear
    """
    _thread_local.task = task
