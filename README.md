# PyNipe

[![CI/CD](https://github.com/vanandrew/pynipe/actions/workflows/workflow.yml/badge.svg)](https://github.com/vanandrew/pynipe/actions/workflows/workflow.yml)
[![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://github.com/vanandrew/pynipe)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A neuroimaging workflow library that builds upon Nipype's excellent interfaces while providing a more intuitive and debuggable execution model with support for parallel execution.

## Overview

PyNipe enables neuroimaging researchers to create processing pipelines using natural Python flow, making development and debugging significantly easier while maintaining the ability to run tasks in parallel.

## Key Features

- **Reuse Nipype interfaces**: Leverage the mature interface implementations from Nipype
- **Natural Python flow**: Enable standard Python control structures (if/else, loops, etc.)
- **Improved debugging**: Make it easy to see what's happening at each step
- **Modular processing**: Build pipelines from reusable processing functions
- **Parallel execution**: Support concurrent execution of independent tasks
- **Delayed execution**: Configure tasks first, execute later through the executor
- **Automatic dependency tracking**: Dependencies between tasks are automatically tracked
- **Integration with pipeline tools**: Support modern pipeline management tools like Airflow

## Installation

```bash
pip install pynipe
```

## Basic Usage

```python
from nipype.interfaces import fsl
from pynipe import TaskContext, Workflow, LocalExecutor

# Define a processing function
def process_subject(subject_id, anat_file, output_dir):
    # Brain extraction task
    with TaskContext("Brain Extraction") as ctx:
        # Create and configure the interface
        bet = fsl.BET()
        ctx.set_interface(bet)

        # Configure the interface parameters
        ctx.configure_interface(
            in_file=anat_file,
            out_file=f"{output_dir}/{subject_id}_brain.nii.gz",
            mask=True,
            frac=0.3
        )

        # Get output proxies for later use
        outputs = ctx.get_output_proxy()
        brain_file = outputs.outputs.out_file
        mask_file = outputs.outputs.mask_file

    return {
        "brain": brain_file,
        "mask": mask_file
    }

# Create a workflow
workflow = Workflow("Simple Pipeline")

# Add processing for a subject
workflow.add_function(
    process_subject,
    inputs={
        "subject_id": "sub-01",
        "anat_file": "/path/to/sub-01/anat.nii.gz",
        "output_dir": "/path/to/output"
    }
)

# Run the workflow with parallel execution
executor = LocalExecutor(max_workers=2)
results = workflow.run(executor=executor)

# Access task information after execution
for task_name, task_outputs in results["tasks"].items():
    task = workflow.get_task_by_name(task_name)
    if task:
        print(f"Task: {task_name}")
        print(f"Status: {task.status}")
        print(f"Execution time: {task.elapsed_time:.2f}s")
        print(f"Command: {task.command}")
```

## License

[MIT License](LICENSE)
