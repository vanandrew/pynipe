"""Unit tests for the Task class."""

import pytest
from unittest.mock import MagicMock, patch

from pynipe.core.task import Task, TaskOutput


class TestTask:
    """Tests for the Task class."""
    
    def test_init(self):
        """Test Task initialization."""
        task = Task("test_task")
        assert task.name == "test_task"
        assert task.status == "PENDING"
        assert task.inputs == {}
        assert task.outputs == {}
        assert task.dependencies == set()
        
    def test_connect_input(self):
        """Test connecting inputs between tasks."""
        task1 = Task("task1")
        task2 = Task("task2")
        
        task2.connect_input("input1", task1, "output1")
        
        assert len(task2.inputs) == 1
        assert isinstance(task2.inputs["input1"], TaskOutput)
        assert task2.inputs["input1"].task == task1
        assert task2.inputs["input1"].output_name == "output1"
        assert task1 in task2.dependencies
        
    @patch("nipype.interfaces.base.Interface")
    def test_run_success(self, mock_interface_class):
        """Test successful task execution."""
        # Setup mock interface
        mock_interface = MagicMock()
        mock_result = MagicMock()
        mock_result.runtime.cmdline = "test command"
        mock_result.outputs = MagicMock()
        mock_result.outputs.output1 = "output_value"
        
        mock_interface.run.return_value = mock_result
        mock_interface.output_spec().get.return_value = {"output1": None}
        
        # Create task with mock interface
        task = Task("test_task", interface=mock_interface)
        task.inputs = {"input1": "value1"}
        
        # Run task
        outputs = task.run()
        
        # Verify interface was called correctly
        assert mock_interface.inputs.input1 == "value1"
        assert mock_interface.run.called
        
        # Verify outputs were captured
        assert outputs == {"output1": "output_value"}
        assert task.outputs == {"output1": "output_value"}
        assert task.status == "COMPLETE"
        assert task.command == "test command"
        assert task.elapsed_time is not None
        
    @patch("nipype.interfaces.base.Interface")
    def test_run_failure(self, mock_interface_class):
        """Test task execution failure."""
        # Setup mock interface to raise exception
        mock_interface = MagicMock()
        mock_interface.run.side_effect = Exception("Test error")
        
        # Create task with mock interface
        task = Task("test_task", interface=mock_interface)
        
        # Run task and expect exception
        with pytest.raises(Exception, match="Test error"):
            task.run()
            
        # Verify task status
        assert task.status == "FAILED"
        assert task.error is not None
        assert str(task.error) == "Test error"
        assert task.elapsed_time is not None
        
    def test_resolve_inputs(self):
        """Test resolving inputs with dependencies."""
        # Create source task with output
        source_task = Task("source")
        source_task.status = "COMPLETE"
        source_task.outputs = {"output1": "output_value"}
        
        # Create dependent task
        dependent_task = Task("dependent")
        dependent_task.connect_input("input1", source_task, "output1")
        dependent_task.inputs["input2"] = "direct_value"
        
        # Resolve inputs
        resolved = dependent_task._resolve_inputs()
        
        # Verify resolved inputs
        assert resolved == {
            "input1": "output_value",
            "input2": "direct_value"
        }
        
    def test_resolve_inputs_incomplete_dependency(self):
        """Test resolving inputs with incomplete dependency."""
        # Create source task without running
        source_task = Task("source")
        
        # Create dependent task
        dependent_task = Task("dependent")
        dependent_task.connect_input("input1", source_task, "output1")
        
        # Attempt to resolve inputs and expect error
        with pytest.raises(ValueError, match="Dependency source not complete"):
            dependent_task._resolve_inputs()
