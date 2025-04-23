"""Integration test for a simple workflow."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from pynipe import LocalExecutor, TaskContext, Workflow


class TestSimpleWorkflow:
    """Integration tests for a simple workflow."""

    @patch("nipype.interfaces.base.Interface")
    def test_simple_workflow(self, mock_interface_class):
        """Test a simple workflow with a single task."""
        # Setup mock interface
        mock_interface = MagicMock()
        mock_result = MagicMock()
        mock_result.runtime.cmdline = "test command"
        mock_result.outputs = MagicMock()
        mock_result.outputs.out_file = "/path/to/output.nii.gz"

        mock_interface.run.return_value = mock_result
        mock_interface.output_spec().get.return_value = {"out_file": None}

        # Create a temporary directory for outputs
        with tempfile.TemporaryDirectory() as temp_dir:
            # Define a processing function
            def process_subject(subject_id, input_file, output_dir):
                # Create subject output directory
                subject_dir = os.path.join(output_dir, subject_id)
                os.makedirs(subject_dir, exist_ok=True)

                # Run a task
                with TaskContext("Test Task") as ctx:
                    # Set up the interface
                    ctx.task.interface = mock_interface
                    ctx.task.inputs = {
                        "in_file": input_file,
                        "out_file": os.path.join(subject_dir, "output.nii.gz"),
                    }

                    # Run the task
                    outputs = ctx.task.run()

                    # Return the output file
                    return {"output_file": outputs["out_file"]}

            # Create a workflow
            workflow = Workflow("Test Workflow")

            # Add the processing function
            workflow.add_function(
                process_subject,
                inputs={
                    "subject_id": "sub-01",
                    "input_file": "/path/to/input.nii.gz",
                    "output_dir": temp_dir,
                },
            )

            # Run the workflow
            results = workflow.run(executor=LocalExecutor())

            # Verify the results
            assert "functions" in results
            assert "process_subject" in results["functions"]
            assert results["functions"]["process_subject"]["output_file"] == "/path/to/output.nii.gz"

            # Verify the interface was called correctly
            assert mock_interface.inputs.in_file == "/path/to/input.nii.gz"
            assert "out_file" in mock_interface.inputs.__dict__
            assert mock_interface.run.called
