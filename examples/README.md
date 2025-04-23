# PyNipe Examples

This directory contains example scripts demonstrating how to use PyNipe for neuroimaging workflows.

## Examples

- `simple_pipeline.py`: A simple example demonstrating basic PyNipe usage with a single subject
- `multi_subject_pipeline.py`: An example showing how to process multiple subjects in parallel

## Key Concepts

These examples demonstrate several key concepts in PyNipe:

1. **Delayed Execution**: Tasks are configured first and executed later by the executor
2. **Automatic Dependency Tracking**: Dependencies between tasks are automatically tracked
3. **Output Proxies**: References to outputs that will be available after execution
4. **Workflow Management**: Creating and running workflows with multiple tasks

## Running Examples

To run the examples, you need to have PyNipe installed:

```bash
# Install PyNipe in development mode
pip install -e ..
```

Then you can run the examples:

```bash
python simple_pipeline.py
python multi_subject_pipeline.py
```

## Usage Pattern

The examples follow this pattern for defining tasks:

```python
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
        frac=0.3
    )

    # Get output proxies for later use
    outputs = ctx.get_output_proxy()
    brain_file = outputs.outputs.out_file
    mask_file = outputs.outputs.mask_file
```

This pattern ensures that the interface is not executed immediately, but rather when the task is passed to the executor. Dependencies between tasks are automatically tracked through the `TaskOutput` objects.

## Notes

- These examples use placeholder paths for input data. In a real scenario, you would use actual data files.
- The examples demonstrate the API usage but won't run successfully without actual neuroimaging data and installed neuroimaging tools.
- To run with real data, replace the placeholder paths with actual file paths to your neuroimaging data.

## Example Data

For real usage, you would need:

1. Structural MRI data (T1-weighted images)
2. Functional MRI data (if using functional examples)
3. Installed neuroimaging tools (FSL, AFNI, ANTs, etc.)

## Example Output

The examples will create an `output` directory with:

- Processed neuroimaging data
- Execution graphs visualizing the workflow
