"""Unit tests for the Workflow class."""

import pytest
from unittest.mock import patch, MagicMock

from pynipe.core.workflow import Workflow
from pynipe.core.task import Task


class TestWorkflow:
    """Tests for the Workflow class."""
    
    def test_init(self):
        """Test workflow initialization."""
        workflow = Workflow("test_workflow")
        assert workflow.name == "test_workflow"
        assert workflow.tasks == []
        assert workflow.functions == []
        
    def test_add_task(self):
        """Test adding a task to the workflow."""
        workflow = Workflow("test_workflow")
        task = Task("test_task")
        
        workflow.add_task(task)
        
        assert len(workflow.tasks) == 1
        assert workflow.tasks[0] == task
        
    def test_add_function(self):
        """Test adding a function to the workflow."""
        workflow = Workflow("test_workflow")
        
        def test_func(a, b):
            return a + b
            
        workflow.add_function(test_func, inputs={"a": 1, "b": 2}, name="custom_name")
        
        assert len(workflow.functions) == 1
        assert workflow.functions[0]["name"] == "custom_name"
        assert workflow.functions[0]["function"] == test_func
        assert workflow.functions[0]["inputs"] == {"a": 1, "b": 2}
        
    @patch("pynipe.executors.local.LocalExecutor")
    @patch("pynipe.core.thread_local.set_current_workflow")
    def test_run(self, mock_set_workflow, mock_executor_class):
        """Test running the workflow."""
        # Setup mock executor
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        mock_executor.execute.return_value = {"task1": {"output1": "value1"}}
        
        # Setup test function
        def test_func(a, b):
            return a + b
            
        # Create workflow
        workflow = Workflow("test_workflow")
        workflow.add_function(test_func, inputs={"a": 1, "b": 2})
        
        # Add a task
        task = Task("task1")
        workflow.add_task(task)
        
        # Run workflow
        results = workflow.run()
        
        # Verify function was executed
        assert results["functions"]["test_func"] == 3
        
        # Verify executor was called with tasks
        mock_executor.execute.assert_called_once_with([task])
        
        # Verify task results were returned
        assert results["tasks"] == {"task1": {"output1": "value1"}}
        
    def test_to_airflow_not_implemented(self):
        """Test that to_airflow raises NotImplementedError."""
        workflow = Workflow("test_workflow")
        
        with pytest.raises(NotImplementedError):
            workflow.to_airflow("test.py")
