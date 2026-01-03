"""
Sleep Stage Visualization
=========================

Specialized visualizations for sleep stage analysis.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from typing import Dict, List, Optional, Tuple


# Stage colors
STAGE_COLORS = {
    'W': '#E74C3C',
    'N1': '#F39C12',
    'N2': '#3498DB',
    'N3': '#2C3E50',
    'R': '#9B59B6',
    'P': '#95A5A6',
    'Missing': '#BDC3C7'
}

STAGE_ORDER = ['W', 'R', 'N1', 'N2', 'N3']
STAGE_Y_POS = {'W': 4, 'R': 3, 'N1': 2, 'N2': 1, 'N3': 0, 'P': 4, 'Missing': -1}


def plot_hypnogram(
    stages: np.ndarray,
    epoch_duration: float = 30.0,
    title: str = "Hypnogram",
    figsize: Tuple[int, int] = (14, 4),
    show_hours: bool = True
) -> plt.Figure:
    """
    Plot a hypnogram (sleep stage progression over time).
    
    Parameters
    ----------
    stages : np.ndarray
        Array of sleep stage labels (one per epoch).
    epoch_duration : float
        Duration of each epoch in seconds (default 30s for standard sleep staging).
    title : str
        Plot title.
    figsize : Tuple[int, int]
        Figure size.
    show_hours : bool
        Whether to display time in hours instead of minutes.
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create time vector
    n_epochs = len(stages)
    if show_hours:
        time = np.arange(n_epochs) * epoch_duration / 3600
        time_label = 'Time (hours)'
    else:
        time = np.arange(n_epochs) * epoch_duration / 60
        time_label = 'Time (minutes)'
    
    # Convert stages to numeric positions
    y_values = np.array([STAGE_Y_POS.get(str(s), -1) for s in stages])
    
    # Plot hypnogram as step function
    ax.step(time, y_values, where='post', linewidth=2, color='#2C3E50')
    
    # Fill regions with stage colors
    for i in range(len(stages) - 1):
        stage = str(stages[i])
        color = STAGE_COLORS.get(stage, '#CCCCCC')
        y = STAGE_Y_POS.get(stage, -1)
        
        ax.fill_between(
            [time[i], time[i + 1]], 
            y - 0.4, 
            y + 0.4,
            color=color,
            alpha=0.3,
            step='post'
        )
    
    # Formatting
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(['N3', 'N2', 'N1', 'REM', 'Wake'], fontsize=11)
    ax.set_ylim(-0.5, 4.5)
    ax.set_xlim(time[0], time[-1])
    
    ax.set_xlabel(time_label, fontsize=12)
    ax.set_ylabel('Sleep Stage', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.grid(True, alpha=0.3, axis='x')
    ax.invert_yaxis()  # Deep sleep at bottom
    
    # Add legend
    legend_elements = [
        Patch(facecolor=STAGE_COLORS['W'], alpha=0.5, label='Wake'),
        Patch(facecolor=STAGE_COLORS['R'], alpha=0.5, label='REM'),
        Patch(facecolor=STAGE_COLORS['N1'], alpha=0.5, label='N1'),
        Patch(facecolor=STAGE_COLORS['N2'], alpha=0.5, label='N2'),
        Patch(facecolor=STAGE_COLORS['N3'], alpha=0.5, label='N3'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    plt.tight_layout()
    return fig


def plot_stage_distribution(
    stages: np.ndarray,
    epoch_duration: float = 30.0,
    title: str = "Sleep Stage Distribution",
    figsize: Tuple[int, int] = (10, 5),
    show_percentage: bool = True
) -> plt.Figure:
    """
    Plot the distribution of sleep stages.
    
    Parameters
    ----------
    stages : np.ndarray
        Array of sleep stage labels.
    epoch_duration : float
        Duration of each epoch in seconds.
    title : str
        Plot title.
    figsize : Tuple[int, int]
        Figure size.
    show_percentage : bool
        Whether to show percentages on bars.
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # Count stages
    unique, counts = np.unique(stages, return_counts=True)
    stage_counts = dict(zip(unique, counts))
    
    # Ensure all main stages are present
    for stage in STAGE_ORDER:
        if stage not in stage_counts:
            stage_counts[stage] = 0
    
    # Calculate durations in minutes
    durations = {k: v * epoch_duration / 60 for k, v in stage_counts.items()}
    
    # Bar plot
    stages_to_plot = [s for s in STAGE_ORDER if s in stage_counts]
    values = [durations.get(s, 0) for s in stages_to_plot]
    colors = [STAGE_COLORS.get(s, '#CCCCCC') for s in stages_to_plot]
    
    bars = axes[0].bar(stages_to_plot, values, color=colors, edgecolor='white', linewidth=2)
    axes[0].set_xlabel('Sleep Stage', fontsize=12)
    axes[0].set_ylabel('Duration (minutes)', fontsize=12)
    axes[0].set_title('Time in Each Stage', fontsize=13, fontweight='bold')
    
    # Add value labels
    if show_percentage:
        total = sum(values)
        for bar, val in zip(bars, values):
            pct = (val / total * 100) if total > 0 else 0
            axes[0].text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f'{pct:.1f}%',
                ha='center',
                fontsize=10
            )
    
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # Pie chart
    pie_values = [stage_counts.get(s, 0) for s in stages_to_plot if stage_counts.get(s, 0) > 0]
    pie_labels = [s for s in stages_to_plot if stage_counts.get(s, 0) > 0]
    pie_colors = [STAGE_COLORS.get(s, '#CCCCCC') for s in pie_labels]
    
    if pie_values:
        wedges, texts, autotexts = axes[1].pie(
            pie_values,
            labels=pie_labels,
            colors=pie_colors,
            autopct='%1.1f%%',
            startangle=90,
            explode=[0.02] * len(pie_values)
        )
        axes[1].set_title('Stage Proportions', fontsize=13, fontweight='bold')
    
    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig


def plot_stage_transitions(
    stages: np.ndarray,
    title: str = "Sleep Stage Transitions",
    figsize: Tuple[int, int] = (8, 6)
) -> plt.Figure:
    """
    Plot a heatmap of transitions between sleep stages.
    
    Parameters
    ----------
    stages : np.ndarray
        Array of sleep stage labels.
    title : str
        Plot title.
    figsize : Tuple[int, int]
        Figure size.
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Compute transition matrix
    labels = STAGE_ORDER
    n_labels = len(labels)
    label_to_idx = {l: i for i, l in enumerate(labels)}
    
    transition_matrix = np.zeros((n_labels, n_labels))
    
    for i in range(len(stages) - 1):
        from_stage = str(stages[i])
        to_stage = str(stages[i + 1])
        
        if from_stage in label_to_idx and to_stage in label_to_idx:
            transition_matrix[label_to_idx[from_stage], label_to_idx[to_stage]] += 1
    
    # Normalize by row (transition probabilities)
    row_sums = transition_matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    transition_probs = transition_matrix / row_sums
    
    # Plot heatmap
    im = ax.imshow(transition_probs, cmap='Blues', aspect='auto', vmin=0, vmax=1)
    
    # Add colorbar
    cbar = fig.colorbar(im, ax=ax, label='Transition Probability')
    
    # Labels
    ax.set_xticks(range(n_labels))
    ax.set_yticks(range(n_labels))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_yticklabels(labels, fontsize=11)
    
    ax.set_xlabel('To Stage', fontsize=12)
    ax.set_ylabel('From Stage', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add text annotations
    for i in range(n_labels):
        for j in range(n_labels):
            prob = transition_probs[i, j]
            color = 'white' if prob > 0.5 else 'black'
            ax.text(j, i, f'{prob:.2f}', ha='center', va='center', color=color, fontsize=10)
    
    plt.tight_layout()
    return fig


def compute_sleep_metrics(
    stages: np.ndarray,
    epoch_duration: float = 30.0
) -> Dict[str, float]:
    """
    Compute common sleep metrics from stage labels.
    
    Parameters
    ----------
    stages : np.ndarray
        Array of sleep stage labels.
    epoch_duration : float
        Duration of each epoch in seconds.
        
    Returns
    -------
    Dict[str, float]
        Dictionary of sleep metrics.
    """
    stages = np.array([str(s) for s in stages])
    n_epochs = len(stages)
    
    # Count epochs for each stage
    counts = {stage: np.sum(stages == stage) for stage in STAGE_ORDER}
    
    # Calculate times in minutes
    times = {f'{stage}_minutes': count * epoch_duration / 60 
             for stage, count in counts.items()}
    
    # Total recording time
    total_time = n_epochs * epoch_duration / 60
    
    # Total sleep time (all stages except Wake and Prep)
    sleep_stages = ['N1', 'N2', 'N3', 'R']
    tst = sum(counts.get(s, 0) for s in sleep_stages) * epoch_duration / 60
    
    # Wake after sleep onset (WASO)
    # Find first sleep epoch
    sleep_mask = np.isin(stages, sleep_stages)
    if np.any(sleep_mask):
        first_sleep_idx = np.argmax(sleep_mask)
        last_sleep_idx = len(stages) - 1 - np.argmax(sleep_mask[::-1])
        waso_epochs = np.sum(stages[first_sleep_idx:last_sleep_idx + 1] == 'W')
        waso = waso_epochs * epoch_duration / 60
    else:
        waso = 0.0
        first_sleep_idx = None
    
    # Sleep onset latency
    sol = (first_sleep_idx * epoch_duration / 60) if first_sleep_idx is not None else total_time
    
    # Sleep efficiency
    sleep_efficiency = (tst / total_time * 100) if total_time > 0 else 0.0
    
    # REM latency (from first sleep to first REM)
    rem_mask = stages == 'R'
    if np.any(rem_mask) and first_sleep_idx is not None:
        first_rem_idx = np.argmax(rem_mask)
        rem_latency = (first_rem_idx - first_sleep_idx) * epoch_duration / 60
    else:
        rem_latency = None
    
    metrics = {
        'total_recording_time_min': total_time,
        'total_sleep_time_min': tst,
        'sleep_onset_latency_min': sol,
        'wake_after_sleep_onset_min': waso,
        'sleep_efficiency_pct': sleep_efficiency,
        'rem_latency_min': rem_latency,
        **times,
        'n_stage_transitions': np.sum(np.diff(stages.astype(str)) != '')
    }
    
    return metrics

