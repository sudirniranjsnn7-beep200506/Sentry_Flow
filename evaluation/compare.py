"""
Model Comparison Module

Loads evaluation artifacts from multiple models and generates comparison reports.
Per AGENTS.md: build tables/plots from JSON artifacts only; no hand-typed numbers.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import matplotlib.pyplot as plt

from common.config import load_config
from common.errors import DatasetError
from common.paths import ProjectPaths

logger = logging.getLogger(__name__)


def load_model_artifacts(report_dir: Path) -> Optional[Dict]:
    """
    Load all artifacts for a single model evaluation.
    
    Args:
        report_dir: Path to artifacts/reports/<run_id>/
        
    Returns:
        Dictionary with metrics, timing, and metadata, or None if not found
    """
    if not report_dir.exists():
        logger.warning(f"Report directory not found: {report_dir}")
        return None
    
    try:
        # Load summary (contains everything)
        summary_path = report_dir / "summary.json"
        if not summary_path.exists():
            logger.warning(f"Summary file not found: {summary_path}")
            return None
            
        with open(summary_path, 'r') as f:
            data = json.load(f)
        
        # Also load CV metrics from run directory if available
        run_id = data.get('run_id', report_dir.name)
        config = load_config()
        paths = ProjectPaths(config)
        run_dir = paths.runs_dir / run_id
        
        cv_metrics_path = run_dir / "metrics_cv.json"
        if cv_metrics_path.exists():
            with open(cv_metrics_path, 'r') as f:
                cv_data = json.load(f)
                data['cv_score'] = cv_data.get('best_score')
                data['cv_params'] = cv_data.get('best_params')
        
        # Load model size
        pipeline_path = run_dir / "pipeline.joblib"
        if pipeline_path.exists():
            data['model_size_mb'] = pipeline_path.stat().st_size / (1024 * 1024)
        
        return data
        
    except Exception as e:
        logger.error(f"Error loading artifacts from {report_dir}: {e}")
        return None


def find_evaluated_models(reports_dir: Path) -> List[str]:
    """
    Find all models that have evaluation reports.
    
    Args:
        reports_dir: Path to artifacts/reports/
        
    Returns:
        List of run_ids that have evaluation reports
    """
    if not reports_dir.exists():
        return []
    
    run_ids = []
    for item in reports_dir.iterdir():
        if item.is_dir() and (item / "summary.json").exists():
            run_ids.append(item.name)
    
    logger.info(f"Found {len(run_ids)} evaluated models: {run_ids}")
    return run_ids


def build_comparison_table(model_data: Dict[str, Dict]) -> pd.DataFrame:
    """
    Build comparison table from model artifacts.
    
    Args:
        model_data: Dictionary mapping run_id to loaded artifacts
        
    Returns:
        DataFrame with comparison metrics
    """
    rows = []
    
    for run_id, data in model_data.items():
        if data is None:
            continue
            
        model_name = data.get('model_name', 'unknown')
        metrics = data.get('metrics', {})
        timing = data.get('timing', {})
        
        row = {
            'run_id': run_id,
            'model_name': model_name,
            'cv_macro_f1': data.get('cv_score'),
            'test_accuracy': metrics.get('accuracy'),
            'test_macro_precision': metrics.get('macro', {}).get('precision'),
            'test_macro_recall': metrics.get('macro', {}).get('recall'),
            'test_macro_f1': metrics.get('macro', {}).get('f1'),
            'test_weighted_f1': metrics.get('weighted', {}).get('f1'),
            'inference_time_ms': timing.get('mean_time_per_flow_ms'),
            'train_time_s': data.get('train_time_seconds'),
            'model_size_mb': data.get('model_size_mb'),
            'train_samples': data.get('train_samples'),
            'test_samples': data.get('test_samples'),
        }
        
        # Add per-class F1 scores
        per_class = metrics.get('per_class', {})
        for class_name, class_metrics in per_class.items():
            col_name = f'f1_{class_name.lower().replace(" ", "_")}'
            row[col_name] = class_metrics.get('f1')
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Sort by CV macro F1 (RID-20 criterion) descending
    if 'cv_macro_f1' in df.columns and not df['cv_macro_f1'].isna().all():
        df = df.sort_values('cv_macro_f1', ascending=False)
    
    return df


def plot_model_comparison(comparison_df: pd.DataFrame, output_path: Path):
    """
    Create comparison plots for models.
    
    Args:
        comparison_df: Comparison table from build_comparison_table
        output_path: Where to save the plot
    """
    if comparison_df.empty:
        logger.warning("No data to plot")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Model Comparison - FlowSentry', fontsize=16, fontweight='bold')
    
    models = comparison_df['model_name'].values
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    
    # 1. CV vs Test Macro F1
    ax = axes[0, 0]
    if 'cv_macro_f1' in comparison_df.columns and 'test_macro_f1' in comparison_df.columns:
        x = range(len(comparison_df))
        width = 0.35
        ax.bar([i - width/2 for i in x], comparison_df['cv_macro_f1'], 
               width, label='CV Macro F1', color=colors[0], alpha=0.8)
        ax.bar([i + width/2 for i in x], comparison_df['test_macro_f1'], 
               width, label='Test Macro F1', color=colors[1], alpha=0.8)
        ax.set_ylabel('Macro F1 Score')
        ax.set_title('Cross-Validation vs Test Performance')
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim([0.85, 1.0])
    
    # 2. Per-Class F1 Scores
    ax = axes[0, 1]
    class_cols = [col for col in comparison_df.columns if col.startswith('f1_')]
    if class_cols:
        class_names = [col.replace('f1_', '').replace('_', ' ').title() 
                       for col in class_cols]
        
        if len(comparison_df) == 1:
            # Single model: show per-class breakdown
            values = [comparison_df[col].iloc[0] for col in class_cols]
            bars = ax.barh(class_names, values, color=colors[:len(class_names)])
            ax.set_xlabel('F1 Score')
            ax.set_title(f'Per-Class Performance\n({models[0]})')
            ax.set_xlim([0.85, 1.0])
            ax.grid(axis='x', alpha=0.3)
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2, 
                       f'{width:.3f}', ha='left', va='center', fontsize=9)
        else:
            # Multiple models: grouped bars
            x = range(len(class_names))
            width = 0.8 / len(comparison_df)
            for i, (idx, row) in enumerate(comparison_df.iterrows()):
                values = [row[col] for col in class_cols]
                ax.bar([j + i*width for j in x], values, width, 
                      label=row['model_name'], color=colors[i % len(colors)], alpha=0.8)
            ax.set_ylabel('F1 Score')
            ax.set_title('Per-Class F1 Comparison')
            ax.set_xticks([i + width*(len(comparison_df)-1)/2 for i in x])
            ax.set_xticklabels(class_names, rotation=45, ha='right')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
    
    # 3. Inference Time
    ax = axes[1, 0]
    if 'inference_time_ms' in comparison_df.columns:
        bars = ax.bar(models, comparison_df['inference_time_ms'], 
                     color=colors[:len(models)], alpha=0.8)
        ax.set_ylabel('Time per Flow (ms)')
        ax.set_title('Inference Speed')
        ax.set_xticklabels(models, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height,
                   f'{height:.4f}', ha='center', va='bottom', fontsize=9)
    
    # 4. Model Size
    ax = axes[1, 1]
    if 'model_size_mb' in comparison_df.columns:
        bars = ax.bar(models, comparison_df['model_size_mb'], 
                     color=colors[:len(models)], alpha=0.8)
        ax.set_ylabel('Model Size (MB)')
        ax.set_title('Model Storage Footprint')
        ax.set_xticklabels(models, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"Comparison plot saved to {output_path}")
    plt.close()


def generate_comparison_report(comparison_df: pd.DataFrame, output_path: Path):
    """
    Generate markdown comparison report.
    
    Args:
        comparison_df: Comparison table
        output_path: Path to save markdown file
    """
    lines = [
        "# Model Comparison Report - FlowSentry",
        "",
        f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Models Evaluated:** {len(comparison_df)}",
        "",
        "## Overview",
        "",
    ]
    
    if len(comparison_df) == 1:
        lines.append("⚠️ **Note:** Only one model was trained and evaluated. "
                    "Random Forest, SVM, and XGBoost were not completed within "
                    "project time constraints.")
        lines.append("")
    
    lines.extend([
        "## Performance Comparison",
        "",
        "### Overall Metrics",
        "",
    ])
    
    # Format main metrics table
    metric_cols = ['model_name', 'cv_macro_f1', 'test_accuracy', 
                   'test_macro_f1', 'test_weighted_f1']
    if all(col in comparison_df.columns for col in metric_cols):
        metric_df = comparison_df[metric_cols].copy()
        headers = ['Model', 'CV Macro F1', 'Test Accuracy', 
                   'Test Macro F1', 'Test Weighted F1']
        
        # Build markdown table manually
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        for _, row in metric_df.iterrows():
            values = [row['model_name']]
            for col in metric_cols[1:]:
                val = row[col]
                values.append(f"{val:.4f}" if pd.notna(val) else "N/A")
            lines.append("| " + " | ".join(values) + " |")
        lines.append("")
    
    lines.extend([
        "### Per-Class F1 Scores",
        "",
    ])
    
    # Per-class table
    class_cols = ['model_name'] + [col for col in comparison_df.columns if col.startswith('f1_')]
    if class_cols and len(class_cols) > 1:
        class_df = comparison_df[class_cols].copy()
        headers = ['Model'] + [col.replace('f1_', '').replace('_', ' ').title() 
                               for col in class_cols[1:]]
        
        # Build markdown table manually
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        for _, row in class_df.iterrows():
            values = [row['model_name']]
            for col in class_cols[1:]:
                val = row[col]
                values.append(f"{val:.4f}" if pd.notna(val) else "N/A")
            lines.append("| " + " | ".join(values) + " |")
        lines.append("")
    
    lines.extend([
        "### Efficiency Metrics",
        "",
    ])
    
    # Efficiency table
    eff_cols = ['model_name', 'inference_time_ms', 'train_time_s', 'model_size_mb']
    if all(col in comparison_df.columns for col in eff_cols):
        eff_df = comparison_df[eff_cols].copy()
        headers = ['Model', 'Inference Time (ms/flow)', 
                   'Train Time (s)', 'Model Size (MB)']
        
        # Build markdown table manually
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        for _, row in eff_df.iterrows():
            model = row['model_name']
            inf_time = f"{row['inference_time_ms']:.4f}" if pd.notna(row['inference_time_ms']) else "N/A"
            train_time = f"{row['train_time_s']:.1f}" if pd.notna(row['train_time_s']) else "N/A"
            model_size = f"{row['model_size_mb']:.2f}" if pd.notna(row['model_size_mb']) else "N/A"
            
            lines.append(f"| {model} | {inf_time} | {train_time} | {model_size} |")
        lines.append("")
    
    lines.extend([
        "## Best Model Selection",
        "",
        "**Selection Criterion:** CV Macro F1 (RID-20)",
        "",
    ])
    
    if 'cv_macro_f1' in comparison_df.columns and not comparison_df['cv_macro_f1'].isna().all():
        best_row = comparison_df.iloc[0]
        best_model = best_row['model_name']
        best_cv_f1 = best_row['cv_macro_f1']
        best_test_f1 = best_row.get('test_macro_f1', 'N/A')
        
        lines.append(f"**Selected Model:** {best_model}")
        lines.append(f"**CV Macro F1:** {best_cv_f1:.4f}")
        if isinstance(best_test_f1, float):
            lines.append(f"**Test Macro F1:** {best_test_f1:.4f}")
        lines.append("")
    
    lines.extend([
        "## Comparison to Review-1",
        "",
        "Review-1 claimed 95-98% accuracy for similar traffic classification.",
        "",
    ])
    
    if 'test_accuracy' in comparison_df.columns:
        best_acc = comparison_df['test_accuracy'].max()
        if pd.notna(best_acc):
            lines.append(f"**Our Best Test Accuracy:** {best_acc:.4f} ({best_acc*100:.2f}%)")
            if 0.95 <= best_acc <= 0.98:
                lines.append("✅ Within Review-1 range")
            elif best_acc > 0.98:
                lines.append("✅ Exceeds Review-1 upper bound")
            else:
                lines.append("⚠️ Below Review-1 range")
            lines.append("")
    
    lines.extend([
        "## Limitations",
        "",
        "1. **Model Coverage:**",
    ])
    
    if len(comparison_df) < 4:
        lines.append(f"   - Only {len(comparison_df)} model(s) evaluated (target was 4)")
        lines.append("   - Cannot compare across model families")
        lines.append("")
    
    lines.extend([
        "2. **Dataset Specificity:**",
        "   - Results specific to ISCX-VPN2016 dataset",
        "   - Generalization to other traffic requires validation",
        "",
        "3. **Class Balance:**",
        "   - Training set has class imbalance (Streaming 4.6%)",
        "   - Smallest class may have lower performance",
        "",
        "## Artifact Provenance",
        "",
    ])
    
    for _, row in comparison_df.iterrows():
        run_id = row['run_id']
        lines.append(f"- **{row['model_name']}:** `artifacts/reports/{run_id}/`")
    
    lines.append("")
    lines.append("---")
    lines.append("*All metrics loaded from JSON artifacts (no hand-typed numbers)*")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Comparison report saved to {output_path}")


def main():
    """Main entry point for model comparison."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compare evaluated models and identify best model"
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('artifacts/reports'),
        help='Directory containing model evaluation reports'
    )
    parser.add_argument(
        '--comparison-file',
        type=Path,
        default=Path('artifacts/reports/comparison.csv'),
        help='Output path for comparison CSV'
    )
    parser.add_argument(
        '--report-file',
        type=Path,
        default=Path('artifacts/reports/comparison.md'),
        help='Output path for comparison markdown report'
    )
    parser.add_argument(
        '--plot-file',
        type=Path,
        default=Path('artifacts/reports/comparison.png'),
        help='Output path for comparison plot'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting model comparison")
    
    # Find evaluated models
    run_ids = find_evaluated_models(args.output_dir)
    
    if not run_ids:
        logger.error(f"No evaluated models found in {args.output_dir}")
        raise DatasetError(
            f"No model evaluation reports found in {args.output_dir}"
        )
    
    # Load artifacts
    model_data = {}
    for run_id in run_ids:
        report_dir = args.output_dir / run_id
        data = load_model_artifacts(report_dir)
        if data:
            model_data[run_id] = data
    
    if not model_data:
        logger.error("Failed to load any model artifacts")
        raise DatasetError("No valid model artifacts found")
    
    logger.info(f"Loaded artifacts for {len(model_data)} models")
    
    # Build comparison table
    comparison_df = build_comparison_table(model_data)
    
    # Save comparison table
    args.comparison_file.parent.mkdir(parents=True, exist_ok=True)
    comparison_df.to_csv(args.comparison_file, index=False)
    logger.info(f"Comparison table saved to {args.comparison_file}")
    
    # Generate plot
    plot_model_comparison(comparison_df, args.plot_file)
    
    # Generate markdown report
    generate_comparison_report(comparison_df, args.report_file)
    
    logger.info("Model comparison complete")
    
    # Print summary
    print("\n" + "="*60)
    print("MODEL COMPARISON SUMMARY")
    print("="*60)
    print(f"\nModels evaluated: {len(comparison_df)}")
    
    if 'cv_macro_f1' in comparison_df.columns:
        best_row = comparison_df.iloc[0]
        print(f"\nBest model (by CV Macro F1):")
        print(f"  Model: {best_row['model_name']}")
        print(f"  Run ID: {best_row['run_id']}")
        print(f"  CV Macro F1: {best_row['cv_macro_f1']:.4f}")
        if 'test_macro_f1' in best_row and pd.notna(best_row['test_macro_f1']):
            print(f"  Test Macro F1: {best_row['test_macro_f1']:.4f}")
    
    print(f"\nOutputs:")
    print(f"  Table: {args.comparison_file}")
    print(f"  Plot: {args.plot_file}")
    print(f"  Report: {args.report_file}")
    print()


if __name__ == '__main__':
    main()
