# PyNipe

A neuroimaging workflow library that builds upon Nipype's excellent interfaces while providing a more intuitive and debuggable execution model with support for parallel execution.

## Overview

PyNipe enables neuroimaging researchers to create processing pipelines using natural Python flow, making development and debugging significantly easier while maintaining the ability to run tasks in parallel.

## Key Features

- **Reuse Nipype interfaces**: Leverage the mature interface implementations from Nipype
- **Natural Python flow**: Enable standard Python control structures (if/else, loops, etc.)
- **Improved debugging**: Make it easy to see what's happening at each step
- **Modular processing**: Build pipelines from reusable processing functions
- **Parallel execution**: Support concurrent execution of independent tasks
- **Integration with pipeline tools**: Support modern pipeline management tools like Airflow

## Installation

```bash
pip install pynipe
```

## Basic Usage

```python
from nipype.interfaces import fsl
from pynipe import TaskContext

# Simple brain extraction
with TaskContext("Brain Extraction") as ctx:
    bet = fsl.BET(in_file="subject_01.nii.gz", frac=0.3)
    result = bet.run()
    brain_file = result.outputs.out_file
    
# Access task information
print(f"Task status: {ctx.task.status}")
print(f"Execution time: {ctx.task.elapsed_time:.2f}s")
print(f"Command: {ctx.task.command}")
```

## License

[MIT License](LICENSE)
