# Inter-Function Communication Analysis

This directory contains scripts to generate plots for inter-function communication time analysis (Figure 14 in the paper).

## Scripts

- `inter_fn.py`: Generates box plots showing inter-function communication times across all workflows and CSPs.

## Running the Scripts

Before running, set the following variables in the scripts:

- `<PARENT_DIRECTORY_PATH>`: Path to the parent directory containing workflow directories
- `<XFBench_DIR>`: Path to your XFBench installation directory
- `<OUTPUT_DIRECTORY_PATH>`: Path to the output directory where plots will be saved

Example run command:
```bash
python3 inter_fn.py --wf-user-directory <path> --dynamism static --wf graph
```

## Sample Plots

Sample plots from the paper are available in this directory:
- `fig14-interfn.png`: Inter-function communication time analysis plots
