"""
Simple example of using PyNipe to create a neuroimaging pipeline.

This example demonstrates the basic usage of PyNipe with a simple brain extraction task.
"""

import logging
import os

from nipype.interfaces import fsl

from pynipe import SerialExecutor, TaskContext, Workflow, create_execution_graph

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Define the output directory
output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)


def process_subject(subject_id, anat_file, output_dir):
    """
    Process a single subject's anatomical image.

    Parameters:
    -----------
    subject_id : str
        Subject identifier
    anat_file : str
        Path to anatomical image
    output_dir : str
        Path to output directory

    Returns:
    --------
    dict
        Processing results
    """
    # Create subject output directory
    subject_dir = os.path.join(output_dir, subject_id)
    os.makedirs(subject_dir, exist_ok=True)

    # Brain extraction task
    with TaskContext("Brain Extraction") as ctx:
        # Create and configure the interface
        bet = fsl.BET()
        ctx.set_interface(bet)

        # Configure the interface parameters
        ctx.configure_interface(
            in_file=anat_file,
            out_file=os.path.join(subject_dir, f"{subject_id}_brain.nii.gz"),
            mask=True,
            frac=0.3,
        )

        # Get output proxies for later use
        outputs = ctx.get_output_proxy()
        # We're using TaskOutput objects that will be resolved during execution
        brain_file = outputs.outputs.out_file  # type: ignore
        mask_file = outputs.outputs.mask_file  # type: ignore

    return {"brain": brain_file, "mask": mask_file}


def main():
    """Run the example pipeline."""
    # Create a workflow
    workflow = Workflow("Simple Pipeline")

    # Add processing for a subject
    # Note: In a real scenario, you would use actual data files
    workflow.add_function(
        process_subject,
        inputs={
            "subject_id": "sub-01",
            "anat_file": "/path/to/sub-01/anat.nii.gz",
            "output_dir": output_dir,
        },
    )

    # Choose an executor based on your needs:

    # Option 1: Parallel execution with multiple workers
    # executor = LocalExecutor(max_workers=2)

    # Option 2: Serial execution (one task at a time)
    executor = SerialExecutor()

    # Run the workflow
    results = workflow.run(executor=executor)

    # After execution, we can access the task information
    for task_name, task_outputs in results["tasks"].items():
        task = workflow.get_task_by_name(task_name)
        if task:
            print(f"Task: {task_name}")
            print(f"Status: {task.status}")
            print(f"Execution time: {task.elapsed_time:.2f}s")
            print(f"Command: {task.command}")
            print(f"Outputs: {task_outputs}")
            print()

    # Create and save execution graph
    graph = create_execution_graph(results)
    graph.to_html(os.path.join(output_dir, "execution_graph.html"))

    print(f"Results saved to {output_dir}")


if __name__ == "__main__":
    main()
