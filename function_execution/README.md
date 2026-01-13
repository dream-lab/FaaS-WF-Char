# Function Execution Analysis

This directory contains scripts to generate plots for function execution time analysis across different hardware types (Figure 13 in the paper).

## Scripts

- `func_exec.py`: Generates plots showing function execution times across different CPU types and regions for graph and image workflows, including percentage of executions on each hardware type.

## Running the Scripts

Before running, set the following variables in the scripts:

- `<PARENT_DIRECTORY_PATH>`: Path to the parent directory containing cross-region files
- `<OUTPUT_DIRECTORY_PATH>`: Path to the output directory where plots will be saved

The script expects input files:
- `graph_cross_region_files.txt`: List of graph workflow experiment paths
- `image_cross_region_files.txt`: List of image workflow experiment paths

Example run command:
```bash
python3 func_exec.py
```

## Sample Plots

Sample plots from the paper are available in this directory:
- `func_exec.pdf`: Function execution time analysis across hardware types
