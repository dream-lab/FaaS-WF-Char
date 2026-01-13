#!/bin/bash

# Static scaling experiments for text workflow on AWS
# Runs 148 RPS with medium payload

set -e

XFBench_DIR=<XFBench_DIR>

echo "Starting AWS static scaling experiments for text workflow..."

python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp aws --region centralindia --max-rps 148 --duration 120 --payload-size medium --dynamism static --wf-name text --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/text_analytics_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key localhost

echo "Completed AWS static scaling experiments for text workflow"

