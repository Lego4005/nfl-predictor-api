#!/usr/bin/env python3
"""
Model Validation and Performance Tracking System
Provides comprehensive validation, backtesting, and performance monitoring
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, log_loss, roc_auc_score
)
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelValidator:
    """Comprehensive model validation and performance tracking"""

    def __init__(self, save_results: bool = True, results_dir: str = 'validation_results'):
        self.save_results = save_results
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.validation_history = []
        self.performance_metrics = {}
        self.backtest_results = {}

    def validate_model(self, model, X: pd.DataFrame, y: np.ndarray,
                      validation_type: str = 'time_series') -> Dict[str, Any]:
        """Comprehensive model validation"""

        logger.info(f"Starting {validation_type} validation...")

        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'validation_type': validation_type,
            'data_shape': X.shape,
            'class_distribution': dict(zip(*np.unique(y, return_counts=True)))
        }

        if validation_type == 'time_series':
            results = self._time_series_validation(model, X, y)
        elif validation_type == 'cross_validation':
            results = self._cross_validation(model, X, y)
        elif validation_type == 'holdout':
            results = self._holdout_validation(model, X, y)
        else:
            raise ValueError(f"Unknown validation type: {validation_type}")

        validation_results.update(results)

        # Add to history
        self.validation_history.append(validation_results)

        # Save results if requested
        if self.save_results:
            self._save_validation_results(validation_results)

        return validation_results

    def _time_series_validation(self, model, X: pd.DataFrame, y: np.ndarray) -> Dict[str, Any]:
        """Time series cross-validation for sequential data"""

        tscv = TimeSeriesSplit(n_splits=5, test_size=None)

        fold_results = []
        all_predictions = []
        all_probabilities = []
        all_true_labels = []

        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            # Train model on fold
            model.fit(X_train, y_train)

            # Predictions
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None

            # Calculate metrics for fold
            fold_metrics = self._calculate_metrics(y_test, y_pred, y_proba)
            fold_metrics['fold'] = fold
            fold_metrics['train_size'] = len(train_idx)
            fold_metrics['test_size'] = len(test_idx)

            fold_results.append(fold_metrics)

            # Store for overall metrics
            all_predictions.extend(y_pred)
            all_true_labels.extend(y_test)
            if y_proba is not None:
                all_probabilities.extend(y_proba)

        # Overall metrics
        overall_metrics = self._calculate_metrics(
            np.array(all_true_labels),
            np.array(all_predictions),
            np.array(all_probabilities) if all_probabilities else None
        )

        # Summary statistics
        metric_names = ['accuracy', 'precision', 'recall', 'f1_score']
        summary_stats = {}
        for metric in metric_names:
            values = [fold[metric] for fold in fold_results if metric in fold]
            summary_stats[f'{metric}_mean'] = np.mean(values)
            summary_stats[f'{metric}_std'] = np.std(values)
            summary_stats[f'{metric}_min'] = np.min(values)
            summary_stats[f'{metric}_max'] = np.max(values)

        return {
            'overall_metrics': overall_metrics,
            'fold_results': fold_results,
            'summary_statistics': summary_stats,
            'confusion_matrix': confusion_matrix(all_true_labels, all_predictions).tolist()
        }

    def _cross_validation(self, model, X: pd.DataFrame, y: np.ndarray) -> Dict[str, Any]:
        """Standard k-fold cross-validation"""

        # Use sklearn's cross_val_score for multiple metrics
        scoring_metrics = ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']

        cv_results = {}
        for metric in scoring_metrics:
            scores = cross_val_score(model, X, y, cv=5, scoring=metric, n_jobs=-1)
            cv_results[metric] = {
                'scores': scores.tolist(),
                'mean': scores.mean(),
                'std': scores.std(),
                'min': scores.min(),
                'max': scores.max()
            }

        return {
            'cross_validation_results': cv_results,
            'method': 'k_fold_cv',
            'folds': 5
        }

    def _holdout_validation(self, model, X: pd.DataFrame, y: np.ndarray) -> Dict[str, Any]:
        """Simple train-test holdout validation"""

        from sklearn.model_selection import train_test_split

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train and predict
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None

        # Calculate metrics
        metrics = self._calculate_metrics(y_test, y_pred, y_proba)

        return {
            'holdout_metrics': metrics,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }

    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                          y_proba: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Calculate comprehensive classification metrics"""

        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
        }

        # Add probabilistic metrics if probabilities available
        if y_proba is not None:
            try:
                metrics['log_loss'] = log_loss(y_true, y_proba)

                # AUC for binary/multiclass
                if len(np.unique(y_true)) == 2:
                    metrics['roc_auc'] = roc_auc_score(y_true, y_proba[:, 1])
                else:
                    metrics['roc_auc_ovr'] = roc_auc_score(y_true, y_proba, multi_class='ovr', average='weighted')
            except Exception as e:
                logger.warning(f"Could not calculate probabilistic metrics: {e}")

        return metrics

    def backtest_model(self, model, historical_data: pd.DataFrame,
                      target_column: str, date_column: str,
                      start_date: str, end_date: str) -> Dict[str, Any]:
        """Backtest model on historical data"""

        logger.info(f"Backtesting model from {start_date} to {end_date}")

        # Filter data by date range
        historical_data[date_column] = pd.to_datetime(historical_data[date_column])
        mask = (historical_data[date_column] >= start_date) & (historical_data[date_column] <= end_date)
        backtest_data = historical_data[mask].copy()

        if len(backtest_data) == 0:
            logger.warning("No data found in specified date range")
            return {'error': 'No data in date range'}

        # Sort by date
        backtest_data = backtest_data.sort_values(date_column)

        # Prepare features and target
        feature_columns = [col for col in backtest_data.columns
                          if col not in [target_column, date_column, 'game_id', 'home_team', 'away_team']]

        X = backtest_data[feature_columns]
        y = backtest_data[target_column]
        dates = backtest_data[date_column]

        # Rolling window predictions
        predictions = []
        actual_results = []
        prediction_dates = []

        # Use expanding window for predictions
        min_train_size = max(100, len(X) // 10)  # At least 100 samples or 10% of data

        for i in range(min_train_size, len(X)):
            # Training data up to current point
            X_train = X.iloc[:i]
            y_train = y.iloc[:i]

            # Current prediction point
            X_current = X.iloc[i:i+1]
            y_current = y.iloc[i]

            try:
                # Train model and predict
                model.fit(X_train, y_train)
                prediction = model.predict(X_current)[0]

                predictions.append(prediction)
                actual_results.append(y_current)
                prediction_dates.append(dates.iloc[i])

            except Exception as e:
                logger.warning(f"Prediction failed at index {i}: {e}")
                continue

        # Calculate backtest metrics
        if len(predictions) > 0:
            backtest_metrics = self._calculate_metrics(
                np.array(actual_results),
                np.array(predictions)
            )

            # Time series specific metrics
            backtest_metrics['total_predictions'] = len(predictions)
            backtest_metrics['date_range'] = {
                'start': str(min(prediction_dates)),
                'end': str(max(prediction_dates))
            }

            # Create results dataframe
            results_df = pd.DataFrame({
                'date': prediction_dates,
                'actual': actual_results,
                'predicted': predictions,
                'correct': [a == p for a, p in zip(actual_results, predictions)]
            })

            # Rolling accuracy
            window_size = min(50, len(results_df) // 5)
            results_df['rolling_accuracy'] = results_df['correct'].rolling(
                window=window_size, min_periods=10
            ).mean()

            backtest_results = {
                'metrics': backtest_metrics,
                'predictions_timeline': results_df.to_dict('records'),
                'final_rolling_accuracy': results_df['rolling_accuracy'].iloc[-1] if len(results_df) > 0 else 0
            }

            # Store results
            self.backtest_results[f'{start_date}_to_{end_date}'] = backtest_results

            return backtest_results

        else:
            return {'error': 'No predictions generated during backtest'}

    def performance_monitoring(self, model, live_predictions: List[Dict],
                             actual_results: List[Dict]) -> Dict[str, Any]:
        """Monitor model performance on live predictions"""

        if len(live_predictions) != len(actual_results):
            raise ValueError("Predictions and results must have same length")

        # Align predictions with results
        performance_data = []
        for pred, actual in zip(live_predictions, actual_results):
            if pred['game_id'] == actual['game_id']:
                performance_data.append({
                    'game_id': pred['game_id'],
                    'prediction': pred['prediction'],
                    'confidence': pred.get('confidence', 0.5),
                    'actual': actual['result'],
                    'correct': pred['prediction'] == actual['result'],
                    'date': pred.get('date', datetime.now().isoformat())
                })

        if not performance_data:
            return {'error': 'No matching predictions and results'}

        df = pd.DataFrame(performance_data)

        # Calculate performance metrics
        accuracy = df['correct'].mean()
        high_confidence_accuracy = df[df['confidence'] > 0.7]['correct'].mean() if len(df[df['confidence'] > 0.7]) > 0 else 0
        low_confidence_accuracy = df[df['confidence'] <= 0.5]['correct'].mean() if len(df[df['confidence'] <= 0.5]) > 0 else 0

        # Performance by time
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Rolling performance
        window_size = min(20, len(df) // 3)
        df['rolling_accuracy'] = df['correct'].rolling(window=window_size, min_periods=5).mean()

        monitoring_results = {
            'overall_accuracy': accuracy,
            'high_confidence_accuracy': high_confidence_accuracy,
            'low_confidence_accuracy': low_confidence_accuracy,
            'total_predictions': len(df),
            'confidence_distribution': {
                'mean': df['confidence'].mean(),
                'std': df['confidence'].std(),
                'min': df['confidence'].min(),
                'max': df['confidence'].max()
            },
            'recent_performance': {
                'last_10_accuracy': df['correct'].tail(10).mean() if len(df) >= 10 else accuracy,
                'last_20_accuracy': df['correct'].tail(20).mean() if len(df) >= 20 else accuracy,
                'trend': 'improving' if len(df) >= 10 and df['correct'].tail(10).mean() > df['correct'].head(-10).mean() else 'declining'
            },
            'performance_timeline': df[['date', 'correct', 'rolling_accuracy']].to_dict('records')
        }

        return monitoring_results

    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""

        if not self.validation_history:
            return "No validation results available"

        latest_validation = self.validation_history[-1]

        report = f"""
MODEL VALIDATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== VALIDATION SUMMARY ===
Validation Type: {latest_validation['validation_type']}
Data Shape: {latest_validation['data_shape']}
Class Distribution: {latest_validation['class_distribution']}

=== PERFORMANCE METRICS ===
"""

        if 'overall_metrics' in latest_validation:
            metrics = latest_validation['overall_metrics']
            report += f"""
Overall Accuracy: {metrics.get('accuracy', 0):.4f}
Precision: {metrics.get('precision', 0):.4f}
Recall: {metrics.get('recall', 0):.4f}
F1 Score: {metrics.get('f1_score', 0):.4f}
"""

            if 'log_loss' in metrics:
                report += f"Log Loss: {metrics['log_loss']:.4f}\n"
            if 'roc_auc' in metrics:
                report += f"ROC AUC: {metrics['roc_auc']:.4f}\n"

        if 'summary_statistics' in latest_validation:
            stats = latest_validation['summary_statistics']
            report += f"""
=== CROSS-VALIDATION STATISTICS ===
Accuracy: {stats.get('accuracy_mean', 0):.4f} ± {stats.get('accuracy_std', 0):.4f}
Precision: {stats.get('precision_mean', 0):.4f} ± {stats.get('precision_std', 0):.4f}
Recall: {stats.get('recall_mean', 0):.4f} ± {stats.get('recall_std', 0):.4f}
F1 Score: {stats.get('f1_score_mean', 0):.4f} ± {stats.get('f1_score_std', 0):.4f}
"""

        # Add backtest results if available
        if self.backtest_results:
            report += "\n=== BACKTEST RESULTS ===\n"
            for period, results in self.backtest_results.items():
                if 'metrics' in results:
                    metrics = results['metrics']
                    report += f"""
Period: {period}
Accuracy: {metrics.get('accuracy', 0):.4f}
Total Predictions: {metrics.get('total_predictions', 0)}
Rolling Accuracy: {results.get('final_rolling_accuracy', 0):.4f}
"""

        return report

    def create_performance_visualizations(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """Create performance visualization plots"""

        visualizations = {}

        if not self.validation_history:
            return {'error': 'No validation data available for visualization'}

        latest_validation = self.validation_history[-1]

        # 1. Confusion Matrix
        if 'confusion_matrix' in latest_validation:
            cm = np.array(latest_validation['confusion_matrix'])

            fig_cm = go.Figure(data=go.Heatmap(
                z=cm,
                x=['Predicted 0', 'Predicted 1', 'Predicted 2'][:cm.shape[1]],
                y=['Actual 0', 'Actual 1', 'Actual 2'][:cm.shape[0]],
                colorscale='Blues',
                text=cm,
                texttemplate="%{text}",
                textfont={"size": 16},
            ))

            fig_cm.update_layout(
                title='Confusion Matrix',
                xaxis_title='Predicted',
                yaxis_title='Actual'
            )

            visualizations['confusion_matrix'] = fig_cm

        # 2. Performance Metrics Comparison
        if 'summary_statistics' in latest_validation:
            stats = latest_validation['summary_statistics']
            metrics = ['accuracy', 'precision', 'recall', 'f1_score']
            means = [stats.get(f'{m}_mean', 0) for m in metrics]
            stds = [stats.get(f'{m}_std', 0) for m in metrics]

            fig_metrics = go.Figure()
            fig_metrics.add_trace(go.Bar(
                x=metrics,
                y=means,
                error_y=dict(type='data', array=stds),
                name='Performance Metrics'
            ))

            fig_metrics.update_layout(
                title='Model Performance Metrics (with Standard Deviation)',
                yaxis_title='Score',
                yaxis_range=[0, 1]
            )

            visualizations['performance_metrics'] = fig_metrics

        # 3. Validation History Timeline
        if len(self.validation_history) > 1:
            timeline_data = []
            for i, validation in enumerate(self.validation_history):
                if 'overall_metrics' in validation:
                    metrics = validation['overall_metrics']
                    timeline_data.append({
                        'validation_run': i + 1,
                        'accuracy': metrics.get('accuracy', 0),
                        'timestamp': validation.get('timestamp', '')
                    })

            if timeline_data:
                df_timeline = pd.DataFrame(timeline_data)

                fig_timeline = px.line(
                    df_timeline,
                    x='validation_run',
                    y='accuracy',
                    title='Model Accuracy Over Validation Runs',
                    markers=True
                )

                visualizations['validation_timeline'] = fig_timeline

        # 4. Backtest Performance
        if self.backtest_results:
            for period, results in self.backtest_results.items():
                if 'predictions_timeline' in results:
                    timeline_df = pd.DataFrame(results['predictions_timeline'])

                    fig_backtest = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=('Predictions vs Actual', 'Rolling Accuracy'),
                        vertical_spacing=0.1
                    )

                    # Plot predictions vs actual
                    fig_backtest.add_trace(
                        go.Scatter(
                            x=timeline_df['date'],
                            y=timeline_df['actual'],
                            mode='markers',
                            name='Actual',
                            marker=dict(color='blue')
                        ),
                        row=1, col=1
                    )

                    fig_backtest.add_trace(
                        go.Scatter(
                            x=timeline_df['date'],
                            y=timeline_df['predicted'],
                            mode='markers',
                            name='Predicted',
                            marker=dict(color='red', symbol='x')
                        ),
                        row=1, col=1
                    )

                    # Plot rolling accuracy
                    fig_backtest.add_trace(
                        go.Scatter(
                            x=timeline_df['date'],
                            y=timeline_df['rolling_accuracy'],
                            mode='lines',
                            name='Rolling Accuracy',
                            line=dict(color='green')
                        ),
                        row=2, col=1
                    )

                    fig_backtest.update_layout(
                        title=f'Backtest Results: {period}',
                        height=600
                    )

                    visualizations[f'backtest_{period}'] = fig_backtest

        # Save visualizations if path provided
        if save_path:
            save_dir = Path(save_path)
            save_dir.mkdir(parents=True, exist_ok=True)

            for name, fig in visualizations.items():
                fig.write_html(save_dir / f'{name}.html')
                fig.write_image(save_dir / f'{name}.png')

        return visualizations

    def _save_validation_results(self, results: Dict[str, Any]):
        """Save validation results to file"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.results_dir / f'validation_{timestamp}.json'

        # Convert numpy arrays to lists for JSON serialization
        serializable_results = self._make_serializable(results)

        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        logger.info(f"Validation results saved to {filename}")

    def _make_serializable(self, obj):
        """Make object JSON serializable"""

        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj


# Example usage
if __name__ == "__main__":
    from ensemble_predictor import AdvancedEnsemblePredictor, create_sample_training_data

    # Create sample data and model
    X_sample, y_sample = create_sample_training_data(500)
    model = AdvancedEnsemblePredictor()

    # Initialize validator
    validator = ModelValidator(save_results=True)

    # Perform validation
    validation_results = validator.validate_model(model, X_sample, y_sample, 'time_series')

    # Generate report
    report = validator.generate_validation_report()
    print(report)

    # Create visualizations
    visualizations = validator.create_performance_visualizations('validation_plots')

    logger.info("Model validation completed successfully")