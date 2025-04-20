# Installing PyNipe

This document provides instructions for installing PyNipe and its dependencies.

## Prerequisites

PyNipe requires:

- Python 3.10 or higher
- Nipype and its dependencies
- FSL, AFNI, ANTs, or other neuroimaging tools (depending on which interfaces you plan to use)

## Installation

### 1. Install Python Dependencies

First, create a virtual environment (recommended):

```bash
# Create a virtual environment
python -m venv pynipe-env

# Activate the virtual environment
# On Linux/Mac:
source pynipe-env/bin/activate
# On Windows:
pynipe-env\Scripts\activate
```

### 2. Install PyNipe

#### From PyPI (recommended for users)

```bash
pip install pynipe
```

#### From Source (recommended for developers)

```bash
# Clone the repository
git clone https://github.com/username/pynipe.git
cd pynipe

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install visualization dependencies
pip install -e ".[visualization]"
```

### 3. Install Neuroimaging Tools

PyNipe uses Nipype interfaces to interact with neuroimaging tools. Depending on which tools you plan to use, you'll need to install them separately:

- **FSL**: [Installation instructions](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation)
- **AFNI**: [Installation instructions](https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/background_install/install_instructs/index.html)
- **ANTs**: [Installation instructions](http://stnava.github.io/ANTs/)
- **FreeSurfer**: [Installation instructions](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall)
- **SPM**: [Installation instructions](https://www.fil.ion.ucl.ac.uk/spm/software/spm12/)

Make sure these tools are properly installed and their binaries are in your system PATH.

## Verifying Installation

To verify that PyNipe is installed correctly, run:

```bash
python -c "import pynipe; print(pynipe.__version__)"
```

This should print the version number of PyNipe.

## Running Tests

To run the tests:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest
```

## Troubleshooting

If you encounter issues with the installation:

1. Make sure your Python version is 3.10 or higher
2. Ensure that Nipype is installed correctly
3. Check that the neuroimaging tools you plan to use are installed and in your PATH
4. If you're installing from source, make sure you have the latest version of pip and setuptools

For more help, please open an issue on the GitHub repository.
