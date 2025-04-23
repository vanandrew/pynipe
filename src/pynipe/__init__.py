"""
PyNipe: A neuroimaging workflow library that builds upon Nipype's interfaces.

PyNipe provides a more intuitive and debuggable execution model with support for parallel execution.
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"

from .core.context import TaskContext
from .core.task import Task, TaskOutput
from .core.workflow import Workflow
from .executors.local import LocalExecutor
from .executors.serial import SerialExecutor
from .visualization import create_execution_graph

__all__ = [
    "TaskContext",
    "Task",
    "TaskOutput",
    "Workflow",
    "LocalExecutor",
    "SerialExecutor",
    "create_execution_graph",
]
