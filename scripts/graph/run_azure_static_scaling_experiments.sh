#!/bin/bash

# Static scaling experiments for graph workflow on Azure
# Runs 148 RPS with medium payload

set -e

XFBench_DIR=<XFBench_DIR>

echo "Starting Azure static scaling experiments for graph workflow..."

python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 148 --duration 120 --payload-size medium --dynamism static --wf-name graph --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/graph_processing_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key localhost

echo "Completed Azure static scaling experiments for graph workflow"

