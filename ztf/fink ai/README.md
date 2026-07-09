# Fink AI: MLflow experiment tracking

These tutorials show how to track model training with [MLflow](https://mlflow.org), from local experimentation to sending a final model to the Fink remote MLflow server.

## Workflow

1. **Experiment locally, without limits.** Run an MLflow server on your own machine and log as many training runs as you want (params, metrics, models, artifacts), with no cost and no impact on shared infrastructure.
2. **Pick a winner.** Compare your local runs in the MLflow UI and select the one you're happy with.
3. **Send only that run to the remote server.** Re-run it against the Fink remote MLflow server, this time also logging the preprocessing code and dependencies so the model is usable in production.

MLflow has no built-in "copy run to another server" feature, so step 3 is a deliberate re-run, not a transfer. See Tutorial 2 for why.

## Notebooks

- [`01_mlflow_local_setup_and_first_run.ipynb`](01_mlflow_local_setup_and_first_run.ipynb): install and start MLflow locally, log your first run, explore the UI, compare multiple runs.
- [`02_send_run_to_remote_server.ipynb`](02_send_run_to_remote_server.ipynb): pick the best local run, retrieve its artifacts, and re-run it on the remote Fink MLflow server.

## Where things are stored

By default, running `mlflow server` locally stores everything in the directory you launch it from:
- `mlruns/`: parameters, metrics, run metadata
- `mlartifacts/`: models, logged data, files

Both tutorials assume you keep using that same directory/port throughout, so you can find your local runs again in Tutorial 2.

## Prerequisites

- Python ≥ 3.9
- MLflow installed (`pip install mlflow`)
- For Tutorial 2: access credentials to the remote MLflow server, set as environment variables (never hardcoded in a notebook)