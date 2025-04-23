"""
Multi-subject example of using PyNipe to create a neuroimaging pipeline.

This example demonstrates how to process multiple subjects in parallel using PyNipe,
including parallel tasks, non-nipype Python tasks, and dependency tracking.
"""

import logging
import os

import nibabel as nib
import numpy as np
from nipype.interfaces import ants, fsl

from pynipe import LocalExecutor, TaskContext, Workflow, create_execution_graph

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Define the output directory
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "output"))
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
        brain_file = outputs.outputs.out_file  # type: ignore
        mask_file = outputs.outputs.mask_file  # type: ignore

    # Bias field correction task (runs in parallel with brain extraction)
    with TaskContext("Bias Field Correction") as ctx:
        # Create and configure the interface
        bias_correct = ants.N4BiasFieldCorrection()
        ctx.set_interface(bias_correct)

        # Configure the interface parameters
        ctx.configure_interface(
            input_image=anat_file,  # Original anatomical image, no dependency on brain extraction
            output_image=os.path.join(subject_dir, f"{subject_id}_bias_corrected.nii.gz"),
            dimension=3,
            shrink_factor=4,
            n_iterations=[50, 50, 30, 20],
        )

        # Get output proxies for later use
        outputs = ctx.get_output_proxy()
        bias_corrected_file = outputs.outputs.output_image  # type: ignore

    # Threshold the brain mask using fslmaths (depends on brain extraction)
    with TaskContext("Threshold Mask") as ctx:
        # Create and configure the interface
        threshold = fsl.maths.Threshold()
        ctx.set_interface(threshold)

        # Configure the interface parameters - mask_file is a TaskOutput that creates dependency
        ctx.configure_interface(
            in_file=mask_file,
            thresh=0.5,
            out_file=os.path.join(subject_dir, f"{subject_id}_mask_thresh.nii.gz"),
        )

        # Get output proxies for later use
        outputs = ctx.get_output_proxy()
        thresholded_mask = outputs.outputs.out_file  # type: ignore

    # Pure Python task to calculate brain volume (depends on thresholded mask)
    volume_report_file = os.path.join(subject_dir, f"{subject_id}_brain_volume.txt")

    with TaskContext("Calculate Brain Volume") as ctx:
        # Using the new decorator syntax for Python functions
        @ctx.python_function(["output_file"], thresholded_mask, volume_report_file)
        def calculate_brain_volume(mask_file, output_file):
            """Calculate brain volume from a binary mask."""
            # Load the mask file
            mask_img = nib.load(mask_file)  # type: ignore
            mask_data = mask_img.get_fdata()  # type: ignore

            # Get voxel dimensions
            voxel_dims = mask_img.header.get_zooms()  # type: ignore
            voxel_volume = voxel_dims[0] * voxel_dims[1] * voxel_dims[2]

            # Count non-zero voxels and calculate volume
            voxel_count = np.count_nonzero(mask_data)
            volume_mm3 = voxel_count * voxel_volume
            volume_cm3 = volume_mm3 / 1000.0

            # Save results to a text file
            with open(output_file, "w") as f:
                f.write(f"Brain Volume Analysis for {subject_id}\n")
                f.write(f"Voxel dimensions (mm): {voxel_dims}\n")
                f.write(f"Voxel volume (mm³): {voxel_volume:.2f}\n")
                f.write(f"Voxel count: {voxel_count}\n")
                f.write(f"Brain volume (mm³): {volume_mm3:.2f}\n")
                f.write(f"Brain volume (cm³): {volume_cm3:.2f}\n")

            return output_file

        # Get output proxy
        outputs = ctx.get_output_proxy()
        volume_report = outputs.outputs.output_file  # type: ignore

    return {
        "brain": brain_file,
        "mask": mask_file,
        "bias_corrected": bias_corrected_file,
        "thresholded_mask": thresholded_mask,
        "volume_report": volume_report,
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
                "output_dir": output_dir,
            },
            name=f"preprocess_{subject['id']}",
        )

    # Choose an executor based on your needs:

    # Option 1: Parallel execution with multiple workers
    executor = LocalExecutor(max_workers=4)

    # Option 2: Serial execution (one task at a time)
    # executor = SerialExecutor()

    # Run the workflow
    results = workflow.run(executor=executor)

    # After execution, we can access the task information
    for task_name, _ in results["tasks"].items():
        task = workflow.get_task_by_name(task_name)
        if task:
            print(f"Task: {task_name}")
            print(f"Status: {task.status}")
            print(f"Execution time: {task.elapsed_time:.2f}s")
            print(f"Command: {task.command}")
            print()

    # Create and save execution graph
    graph = create_execution_graph(results)
    graph.to_html(os.path.join(output_dir, "multi_subject_execution_graph.html"))

    # Access results for each subject
    for subject in subjects:
        subject_id = subject["id"]
        subject_result = results["functions"][f"preprocess_{subject_id}"]
        print(f"Subject {subject_id} brain: {subject_result['brain']}")
        print(f"Subject {subject_id} bias corrected: {subject_result['bias_corrected']}")
        print(f"Subject {subject_id} brain volume: {subject_result['volume_report']}")
        print()

    print(f"Results saved to {output_dir}")


if __name__ == "__main__":
    main()
