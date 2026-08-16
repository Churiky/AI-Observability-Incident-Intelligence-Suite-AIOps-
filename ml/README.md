# ML Directory

This directory contains machine learning related components.

## Subdirectories

- `training/`: Code, scripts, and notebooks for training machine learning models.
- `evaluation/`: Model evaluation results, metrics, and reports.
- `artifacts/:` Saved models, scalers, and other serialized objects used by the services.

## Usage

The services in `app/services/` (such as `AnomalyDetector` and `SeverityClassifier`) save and load models from the `artifacts/` directory.

Training scripts (e.g., `scripts/train_models.py`) will output trained models to `artifacts/`.

Evaluation scripts can be placed in `evaluation/` to store results.