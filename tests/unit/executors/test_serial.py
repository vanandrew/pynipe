"""Unit tests for the SerialExecutor class."""

from unittest.mock import MagicMock

import pytest

from pynipe.core.task import Task
from pynipe.executors.serial import SerialExecutor


class TestSerialExecutor:
    """Tests for the SerialExecutor class."""

    def test_init(self):
        """Test executor initialization."""
        executor = SerialExecutor()
        assert isinstance(executor, SerialExecutor)

    def test_execute_simple(self):
        """Test executing tasks with no dependencies."""
        # Create mock tasks
        task1 = MagicMock(spec=Task)
        task1.name = "task1"
        task1.dependencies = set()
        task1.run.return_value = {"output1": "value1"}

        task2 = MagicMock(spec=Task)
        task2.name = "task2"
        task2.dependencies = set()
        task2.run.return_value = {"output2": "value2"}

        # Execute tasks
        executor = SerialExecutor()
        results = executor.execute([task1, task2])

        # Verify both tasks were run
        task1.run.assert_called_once()
        task2.run.assert_called_once()

        # Verify results
        assert results == {
            "task1": {"output1": "value1"},
            "task2": {"output2": "value2"},
        }

    def test_execute_with_dependencies(self):
        """Test executing tasks with dependencies."""
        # Create mock tasks
        task1 = MagicMock(spec=Task)
        task1.name = "task1"
        task1.dependencies = set()
        task1.run.return_value = {"output1": "value1"}

        task2 = MagicMock(spec=Task)
        task2.name = "task2"
        task2.dependencies = {task1}
        task2.run.return_value = {"output2": "value2"}

        task3 = MagicMock(spec=Task)
        task3.name = "task3"
        task3.dependencies = {task2}
        task3.run.return_value = {"output3": "value3"}

        # Execute tasks
        executor = SerialExecutor()
        results = executor.execute([task3, task1, task2])  # Deliberately out of order

        # Verify tasks were run in correct order
        task1.run.assert_called_once()
        task2.run.assert_called_once()
        task3.run.assert_called_once()

        # Verify results
        assert results == {
            "task1": {"output1": "value1"},
            "task2": {"output2": "value2"},
            "task3": {"output3": "value3"},
        }

    def test_circular_dependencies(self):
        """Test detecting circular dependencies."""
        # Create tasks with circular dependencies
        task1 = MagicMock(spec=Task)
        task1.name = "task1"

        task2 = MagicMock(spec=Task)
        task2.name = "task2"

        # Create circular dependency
        task1.dependencies = {task2}
        task2.dependencies = {task1}

        # Execute tasks and expect error
        executor = SerialExecutor()
        with pytest.raises(ValueError, match="Circular dependencies detected"):
            executor.execute([task1, task2])
