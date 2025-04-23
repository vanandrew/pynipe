"""Unit tests for the TaskContext class."""

from unittest.mock import MagicMock, patch

import pytest

from pynipe.core.context import TaskContext
from pynipe.core.task import OutputProxy
from pynipe.core.thread_local import get_current_task


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
        # Status should not be automatically set to COMPLETE in the new design
        assert ctx.task is not None
        assert ctx.task.status == "PENDING"

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
        assert ctx.task is not None
        assert ctx.task.status == "FAILED"
        assert ctx.task.error is not None
        assert str(ctx.task.error) == "Test error"

    def test_resources(self):
        """Test resource specification."""
        resources = {"cpu": 4, "memory": "8GB"}
        with TaskContext("test_context", resources=resources) as ctx:
            assert ctx.task is not None
            assert ctx.task.resources == resources

    def test_set_interface(self):
        """Test setting interface."""
        mock_interface = MagicMock()

        with TaskContext("test_context") as ctx:
            assert ctx.task is not None
            ctx.set_interface(mock_interface)

            assert ctx.task.interface == mock_interface

    def test_configure_interface(self):
        """Test configuring interface."""
        mock_interface = MagicMock()

        with TaskContext("test_context") as ctx:
            ctx.set_interface(mock_interface)

            # Patch the task's configure_interface method
            with patch.object(ctx.task, "configure_interface") as mock_configure:
                ctx.configure_interface(input1="value1", input2="value2")

                # Verify task's configure_interface was called with correct args
                mock_configure.assert_called_once_with(input1="value1", input2="value2")

    def test_get_output_proxy(self):
        """Test getting output proxy."""
        mock_interface = MagicMock()
        mock_output_spec = MagicMock()
        mock_output_spec.get.return_value = {"output1": None, "output2": None}
        mock_interface.output_spec.return_value = mock_output_spec

        with TaskContext("test_context") as ctx:
            ctx.set_interface(mock_interface)

            # Patch the task's get_output_proxy method
            with patch.object(ctx.task, "get_output_proxy") as mock_get_proxy:
                mock_proxy = MagicMock(spec=OutputProxy)
                mock_get_proxy.return_value = mock_proxy

                proxy = ctx.get_output_proxy()

                # Verify task's get_output_proxy was called
                mock_get_proxy.assert_called_once()
                assert proxy == mock_proxy

    def test_task_not_initialized(self):
        """Test methods when task is not initialized."""
        ctx = TaskContext("test_context")

        with pytest.raises(ValueError, match="Task not initialized"):
            ctx.set_interface(MagicMock())

        with pytest.raises(ValueError, match="Task not initialized"):
            ctx.configure_interface(input1="value1")

        with pytest.raises(ValueError, match="Task not initialized"):
            ctx.get_output_proxy()
