"""
Example training script template for AirBench experiments.

This script demonstrates how to structure your training code to work
with the AirBench experiment tracker.

Usage:
    python example_train.py \
        --base-model meta-llama/Llama-2-7b-hf \
        --dataset /path/to/dataset.json \
        --experiment-id 1 \
        --learning_rate 2e-5 \
        --num_epochs 3 \
        --batch_size 8
"""

import argparse
import json
import time
import requests
from typing import Dict, Any


class ExperimentLogger:
    """Helper class to log metrics back to AirBench"""

    def __init__(self, experiment_id: int, api_url: str = "http://localhost:8000"):
        self.experiment_id = experiment_id
        self.api_url = api_url

    def log_metric(
        self,
        step: int,
        metric_name: str,
        metric_value: float,
        phase: str = "train"
    ):
        """Log a single metric to the experiment tracker"""
        try:
            response = requests.post(
                f"{self.api_url}/experiments/{self.experiment_id}/metrics",
                json={
                    "experiment_id": self.experiment_id,
                    "step": step,
                    "phase": phase,
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                }
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Warning: Failed to log metric: {e}")


def load_dataset(dataset_path: str) -> list:
    """Load dataset from JSON or CSV"""
    with open(dataset_path, 'r') as f:
        if dataset_path.endswith('.json'):
            return json.load(f)
        else:
            import csv
            reader = csv.DictReader(f)
            return list(reader)


def train(
    base_model: str,
    dataset_path: str,
    experiment_id: int,
    hyperparameters: Dict[str, Any]
):
    """
    Main training function.

    In a real implementation, this would:
    1. Load the base model
    2. Load and preprocess the dataset
    3. Set up the training loop
    4. Log metrics at each step
    5. Save checkpoints
    6. Return final metrics
    """
    print(f"Starting training for experiment {experiment_id}")
    print(f"Base model: {base_model}")
    print(f"Dataset: {dataset_path}")
    print(f"Hyperparameters: {hyperparameters}")

    # Initialize logger
    logger = ExperimentLogger(experiment_id)

    # Load dataset
    print("\nLoading dataset...")
    dataset = load_dataset(dataset_path)
    print(f"Loaded {len(dataset)} samples")

    # Extract hyperparameters
    learning_rate = float(hyperparameters.get('learning_rate', 2e-5))
    num_epochs = int(hyperparameters.get('num_epochs', 3))
    batch_size = int(hyperparameters.get('batch_size', 8))

    print(f"\nTraining configuration:")
    print(f"  Learning rate: {learning_rate}")
    print(f"  Epochs: {num_epochs}")
    print(f"  Batch size: {batch_size}")

    # Simulate training
    print("\n" + "="*50)
    print("SIMULATED TRAINING (Replace with real training code)")
    print("="*50 + "\n")

    total_steps = (len(dataset) // batch_size) * num_epochs
    step = 0

    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")
        print("-" * 40)

        # Simulate batches
        num_batches = len(dataset) // batch_size
        for batch_idx in range(num_batches):
            step += 1

            # Simulate training loss (decreasing over time)
            train_loss = 2.5 * (1 - (step / total_steps)) + 0.3

            # Log training loss
            logger.log_metric(
                step=step,
                metric_name="train_loss",
                metric_value=train_loss,
                phase="train"
            )

            # Print progress
            if step % 10 == 0:
                print(f"Step {step}/{total_steps} - Loss: {train_loss:.4f}")

            # Simulate processing time
            time.sleep(0.1)

        # Validation at end of epoch
        val_loss = 2.0 * (1 - (epoch / num_epochs)) + 0.5
        val_accuracy = 0.4 + (0.5 * (epoch / num_epochs))

        logger.log_metric(
            step=step,
            metric_name="val_loss",
            metric_value=val_loss,
            phase="eval"
        )

        logger.log_metric(
            step=step,
            metric_name="val_accuracy",
            metric_value=val_accuracy,
            phase="eval"
        )

        print(f"\nEpoch {epoch + 1} validation:")
        print(f"  Val Loss: {val_loss:.4f}")
        print(f"  Val Accuracy: {val_accuracy:.4f}")

    # Final evaluation
    print("\n" + "="*50)
    print("FINAL EVALUATION")
    print("="*50)

    final_loss = 0.3
    final_accuracy = 0.92

    logger.log_metric(
        step=step,
        metric_name="test_loss",
        metric_value=final_loss,
        phase="final"
    )

    logger.log_metric(
        step=step,
        metric_name="test_accuracy",
        metric_value=final_accuracy,
        phase="final"
    )

    print(f"\nFinal test metrics:")
    print(f"  Test Loss: {final_loss:.4f}")
    print(f"  Test Accuracy: {final_accuracy:.4f}")

    print("\n✓ Training complete!")


def main():
    parser = argparse.ArgumentParser(description="Train a language model")
    parser.add_argument("--base-model", required=True, help="Base model to fine-tune")
    parser.add_argument("--dataset", required=True, help="Path to dataset file")
    parser.add_argument("--experiment-id", type=int, required=True, help="Experiment ID")

    # Hyperparameters
    parser.add_argument("--learning_rate", default="2e-5", help="Learning rate")
    parser.add_argument("--num_epochs", default="3", help="Number of epochs")
    parser.add_argument("--batch_size", default="8", help="Batch size")

    args = parser.parse_args()

    # Collect hyperparameters
    hyperparameters = {
        'learning_rate': args.learning_rate,
        'num_epochs': args.num_epochs,
        'batch_size': args.batch_size,
    }

    # Add any other arguments as hyperparameters
    for key, value in vars(args).items():
        if key not in ['base_model', 'dataset', 'experiment_id'] and value is not None:
            if key not in hyperparameters:
                hyperparameters[key] = value

    try:
        train(
            base_model=args.base_model,
            dataset_path=args.dataset,
            experiment_id=args.experiment_id,
            hyperparameters=hyperparameters
        )
    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
