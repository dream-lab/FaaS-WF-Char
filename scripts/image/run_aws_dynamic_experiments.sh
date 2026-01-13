#!/bin/bash

# Dynamic experiments for image workflow on AWS
# Runs step function, Alibaba, sorted with medium payload

set -e

XFBench_DIR=<XFBench_DIR>

echo "Starting AWS dynamic experiments for image workflow..."

# Step function dynamism
echo "Running experiment: step function dynamism"
python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp aws --region centralindia --max-rps 8 --duration 120 --payload-size medium --dynamism step_function --wf-name image --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/image_processing_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 1 --client-key localhost

# Alibaba dynamism
echo "Running experiment: Alibaba dynamism"
python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp aws --region centralindia --max-rps 17 --duration 120 --payload-size medium --dynamism alibaba --wf-name image --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/image_processing_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 1 --client-key localhost

# Sorted dynamism
echo "Running experiment: sorted dynamism"
python3 ${XFBench_DIR}/serwo/xfaas_run_benchmark.py --csp aws --region centralindia --max-rps 8 --duration 120 --payload-size medium --dynamism sorted --wf-name image --wf-user-directory ${XFBench_DIR}/workflows/custom_workflows/image_processing_wf --path-to-client-config ${XFBench_DIR}/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 1 --client-key localhost

echo "Completed AWS dynamic experiments for image workflow"

