#!/bin/bash

# Static scaling experiments for math workflow on AWS
# Runs 148 RPS with medium payload

set -e

XFBench_DIR=<XFBench_DIR>

echo "Starting AWS static scaling experiments for math workflow..."

python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp aws --region centralindia --max-rps 148 --duration 120 --payload-size medium --dynamism static --wf-name math --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/math_processing_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key localhost

echo "Completed AWS static scaling experiments for math workflow"

