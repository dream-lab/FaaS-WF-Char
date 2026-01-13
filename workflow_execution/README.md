# Workflow Execution Analysis

This directory contains scripts to generate plots for workflow execution time breakdown (Figure 15 in the paper).

## Scripts

- `wf_exec.py`: Generates plots showing the breakdown of E2E time into function execution time and inter-function communication time across all workflows and CSPs.

## Running the Scripts

Before running, set the following variables in the scripts:

- `<PARENT_DIRECTORY_PATH>`: Path to the parent directory containing workflow directories
- `<XFBench_DIR>`: Path to your XFBench installation directory

Example run command:
```bash
python3 wf_exec.py --wf-user-directory <path> --dynamism static --wf graph
```

## Sample Plots

Sample plots from the paper are available in this directory:
- `fig15-wf_exec.png`: Workflow execution time breakdown plots
