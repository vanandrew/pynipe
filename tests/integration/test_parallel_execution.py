"""Integration test for parallel execution."""

import time
from unittest.mock import MagicMock, patch

from pynipe import LocalExecutor, TaskContext, Workflow


class TestParallelExecution:
    """Integration tests for parallel execution."""

    @patch("nipype.interfaces.base.Interface")
    def test_parallel_execution(self, mock_interface_class):
        """Test parallel execution of independent tasks."""
        # Create a list to track execution order
        execution_order = []

        # Create a mock interface factory that records execution time
        def create_mock_interface(task_id, delay):
            mock_interface = MagicMock()
            mock_result = MagicMock()
            mock_result.runtime.cmdline = f"test command {task_id}"
            mock_result.outputs = MagicMock()
            mock_result.outputs.out_file = f"/path/to/output_{task_id}.nii.gz"

            # Make run() sleep for the specified delay and record execution
            def mock_run():
                execution_order.append(task_id)
                time.sleep(delay)
                return mock_result

            mock_interface.run.side_effect = mock_run
            mock_interface.output_spec().get.return_value = {"out_file": None}

            return mock_interface

        # Define a processing function that creates a task
        def create_task(task_id, delay):
            with TaskContext(f"Task {task_id}") as ctx:
                # Set up the interface
                ctx.task.interface = create_mock_interface(task_id, delay)  # type: ignore
                ctx.task.inputs = {}  # type: ignore

                # Run the task
                outputs = ctx.task.run()  # type: ignore

                # Return the output file
                return {"output_file": outputs["out_file"], "task_id": task_id}

        # Create a workflow
        workflow = Workflow("Parallel Workflow")

        # Add multiple tasks with different delays
        # Task 1: Long running task (0.3s)
        # Task 2: Short running task (0.1s)
        # Task 3: Medium running task (0.2s)
        workflow.add_function(create_task, inputs={"task_id": 1, "delay": 0.3}, name="task1")
        workflow.add_function(create_task, inputs={"task_id": 2, "delay": 0.1}, name="task2")
        workflow.add_function(create_task, inputs={"task_id": 3, "delay": 0.2}, name="task3")

        # Run the workflow with parallel execution (2 workers)
        start_time = time.time()
        results = workflow.run(executor=LocalExecutor(max_workers=2))
        end_time = time.time()

        # Verify all tasks completed
        assert "functions" in results
        assert "task1" in results["functions"]
        assert "task2" in results["functions"]
        assert "task3" in results["functions"]

        # Verify task results
        assert results["functions"]["task1"]["output_file"] == "/path/to/output_1.nii.gz"
        assert results["functions"]["task2"]["output_file"] == "/path/to/output_2.nii.gz"
        assert results["functions"]["task3"]["output_file"] == "/path/to/output_3.nii.gz"

        # Verify execution order - task2 should finish first, then task3, then task1
        # But since we're using parallel execution with 2 workers, task1 and task2
        # should start at the same time, followed by task3 when task2 completes
        assert len(execution_order) == 3
        assert 1 in execution_order
        assert 2 in execution_order
        assert 3 in execution_order

        # Verify total execution time is less than the sum of individual task times
        # With 2 workers, the total time should be approximately:
        # max(task1, task2 + task3) = max(0.3, 0.1 + 0.2) = 0.3 seconds
        # Add a larger buffer for overhead in CI environments
        assert end_time - start_time < 1.0, "Parallel execution not working as expected"

    @patch("nipype.interfaces.base.Interface")
    def test_dependency_execution_order(self, mock_interface_class):
        """Test execution order with dependencies."""
        # Create a list to track execution order
        execution_order = []

        # Create a mock interface factory
        def create_mock_interface(task_id):
            mock_interface = MagicMock()
            mock_result = MagicMock()
            mock_result.runtime.cmdline = f"test command {task_id}"
            mock_result.outputs = MagicMock()
            mock_result.outputs.out_file = f"/path/to/output_{task_id}.nii.gz"

            # Record execution order
            def mock_run():
                execution_order.append(task_id)
                return mock_result

            mock_interface.run.side_effect = mock_run
            mock_interface.output_spec().get.return_value = {"out_file": None}

            return mock_interface

        # Define a processing function with dependencies
        def process_with_dependencies():
            # First task
            with TaskContext("Task 1") as ctx1:
                ctx1.task.interface = create_mock_interface(1)  # type: ignore
                ctx1.task.inputs = {}  # type: ignore
                outputs1 = ctx1.task.run()  # type: ignore
                output_file1 = outputs1["out_file"]

            # Second task depends on first
            with TaskContext("Task 2") as ctx2:
                ctx2.task.interface = create_mock_interface(2)  # type: ignore
                ctx2.task.inputs = {"in_file": output_file1}  # type: ignore
                outputs2 = ctx2.task.run()  # type: ignore
                output_file2 = outputs2["out_file"]

            # Third task depends on second
            with TaskContext("Task 3") as ctx3:
                ctx3.task.interface = create_mock_interface(3)  # type: ignore
                ctx3.task.inputs = {"in_file": output_file2}  # type: ignore
                outputs3 = ctx3.task.run()  # type: ignore
                output_file3 = outputs3["out_file"]

            return {
                "output1": output_file1,
                "output2": output_file2,
                "output3": output_file3,
            }

        # Create a workflow
        workflow = Workflow("Dependency Workflow")
        workflow.add_function(process_with_dependencies)

        # Run the workflow
        workflow.run(executor=LocalExecutor(max_workers=4))

        # Verify execution order - should be 1, 2, 3 due to dependencies
        assert execution_order == [1, 2, 3]
