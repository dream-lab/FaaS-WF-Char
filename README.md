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


