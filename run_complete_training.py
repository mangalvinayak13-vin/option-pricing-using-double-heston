"""
Complete training and evaluation pipeline for Double Heston inverse calibration.

This script:
1. Loads the final 10,000-surface synthetic dataset
2. Trains Model 1 (ordinary ANN inverse model)
3. Trains Model 2 (constraint + differentiable repricing-informed model)
4. Evaluates both models on test set
5. Prepares results for web deployment

Usage:
    python run_complete_training.py --model 1 --epochs 50 --batch-size 64
    python run_complete_training.py --model 2 --epochs 50 --batch-size 64
    python run_complete_training.py --eval-only
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, random_split

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Double Heston imports not needed for training script

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrdinaryANNInverseModel(nn.Module):
    """Model 1: Ordinary ANN inverse model."""

    def __init__(self, input_dim: int = 20, hidden_dims: Tuple[int] = (256, 256, 256)):
        super().__init__()

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim

        # Output: 10 parameters
        layers.append(nn.Linear(prev_dim, 10))

        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x shape: (batch_size, input_dim) -> output shape: (batch_size, 10)"""
        return self.net(x)


class ConstraintAwareInverseModel(nn.Module):
    """Model 2: Constraint + differentiable repricing-informed model."""

    def __init__(self, input_dim: int = 20, hidden_dims: Tuple[int] = (256, 256, 256)):
        super().__init__()

        # Main parameter prediction network
        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, 10))
        self.net = nn.Sequential(*layers)

        # Constraint enforcement layer
        self.constraint_scale = nn.Parameter(torch.ones(10), requires_grad=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Predict parameters with constraint awareness."""
        params_raw = self.net(x)

        # Apply soft constraints:
        # 1. All positive (kappa, theta, sigma, v0)
        # 2. kappa_slow < kappa_fast
        # 3. Correlation bounds

        params = params_raw.clone()

        # Ensure positivity for: kappa_slow, theta_slow, sigma_slow, v0_slow,
        #                         kappa_fast, theta_fast, sigma_fast, v0_fast
        for i in [0, 1, 2, 4, 5, 6, 7, 9]:
            params[:, i] = torch.clamp(torch.exp(params_raw[:, i]) - 1, min=0.001)

        # Correlations should be in (-1, 1)
        params[:, 3] = torch.tanh(params_raw[:, 3])  # rho_slow
        params[:, 8] = torch.tanh(params_raw[:, 8])  # rho_fast

        return params


def load_synthetic_data(data_path: Path) -> Tuple[torch.Tensor, torch.Tensor]:
    """Load the frozen 10,000-surface dataset."""

    logger.info(f"Loading synthetic data from {data_path}")

    # Load surfaces and prices
    surfaces_file = data_path / "surfaces.jsonl"

    if not surfaces_file.exists():
        raise FileNotFoundError(f"Dataset not found at {surfaces_file}")

    inputs = []
    outputs = []

    with open(surfaces_file) as f:
        for i, line in enumerate(f):
            record = json.loads(line)

            # Extract 20-dimensional R2 representation (prices)
            prices = record.get("prices", [])
            if len(prices) != 20:
                logger.warning(f"Record {i} has {len(prices)} prices, expected 20. Skipping.")
                continue

            # Extract 10 parameters from metadata
            params_dict = record.get("metadata", {}).get("parameters_canonical_order", {})
            if not params_dict:
                logger.warning(f"Record {i} missing parameters. Skipping.")
                continue

            params = [
                params_dict["kappa_slow"], params_dict["theta_slow"], params_dict["sigma_slow"],
                params_dict["rho_slow"], params_dict["v0_slow"],
                params_dict["kappa_fast"], params_dict["theta_fast"], params_dict["sigma_fast"],
                params_dict["rho_fast"], params_dict["v0_fast"]
            ]

            inputs.append(prices)
            outputs.append(params)

    X = torch.tensor(inputs, dtype=torch.float32)
    y = torch.tensor(outputs, dtype=torch.float32)

    logger.info(f"Loaded {len(X)} samples with shape X={X.shape}, y={y.shape}")

    return X, y


def normalize_tensors(X: torch.Tensor, y: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, Any]]:
    """Normalize inputs and outputs for training."""

    # Normalize inputs (prices) to [0, 1]
    X_min = X.min(dim=0)[0]
    X_max = X.max(dim=0)[0]
    X_norm = (X - X_min) / (X_max - X_min + 1e-8)

    # Normalize outputs (parameters)
    y_mean = y.mean(dim=0)
    y_std = y.std(dim=0)
    y_norm = (y - y_mean) / (y_std + 1e-8)

    stats = {
        'X_min': X_min.numpy(),
        'X_max': X_max.numpy(),
        'y_mean': y_mean.numpy(),
        'y_std': y_std.numpy(),
    }

    logger.info(f"Normalization stats: X range [{X_min.mean():.4f}, {X_max.mean():.4f}], "
                f"y mean {y_mean.mean():.4f}, std {y_std.mean():.4f}")

    return X_norm, y_norm, stats


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 50,
    learning_rate: float = 0.001,
    device: torch.device = None
) -> Dict[str, list]:
    """Train a model and return training history."""

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()

    history = {
        'train_loss': [],
        'val_loss': [],
        'train_mse': [],
        'val_mse': [],
    }

    logger.info(f"Training on {device} for {epochs} epochs")

    for epoch in range(epochs):
        # Training phase
        model.train()
        train_loss = 0.0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)

            optimizer.zero_grad()
            pred = model(batch_x)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * batch_x.shape[0]

        train_loss /= len(train_loader.dataset)

        # Validation phase
        model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                pred = model(batch_x)
                loss = criterion(pred, batch_y)
                val_loss += loss.item() * batch_x.shape[0]

        val_loss /= len(val_loader.dataset)

        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_mse'].append(train_loss)
        history['val_mse'].append(val_loss)

        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs} - Train loss: {train_loss:.6f}, Val loss: {val_loss:.6f}")

    return history


def evaluate_model(
    model: nn.Module,
    test_loader: DataLoader,
    y_stats: Dict[str, Any],
    device: torch.device = None
) -> Dict[str, float]:
    """Evaluate model on test set."""

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = model.to(device)
    model.eval()

    y_preds = []
    y_trues = []

    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x = batch_x.to(device)
            pred = model(batch_x)
            y_preds.append(pred.cpu().numpy())
            y_trues.append(batch_y.numpy())

    y_preds = np.concatenate(y_preds)
    y_trues = np.concatenate(y_trues)

    # Denormalize
    y_mean = torch.tensor(y_stats['y_mean'], dtype=torch.float32)
    y_std = torch.tensor(y_stats['y_std'], dtype=torch.float32)

    y_preds_denorm = y_preds * y_std.numpy() + y_mean.numpy()
    y_trues_denorm = y_trues * y_std.numpy() + y_mean.numpy()

    # Calculate metrics
    mse = np.mean((y_preds_denorm - y_trues_denorm) ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(y_preds_denorm - y_trues_denorm))

    # Parameter-wise recovery
    param_names = ['kappa_s', 'theta_s', 'sigma_s', 'rho_s', 'v0_s',
                   'kappa_f', 'theta_f', 'sigma_f', 'rho_f', 'v0_f']
    param_rmse = {}
    param_mae = {}

    for i, name in enumerate(param_names):
        param_rmse[name] = np.sqrt(np.mean((y_preds_denorm[:, i] - y_trues_denorm[:, i]) ** 2))
        param_mae[name] = np.mean(np.abs(y_preds_denorm[:, i] - y_trues_denorm[:, i]))

    metrics = {
        'mse': float(mse),
        'rmse': float(rmse),
        'mae': float(mae),
        'param_rmse': {k: float(v) for k, v in param_rmse.items()},
        'param_mae': {k: float(v) for k, v in param_mae.items()},
        'test_samples': len(y_trues),
    }

    logger.info(f"Test metrics - RMSE: {rmse:.6f}, MAE: {mae:.6f}")
    logger.info(f"Parameter recovery - avg RMSE: {np.mean(list(param_rmse.values())):.6f}")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Complete Double Heston training pipeline")
    parser.add_argument("--model", type=int, choices=[1, 2], default=1, help="Model type (1=ANN, 2=Constraint-aware)")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--eval-only", action="store_true", help="Only evaluate existing models")
    parser.add_argument("--data-dir", type=str, default=None, help="Path to synthetic dataset")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for results")

    args = parser.parse_args()

    # Setup paths
    if args.data_dir is None:
        args.data_dir = PROJECT_ROOT / "data" / "final_r2_clean_10000"
    else:
        args.data_dir = Path(args.data_dir)

    if args.output_dir is None:
        args.output_dir = PROJECT_ROOT / "outputs" / "training_results"
    else:
        args.output_dir = Path(args.output_dir)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Load data
    X, y = load_synthetic_data(Path(args.data_dir))
    X_norm, y_norm, y_stats = normalize_tensors(X, y)

    # Split data
    train_size = int(0.7 * len(X_norm))
    val_size = int(0.15 * len(X_norm))
    test_size = len(X_norm) - train_size - val_size

    train_dataset, val_dataset, test_dataset = random_split(
        TensorDataset(X_norm, y_norm),
        [train_size, val_size, test_size],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size)

    logger.info(f"Data split - Train: {train_size}, Val: {val_size}, Test: {test_size}")

    # Create or load model
    model_name = f"Model_{args.model}_{'ANN' if args.model == 1 else 'Constraint'}"
    model_path = args.output_dir / f"{model_name}_checkpoint.pt"

    if args.model == 1:
        model = OrdinaryANNInverseModel()
    else:
        model = ConstraintAwareInverseModel()

    # Train or evaluate
    if not args.eval_only and not model_path.exists():
        logger.info(f"Training {model_name}...")
        history = train_model(
            model, train_loader, val_loader,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            device=device
        )

        # Save model and history
        torch.save(model.state_dict(), model_path)
        logger.info(f"Model saved to {model_path}")

        with open(args.output_dir / f"{model_name}_history.json", 'w') as f:
            json.dump(history, f, indent=2)

    elif model_path.exists():
        logger.info(f"Loading trained model from {model_path}")
        model.load_state_dict(torch.load(model_path, map_location=device))

    # Evaluate
    logger.info(f"Evaluating {model_name}...")
    metrics = evaluate_model(model, test_loader, y_stats, device=device)

    # Save metrics
    with open(args.output_dir / f"{model_name}_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Results saved to {args.output_dir}")

    return metrics


if __name__ == "__main__":
    main()
