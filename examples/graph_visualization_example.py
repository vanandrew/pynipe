"""
Example demonstrating the execution graph visualization in PyNipe.

This example creates a simple workflow with a few tasks and generates
an execution graph visualization to show the task dependencies.
"""

import logging
import os

from nipype.interfaces import fsl

from pynipe import LocalExecutor, TaskContext, Workflow, create_execution_graph

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Define the output directory
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "output"))
os.makedirs(output_dir, exist_ok=True)


def process_with_dependencies(output_dir):
    """
    Create a workflow with multiple tasks and dependencies.

    Parameters:
    -----------
    output_dir : str
        Path to output directory

    Returns:
    --------
    dict
        Processing results
    """
    # Create a dummy input file
    input_file = "/Users/andrew.van/Data/temp/sub-PFM03_ses-01_run-01_desc-preproc_T1w.nii.gz"

    # Task 1: Brain extraction
    with TaskContext("Brain Extraction") as ctx:
        # Create and configure the interface
        bet = fsl.BET()
        ctx.set_interface(bet)

        # Configure the interface parameters
        ctx.configure_interface(
            in_file=input_file,
            out_file=os.path.join(output_dir, "brain.nii.gz"),
            mask=True,
            frac=0.3,
        )

        # Get output proxies for later use
        outputs = ctx.get_output_proxy()
        brain_file = outputs.outputs.out_file  # type: ignore
        mask_file = outputs.outputs.mask_file  # type: ignore

    # Task 2: Threshold the brain mask (depends on brain extraction)
    with TaskContext("Threshold Mask") as ctx:
        # Create and configure the interface
        threshold = fsl.maths.Threshold()
        ctx.set_interface(threshold)

        # Configure the interface parameters - mask_file is a TaskOutput that creates dependency
        ctx.configure_interface(
            in_file=mask_file,  # This creates a dependency on Brain Extraction
            thresh=0.5,
            out_file=os.path.join(output_dir, "mask_thresh.nii.gz"),
        )

        # Get output proxies for later use
        outputs = ctx.get_output_proxy()
        thresholded_mask = outputs.outputs.out_file  # type: ignore

    # Task 3: Smooth the brain (depends on brain extraction)
    with TaskContext("Smooth Brain") as ctx:
        # Create and configure the interface
        smooth = fsl.maths.IsotropicSmooth()
        ctx.set_interface(smooth)

        # Configure the interface parameters
        ctx.configure_interface(
            in_file=brain_file,  # This creates a dependency on Brain Extraction
            fwhm=4.0,
            out_file=os.path.join(output_dir, "brain_smooth.nii.gz"),
        )

        # Get output proxies for later use
        outputs = ctx.get_output_proxy()
        smoothed_brain = outputs.outputs.out_file  # type: ignore

    # Task 4: Calculate statistics (depends on smoothed brain)
    with TaskContext("Calculate Statistics") as ctx:
        # Using the decorator syntax for Python functions
        @ctx.python_function(["stats_file"], smoothed_brain, os.path.join(output_dir, "stats.txt"))
        def calculate_statistics(image_file, output_file):
            """Calculate statistics for an image."""
            # In a real scenario, we would load the image and calculate statistics
            # Here we'll just create a dummy file
            with open(output_file, "w") as f:
                f.write("Mean: 100.0\n")
                f.write("Std: 15.0\n")
                f.write("Min: 50.0\n")
                f.write("Max: 150.0\n")

            return output_file

        # Get output proxy
        outputs = ctx.get_output_proxy()
        stats_file = outputs.outputs.stats_file  # type: ignore

    # Task 5: Generate report (depends on thresholded mask and statistics)
    with TaskContext("Generate Report") as ctx:
        # Using the decorator syntax for Python functions
        @ctx.python_function(
            ["report_file"],
            thresholded_mask,
            stats_file,
            os.path.join(output_dir, "report.html"),
        )
        def generate_report(mask_file, stats_file, output_file):
            """Generate a report from mask and statistics."""
            # In a real scenario, we would generate a proper report
            # Here we'll just create a dummy HTML file
            with open(output_file, "w") as f:
                f.write("<html>\n")
                f.write("<head><title>Processing Report</title></head>\n")
                f.write("<body>\n")
                f.write("<h1>Processing Report</h1>\n")
                f.write(f"<p>Mask file: {mask_file}</p>\n")
                f.write(f"<p>Statistics file: {stats_file}</p>\n")
                f.write("<h2>Statistics</h2>\n")
                f.write("<pre>\n")
                with open(stats_file) as stats:
                    f.write(stats.read())
                f.write("</pre>\n")
                f.write("</body>\n")
                f.write("</html>\n")

            return output_file

        # Get output proxy
        outputs = ctx.get_output_proxy()
        report_file = outputs.outputs.report_file  # type: ignore

    return {
        "brain": brain_file,
        "mask": mask_file,
        "thresholded_mask": thresholded_mask,
        "smoothed_brain": smoothed_brain,
        "stats_file": stats_file,
        "report_file": report_file,
    }


def main():
    """Run the example and generate execution graph."""
    # Create a workflow
    workflow = Workflow("Graph Visualization Example")

    # Add processing function
    workflow.add_function(process_with_dependencies, inputs={"output_dir": output_dir})

    # Run the workflow with parallel execution
    executor = LocalExecutor(max_workers=2)
    results = workflow.run(executor=executor)

    # Create and save execution graph
    graph = create_execution_graph(results)
    graph_file = os.path.join(output_dir, "execution_graph.html")
    graph.to_html(graph_file)

    print(f"Execution graph saved to {graph_file}")
    print("Open this file in a web browser to view the graph.")


if __name__ == "__main__":
    main()
