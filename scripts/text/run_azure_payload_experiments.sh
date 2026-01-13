#!/bin/bash

# Payload experiments for text workflow on Azure
# Runs small, medium, large payloads with 1 RPS

set -e

XFBench_DIR=<XFBench_DIR>

echo "Starting Azure payload experiments for text workflow..."

# Small payload, 1 RPS
echo "Running experiment: small payload, 1 RPS"
python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 1 --duration 120 --payload-size small --dynamism static --wf-name text --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/text_analytics_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key localhost

# Medium payload, 1 RPS
echo "Running experiment: medium payload, 1 RPS"
python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 1 --duration 120 --payload-size medium --dynamism static --wf-name text --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/text_analytics_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key localhost

# Large payload, 1 RPS
echo "Running experiment: large payload, 1 RPS"
python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 1 --duration 120 --payload-size large --dynamism static --wf-name text --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/text_analytics_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key localhost

echo "Completed Azure payload experiments for text workflow"

