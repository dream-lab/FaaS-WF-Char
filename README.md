### The Good, the Bad and the Ugly: A Study of FaaS Workflows on Public Clouds

# FaaS Workflow Experiment Artifacts

This repository contains **reproducible experiment artifacts** for characterizing
FaaS workflow platforms across multiple dimensions such as scaling, cold starts,
execution latency, and cost.

## Prerequisite

This repository is a **prerequisite setup** for running experiments using
**XFBench** on your local system.

You must first clone and set up XFBench by following the instructions here:

https://github.com/dream-lab/XFBench

Ensure that:
- XFBench is correctly installed
- Cloud credentials are configured
- Workflows can be deployed and invoked from your local environment

Only after XFBench is working should you proceed with the experiments in this repository.

## Repository Structure

Each experiment category is organized as a **separate directory**.
Each directory will contain:
- Its own `README.md`
- Scripts to run experiments
- Generated plots and logs

## Experiment Scripts

### Script Hierarchy and Organization

The experiment scripts are organized in the `scripts/` directory with a hierarchical structure:

```
scripts/
├── graph/          # Graph processing workflow experiments
├── image/          # Image processing workflow experiments
├── text/           # Text analytics workflow experiments
└── math/           # Math processing workflow experiments
```

Each workflow directory contains **9 shell scripts**, organized by:
- **Cloud Service Provider (CSP)**: AWS, Azure, Azure v2
- **Experiment Type**: Payload experiments, Static scaling, Dynamic experiments

### Script Naming Convention

Scripts follow the naming pattern: `run_{csp}_{experiment_type}_experiments.sh`

- **CSP options**: `aws`, `azure`, `azure_v2`
- **Experiment types**: 
  - `payload` - Payload size variation experiments
  - `static_scaling` - Static RPS scaling experiments
  - `dynamic` - Dynamic workload pattern experiments

### Experiment Types

#### 1. Payload Experiments (`run_*_payload_experiments.sh`)

These scripts test the impact of different payload sizes on workflow performance:
- **Small payload** with 1 RPS
- **Medium payload** with 1 RPS
- **Large payload** with 1 RPS

**Configuration:**
- Duration: 120 seconds
- Dynamism: Static
- Teardown flag: 0 (no teardown between experiments)

#### 2. Static Scaling Experiments (`run_*_static_scaling_experiments.sh`)

These scripts test workflow performance under high static load:
- **148 RPS** with medium payload

**Configuration:**
- Duration: 120 seconds
- Payload size: Medium
- Dynamism: Static
- Teardown flag: 0 (no teardown)

#### 3. Dynamic Experiments (`run_*_dynamic_experiments.sh`)

These scripts test workflow performance under dynamic workload patterns:
- **Step function pattern** at 8 RPS
- **Alibaba trace pattern** at 17 RPS
- **Sorted pattern** at 8 RPS

**Configuration:**
- Duration: 120 seconds
- Payload size: Medium
- Teardown flag: 1 (teardown after each experiment)

### Script Structure

Each script follows a consistent structure:

1. **Shebang and header**: Bash script with descriptive comments
2. **Error handling**: `set -e` to exit on errors
3. **Configuration variable**: `XFBench_DIR=<XFBench_DIR>` - **must be set before running**
4. **Experiment execution**: Sequential execution of benchmark commands
5. **Logging**: Echo statements for progress tracking

### Configuration

**Important**: Before running any script, you must set the `XFBench_DIR` variable to point to your XFBench installation directory.

Edit each script and replace `<XFBench_DIR>` with your actual XFBench path:

```bash
# Example: If XFBench is installed at /home/user/XFBench
XFBench_DIR=/home/user/XFBench
```

### Running Experiments

#### Example: Running All Graph Workflow Experiments

To run all experiments for the **graph workflow**, execute the following scripts in order:

**1. Payload Experiments (AWS):**
```bash
cd scripts/graph
./run_aws_payload_experiments.sh
```

**2. Payload Experiments (Azure):**
```bash
./run_azure_payload_experiments.sh
```

**3. Payload Experiments (Azure v2):**
```bash
./run_azure_v2_payload_experiments.sh
```

**4. Static Scaling Experiments (AWS):**
```bash
./run_aws_static_scaling_experiments.sh
```

**5. Static Scaling Experiments (Azure):**
```bash
./run_azure_static_scaling_experiments.sh
```

**6. Static Scaling Experiments (Azure v2):**
```bash
./run_azure_v2_static_scaling_experiments.sh
```

**7. Dynamic Experiments (AWS):**
```bash
./run_aws_dynamic_experiments.sh
```

**8. Dynamic Experiments (Azure):**
```bash
./run_azure_dynamic_experiments.sh
```

**9. Dynamic Experiments (Azure v2):**
```bash
./run_azure_v2_dynamic_experiments.sh
```

#### Complete Graph Workflow Example

To run all graph workflow experiments sequentially:

```bash
# Navigate to graph workflow directory
cd scripts/graph

# Set XFBench_DIR in all scripts (or use sed for batch update)
# For each script, replace <XFBench_DIR> with your path

# Run all payload experiments
./run_aws_payload_experiments.sh
./run_azure_payload_experiments.sh
./run_azure_v2_payload_experiments.sh

# Run all static scaling experiments
./run_aws_static_scaling_experiments.sh
./run_azure_static_scaling_experiments.sh
./run_azure_v2_static_scaling_experiments.sh

# Run all dynamic experiments
./run_aws_dynamic_experiments.sh
./run_azure_dynamic_experiments.sh
./run_azure_v2_dynamic_experiments.sh
```

### Script Summary

**Total Scripts**: 36 scripts (4 workflows × 3 experiment types × 3 CSPs)

- **Graph workflow**: 9 scripts
- **Image workflow**: 9 scripts
- **Text workflow**: 9 scripts
- **Math workflow**: 9 scripts

Each script is self-contained and can be run independently. All scripts use hardcoded configuration values and require only the `XFBench_DIR` variable to be set.

### Notes

- All scripts use `localhost` as the client key
- Region is set to `centralindia/ap-south-1` (can be modified in scripts if needed)
- Scripts are executable by default
- Each script includes error handling with `set -e`
- Progress messages are printed to stdout for monitoring


