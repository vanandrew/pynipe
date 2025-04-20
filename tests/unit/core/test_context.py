"""Unit tests for the TaskContext class."""

import pytest
from unittest.mock import patch, MagicMock

from pynipe.core.context import TaskContext
from pynipe.core.task import Task
from pynipe.core.thread_local import get_current_task, get_current_workflow


class TestTaskContext:
    """Tests for the TaskContext class."""
    
    def test_enter_exit(self):
        """Test basic context manager functionality."""
        with TaskContext("test_context") as ctx:
            assert ctx.name == "test_context"
            assert ctx.task is not None
            assert ctx.task.name == "test_context"
            assert get_current_task() == ctx.task
            
        # After exit
        assert get_current_task() is None
        assert ctx.task.status == "COMPLETE"
        assert ctx.task.elapsed_time is not None
        
    def test_workflow_registration(self):
        """Test registration with current workflow."""
        # Setup mock workflow
        with patch("pynipe.core.context.get_current_workflow") as mock_get_workflow:
            mock_workflow = MagicMock()
            mock_get_workflow.return_value = mock_workflow
            
            with TaskContext("test_context") as ctx:
                pass
                
            # Verify task was added to workflow
            mock_workflow.add_task.assert_called_once()
            assert mock_workflow.add_task.call_args[0][0] == ctx.task
        
    def test_exception_handling(self):
        """Test exception handling in context."""
        try:
            with TaskContext("test_context") as ctx:
                raise ValueError("Test error")
        except ValueError:
            # Exception should be propagated
            pass
            
        # Verify task status
        assert ctx.task.status == "FAILED"
        assert ctx.task.error is not None
        assert str(ctx.task.error) == "Test error"
        
    def test_resources(self):
        """Test resource specification."""
        resources = {"cpu": 4, "memory": "8GB"}
        with TaskContext("test_context", resources=resources) as ctx:
            assert ctx.task.resources == resources
