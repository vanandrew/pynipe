"""
Simple example of using PyNipe to create a neuroimaging pipeline.

This example demonstrates the basic usage of PyNipe with a simple brain extraction task.
"""

import os
import logging
from nipype.interfaces import fsl
from pynipe import TaskContext, Workflow, LocalExecutor, create_execution_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        bet = fsl.BET()
        bet.inputs.in_file = anat_file
        bet.inputs.out_file = os.path.join(subject_dir, f"{subject_id}_brain.nii.gz")
        bet.inputs.mask = True
        bet.inputs.frac = 0.3
        
        result = bet.run()
        brain_file = result.outputs.out_file
        mask_file = result.outputs.mask_file
    
    # Print task information
    print(f"Task status: {ctx.task.status}")
    print(f"Execution time: {ctx.task.elapsed_time:.2f}s")
    print(f"Command: {ctx.task.command}")
    
    return {
        "brain": brain_file,
        "mask": mask_file
    }


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
            "output_dir": output_dir
        }
    )
    
    # Run the workflow with parallel execution (2 concurrent tasks)
    executor = LocalExecutor(max_workers=2)
    results = workflow.run(executor=executor)
    
    # Create and save execution graph
    graph = create_execution_graph(results)
    graph.to_html(os.path.join(output_dir, "execution_graph.html"))
    
    print(f"Results saved to {output_dir}")


if __name__ == "__main__":
    main()
