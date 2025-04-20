"""Core components for PyNipe."""

from .task import Task, TaskOutput
from .context import TaskContext
from .workflow import Workflow
from .thread_local import (
    get_current_workflow,
    set_current_workflow,
    get_current_task,
    set_current_task,
)

__all__ = [
    "Task",
    "TaskOutput",
    "TaskContext",
    "Workflow",
    "get_current_workflow",
    "set_current_workflow",
    "get_current_task",
    "set_current_task",
]
