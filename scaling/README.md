# Scaling Experiments

This directory contains scripts to generate plots for scaling experiments (Figures 7-8 in the paper).

## Scripts

- `scaling-1.py`: Generates plots for scaling experiments showing E2E time and container count across different RPS levels (1 RPS, 4 RPS, 8 RPS) for all workflows and CSPs.
- `scaling-appendix.py`: Generates appendix plots for scaling experiments with step function dynamism patterns.

## Running the Scripts

Before running, set the following variables in the scripts:

- `<PARENT_DIRECTORY_PATH>`: Path to the parent directory containing workflow directories
- `<XFBench_DIR>`: Path to your XFBench installation directory

Example run command:
```bash
python3 scaling-1.py --wf graph --dynamism static
python3 scaling-appendix.py --wf graph --dynamism workload
```

## Sample Plots

Sample plots from the paper are available in this directory:
- `fig7-scaling.png`: Scaling behavior plots for all workflows
