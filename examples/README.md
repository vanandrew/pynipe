# PyNipe Examples

This directory contains example scripts demonstrating how to use PyNipe for neuroimaging workflows.

## Examples

- `simple_pipeline.py`: A simple example demonstrating basic PyNipe usage with a single subject
- `multi_subject_pipeline.py`: An example showing how to process multiple subjects in parallel

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
