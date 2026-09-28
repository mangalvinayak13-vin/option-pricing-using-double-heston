"""
Double Heston web integration for Streamlit Physics project SEM 1.

This module provides functions to display Double Heston inverse calibration results
in the Streamlit web interface.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class DoubleHestonWebIntegration:
    """Integration layer for Double Heston results in web interface."""

    def __init__(self, results_dir: Path):
        """Initialize with path to training results directory."""
        self.results_dir = Path(results_dir)
        self.models_info = {}
        self._load_model_results()

    def _load_model_results(self):
        """Load model training results."""
        for metrics_file in sorted(self.results_dir.glob("*_metrics.json")):
            model_name = metrics_file.name[: -len("_metrics.json")]

            history_file = self.results_dir / f"{model_name}_history.json"

            with open(metrics_file) as f:
                metrics = json.load(f)

            if history_file.exists():
                with open(history_file) as f:
                    history = json.load(f)
            else:
                history = {}

            self.models_info[model_name] = {
                'metrics': metrics,
                'history': history,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Loaded results for {model_name}")

    def get_model_comparison(self) -> Dict:
        """Get comparison metrics across all trained models."""

        comparison = {
            'models': [],
            'metrics_summary': {},
        }

        for model_name, data in self.models_info.items():
            metrics = data['metrics']

            if metrics:
                comparison['models'].append({
                    'name': model_name,
                    'rmse': metrics.get('rmse', None),
                    'mae': metrics.get('mae', None),
                    'mse': metrics.get('mse', None),
                    'mean_skill': metrics.get('mean_skill', None),
                    'param_skill': metrics.get('param_skill', {}),
                    'test_samples': metrics.get('test_samples', 0),
                })

                # Track param-wise recovery
                if 'param_rmse' in metrics:
                    if model_name not in comparison['metrics_summary']:
                        comparison['metrics_summary'][model_name] = {}

                    for param, rmse in metrics['param_rmse'].items():
                        comparison['metrics_summary'][model_name][param] = rmse

        return comparison

    def get_training_history(self, model_name: str) -> Optional[Dict]:
        """Get training history for a specific model."""
        if model_name in self.models_info:
            return self.models_info[model_name]['history']
        return None

    def get_model_details(self, model_name: str) -> Dict:
        """Get detailed information about a model."""
        if model_name not in self.models_info:
            return {}

        data = self.models_info[model_name]
        metrics = data['metrics']

        return {
            'name': model_name,
            'loaded_at': data['timestamp'],
            'overall_metrics': {
                'rmse': metrics.get('rmse'),
                'mae': metrics.get('mae'),
                'mse': metrics.get('mse'),
                'test_samples': metrics.get('test_samples'),
            },
            'parameter_recovery': metrics.get('param_rmse', {}),
            'parameter_mae': metrics.get('param_mae', {}),
            'parameter_skill': metrics.get('param_skill', {}),
            'mean_skill': metrics.get('mean_skill'),
            'constraint_validity': metrics.get('constraint_validity', {}),
        }

    def get_parameter_names(self) -> List[str]:
        """Get readable parameter names."""
        return [
            'κ_slow (mean reversion)',
            'θ_slow (long-term vol)',
            'σ_slow (volatility)',
            'ρ_slow (correlation)',
            'V₀_slow (initial var)',
            'κ_fast (mean reversion)',
            'θ_fast (long-term vol)',
            'σ_fast (volatility)',
            'ρ_fast (correlation)',
            'V₀_fast (initial var)',
        ]

    def export_for_web(self, output_file: Path):
        """Export results in web-friendly JSON format."""

        export_data = {
            'generated_at': datetime.now().isoformat(),
            'model_comparison': self.get_model_comparison(),
            'models': {},
        }

        for model_name in self.models_info.keys():
            export_data['models'][model_name] = self.get_model_details(model_name)

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported results to {output_file}")
        return export_data


def create_streamlit_metrics_display(integration: DoubleHestonWebIntegration) -> Dict:
    """Create structured data for Streamlit metrics display."""

    comparison = integration.get_model_comparison()

    metrics_display = []

    for model_info in comparison['models']:
        metrics_display.append({
            'name': model_info['name'],
            'rmse': model_info['rmse'],
            'mae': model_info['mae'],
            'test_samples': model_info['test_samples'],
        })

    return {
        'title': 'Double Heston Inverse Calibration Results',
        'description': 'Comparison of inverse calibration models trained on 10,000 synthetic surfaces',
        'models': metrics_display,
        'parameter_recovery_title': 'Parameter Recovery Accuracy (RMSE)',
        'parameter_recovery': comparison['metrics_summary'],
    }


def generate_web_summary_html(integration: DoubleHestonWebIntegration) -> str:
    """Generate HTML summary for web display."""

    comparison = integration.get_model_comparison()
    param_names = integration.get_parameter_names()

    html_parts = [
        "<div class='double-heston-results'>",
        "<h2>Double Heston Inverse Calibration</h2>",
        "<p>Training on 10,000 frozen synthetic surfaces from R2 representation</p>",
    ]

    # Model comparison table
    html_parts.append("<h3>Model Comparison</h3>")
    html_parts.append("<table style='width: 100%;'>")
    html_parts.append("<tr><th>Model</th><th>RMSE</th><th>MAE</th><th>Test Samples</th></tr>")

    for model in comparison['models']:
        html_parts.append(
            f"<tr>"
            f"<td>{model['name']}</td>"
            f"<td>{model['rmse']:.6f}</td>"
            f"<td>{model['mae']:.6f}</td>"
            f"<td>{model['test_samples']}</td>"
            f"</tr>"
        )

    html_parts.append("</table>")

    # Parameter recovery details
    html_parts.append("<h3>Parameter Recovery Accuracy (RMSE)</h3>")

    for model_name, params in comparison['metrics_summary'].items():
        html_parts.append(f"<h4>{model_name}</h4>")
        html_parts.append("<table style='width: 100%;'>")
        html_parts.append("<tr><th>Parameter</th><th>RMSE</th></tr>")

        for i, (param_key, rmse) in enumerate(params.items()):
            if i < len(param_names):
                param_display = param_names[i]
            else:
                param_display = param_key

            html_parts.append(f"<tr><td>{param_display}</td><td>{rmse:.6f}</td></tr>")

        html_parts.append("</table>")

    html_parts.append("</div>")

    return "\n".join(html_parts)


def publish_to_web(results_dir: Path, web_output_dir: Path):
    """Publish all results to web-accessible format."""

    web_output_dir.mkdir(parents=True, exist_ok=True)

    integration = DoubleHestonWebIntegration(results_dir)

    # Export JSON
    json_file = web_output_dir / "double_heston_results.json"
    integration.export_for_web(json_file)

    # Generate HTML summary
    html_summary = generate_web_summary_html(integration)
    html_file = web_output_dir / "double_heston_summary.html"
    with open(html_file, 'w') as f:
        f.write(html_summary)

    logger.info(f"Published results to {web_output_dir}")

    return {
        'json_file': json_file,
        'html_file': html_file,
        'integration': integration,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    results_dir = Path("outputs/training_results")
    web_output_dir = Path("web_outputs")

    if results_dir.exists():
        pub = publish_to_web(results_dir, web_output_dir)
        print(f"✓ Results published to {web_output_dir}")
    else:
        print(f"✗ Results directory not found: {results_dir}")
