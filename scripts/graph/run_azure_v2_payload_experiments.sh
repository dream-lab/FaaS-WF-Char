#!/bin/bash

# Payload experiments for graph workflow on Azure v2
# Runs small, medium, large payloads with 1 RPS

set -e

XFBench_DIR=<XFBench_DIR>

echo "Starting Azure v2 payload experiments for graph workflow..."

# Small payload, 1 RPS
echo "Running experiment: small payload, 1 RPS"
python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 120 --payload-size small --dynamism static --wf-name graph --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/graph_processing_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key localhost

# Medium payload, 1 RPS
echo "Running experiment: medium payload, 1 RPS"
python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 120 --payload-size medium --dynamism static --wf-name graph --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/graph_processing_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key localhost

# Large payload, 1 RPS
echo "Running experiment: large payload, 1 RPS"
python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 120 --payload-size large --dynamism static --wf-name graph --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/graph_processing_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key localhost

echo "Completed Azure v2 payload experiments for graph workflow"

