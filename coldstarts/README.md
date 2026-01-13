# Cold Starts Experiments

This directory contains scripts to generate plots for cold start analysis (Figures 9-11 in the paper).

## Scripts

- `coldstarts.py`: Generates plots comparing cold start vs warm start execution times across different workflows and CSPs (Azure and Azure v2).

## Running the Scripts

Before running, set the following variables in the scripts:

- `<PARENT_DIRECTORY_PATH>`: Path to the parent directory containing workflow directories
- `<XFBench_DIR>`: Path to your XFBench installation directory

Example run command:
```bash
python3 coldstarts.py --wf-user-directory <path> --dynamism static --wf graph
```

## Sample Plots

Sample plots from the paper are available in this directory:
- `coldstarts-fig9-11.png`: Cold start vs warm start comparison plots
