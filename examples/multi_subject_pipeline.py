"""
Multi-subject example of using PyNipe to create a neuroimaging pipeline.

This example demonstrates how to process multiple subjects in parallel using PyNipe.
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


def preprocess_structural(subject_id, anat_file, output_dir):
    """
    Preprocess a subject's structural MRI data.
    
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
    
    # Segmentation task (dependencies auto-detected)
    with TaskContext("Segmentation") as ctx:
        fast = fsl.FAST()
        fast.inputs.in_files = brain_file  # brain_file creates dependency
        fast.inputs.out_basename = os.path.join(subject_dir, f"{subject_id}_seg")
        
        result = fast.run()
        seg_files = result.outputs.tissue_class_files
        
    # Print task information
    print(f"Subject {subject_id} processing complete")
    print(f"Brain extraction time: {ctx.task.elapsed_time:.2f}s")
    
    return {
        "brain": brain_file,
        "mask": mask_file,
        "segmentation": seg_files
    }


def main():
    """Run the example pipeline."""
    # Create a workflow
    workflow = Workflow("Multi-Subject Pipeline")
    
    # Define subjects
    # Note: In a real scenario, you would use actual data files
    subjects = [
        {"id": "sub-01", "anat": "/path/to/sub-01/anat.nii.gz"},
        {"id": "sub-02", "anat": "/path/to/sub-02/anat.nii.gz"},
        {"id": "sub-03", "anat": "/path/to/sub-03/anat.nii.gz"},
    ]
    
    # Add processing for each subject
    for subject in subjects:
        workflow.add_function(
            preprocess_structural,
            inputs={
                "subject_id": subject["id"],
                "anat_file": subject["anat"],
                "output_dir": output_dir
            },
            name=f"preprocess_{subject['id']}"
        )
    
    # Run the workflow with parallel execution (4 concurrent tasks)
    executor = LocalExecutor(max_workers=4)
    results = workflow.run(executor=executor)
    
    # Create and save execution graph
    graph = create_execution_graph(results)
    graph.to_html(os.path.join(output_dir, "multi_subject_execution_graph.html"))
    
    # Access results for each subject
    for subject in subjects:
        subject_id = subject["id"]
        subject_result = results["functions"][f"preprocess_{subject_id}"]
        print(f"Subject {subject_id} brain: {subject_result['brain']}")
        print(f"Subject {subject_id} segmentation: {subject_result['segmentation']}")
    
    print(f"Results saved to {output_dir}")


if __name__ == "__main__":
    main()
