"""
Visualization modules for signal and sleep analysis.
"""

from .signals import SignalVisualizer
from .sleep import (
    plot_hypnogram,
    plot_stage_distribution,
    plot_stage_transitions,
    compute_sleep_metrics
)

__all__ = [
    'SignalVisualizer',
    'plot_hypnogram',
    'plot_stage_distribution',
    'plot_stage_transitions',
    'compute_sleep_metrics'
]

