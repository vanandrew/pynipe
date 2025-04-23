"""Unit tests for the Task class."""

from unittest.mock import MagicMock, patch

import pytest

from pynipe.core.task import OutputProxy, Task, TaskOutput


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

    def test_configure_interface(self):
        """Test configuring interface with parameters."""
        # Setup mock interface
        mock_interface = MagicMock()

        # Create task with mock interface
        task = Task("test_task", interface=mock_interface)

        # Configure interface
        task.configure_interface(input1="value1", input2="value2")

        # Verify inputs were stored
        assert task.inputs == {"input1": "value1", "input2": "value2"}

    def test_configure_interface_with_task_output(self):
        """Test configuring interface with TaskOutput."""
        # Create source task
        source_task = Task("source")

        # Create dependent task
        dependent_task = Task("dependent", interface=MagicMock())

        # Create TaskOutput
        task_output = TaskOutput(source_task, "output1")

        # Configure interface with TaskOutput
        dependent_task.configure_interface(input1=task_output)

        # Verify dependency was added
        assert source_task in dependent_task.dependencies
        assert dependent_task.inputs["input1"] == task_output

    def test_get_output_proxy(self):
        """Test getting output proxy."""
        # Setup mock interface
        mock_interface = MagicMock()
        mock_output_spec = MagicMock()
        mock_output_spec.get.return_value = {"output1": None, "output2": None}
        mock_interface.output_spec.return_value = mock_output_spec

        # Create task with mock interface
        task = Task("test_task", interface=mock_interface)

        # Get output proxy
        proxy = task.get_output_proxy()

        # Verify proxy
        assert isinstance(proxy, OutputProxy)
        assert proxy.task == task
        assert hasattr(proxy.outputs, "output1")
        assert hasattr(proxy.outputs, "output2")
        assert isinstance(proxy.outputs.output1, TaskOutput)  # type: ignore
        assert isinstance(proxy.outputs.output2, TaskOutput)  # type: ignore

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
        mock_output_spec = MagicMock()
        mock_output_spec.get.return_value = {"output1": None}
        mock_interface.output_spec.return_value = mock_output_spec

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
        assert resolved == {"input1": "output_value", "input2": "direct_value"}

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


class TestTaskOutput:
    """Tests for the TaskOutput class."""

    def test_init(self):
        """Test TaskOutput initialization."""
        task = Task("test_task")
        output = TaskOutput(task, "output1")

        assert output.task == task
        assert output.output_name == "output1"

    def test_repr(self):
        """Test TaskOutput string representation."""
        task = Task("test_task")
        output = TaskOutput(task, "output1")

        assert repr(output) == "TaskOutput(task=test_task, output=output1)"


class TestOutputProxy:
    """Tests for the OutputProxy class."""

    def test_init_with_interface(self):
        """Test OutputProxy initialization with interface."""
        # Setup mock interface
        mock_interface = MagicMock()
        mock_output_spec = MagicMock()
        mock_output_spec.get.return_value = {"output1": None, "output2": None}
        mock_interface.output_spec.return_value = mock_output_spec

        # Create task with mock interface
        task = Task("test_task", interface=mock_interface)

        # Create output proxy
        proxy = OutputProxy(task)

        # Verify proxy
        assert proxy.task == task
        assert hasattr(proxy.outputs, "output1")
        assert hasattr(proxy.outputs, "output2")
        assert isinstance(proxy.outputs.output1, TaskOutput)  # type: ignore
        assert isinstance(proxy.outputs.output2, TaskOutput)  # type: ignore

    def test_init_without_interface(self):
        """Test OutputProxy initialization without interface."""
        # Create task without interface
        task = Task("test_task")

        # Create output proxy
        proxy = OutputProxy(task)

        # Verify proxy
        assert proxy.task == task
        # No outputs should be created
        assert not hasattr(proxy.outputs, "output1")
