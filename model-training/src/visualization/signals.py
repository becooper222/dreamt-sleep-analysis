"""
Signal Visualization Module
===========================

Comprehensive visualization tools for IMU and PPG signals from the DREAMT dataset.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, List, Optional, Tuple, Union
import warnings


class SignalVisualizer:
    """
    Visualization toolkit for DREAMT wearable sensor data.
    
    This class provides methods for visualizing IMU (accelerometer) and 
    PPG (blood volume pulse) signals, with support for sleep stage overlays.
    
    Parameters
    ----------
    figsize : Tuple[int, int]
        Default figure size for plots.
    style : str
        Matplotlib style to use.
    dpi : int
        Resolution for saved figures.
        
    Examples
    --------
    >>> viz = SignalVisualizer()
    >>> viz.plot_imu_signals(time, acc_x, acc_y, acc_z)
    >>> viz.plot_ppg_signal(time, bvp, title="PPG Signal")
    """
    
    # Color scheme for sleep stages
    STAGE_COLORS = {
        'W': '#E74C3C',    # Red - Wake
        'N1': '#F39C12',   # Orange - Light sleep
        'N2': '#3498DB',   # Blue - Medium sleep
        'N3': '#2C3E50',   # Dark blue - Deep sleep
        'R': '#9B59B6',    # Purple - REM
        'P': '#95A5A6',    # Gray - Preparation
        'Missing': '#BDC3C7'  # Light gray
    }
    
    # Color scheme for IMU axes
    IMU_COLORS = {
        'X': '#E63946',   # Red
        'Y': '#2A9D8F',   # Teal
        'Z': '#457B9D',   # Blue
        'magnitude': '#1D3557'  # Dark blue
    }
    
    # PPG color
    PPG_COLOR = '#C44569'
    
    def __init__(
        self,
        figsize: Tuple[int, int] = (14, 6),
        style: str = 'seaborn-v0_8-whitegrid',
        dpi: int = 100
    ):
        """Initialize the visualizer with styling preferences."""
        self.figsize = figsize
        self.dpi = dpi
        
        # Try to set style, fall back gracefully
        try:
            plt.style.use(style)
        except OSError:
            try:
                plt.style.use('seaborn-whitegrid')
            except OSError:
                pass  # Use default style
    
    def plot_imu_signals(
        self,
        time: np.ndarray,
        acc_x: np.ndarray,
        acc_y: np.ndarray,
        acc_z: np.ndarray,
        title: str = "IMU Accelerometer Signals",
        show_magnitude: bool = True,
        sleep_stages: Optional[np.ndarray] = None,
        figsize: Optional[Tuple[int, int]] = None,
        time_unit: str = 'seconds',
        alpha: float = 0.8
    ) -> plt.Figure:
        """
        Plot triaxial accelerometer signals.
        
        Parameters
        ----------
        time : np.ndarray
            Time vector in seconds.
        acc_x, acc_y, acc_z : np.ndarray
            Accelerometer data for each axis.
        title : str
            Plot title.
        show_magnitude : bool
            Whether to also plot the magnitude.
        sleep_stages : np.ndarray, optional
            Sleep stage labels for background shading.
        figsize : Tuple[int, int], optional
            Figure size (overrides default).
        time_unit : str
            Time axis label ('seconds', 'minutes', 'hours').
        alpha : float
            Line transparency.
            
        Returns
        -------
        plt.Figure
            The matplotlib figure object.
        """
        figsize = figsize or self.figsize
        
        if show_magnitude:
            fig, axes = plt.subplots(4, 1, figsize=(figsize[0], figsize[1] * 1.5), sharex=True)
        else:
            fig, axes = plt.subplots(3, 1, figsize=figsize, sharex=True)
        
        # Convert time if needed
        time_display, time_label = self._convert_time(time, time_unit)
        
        # Add sleep stage background if provided
        if sleep_stages is not None:
            for ax in axes:
                self._add_stage_background(ax, time_display, sleep_stages)
        
        # Plot each axis
        signals = [
            (acc_x, 'X', self.IMU_COLORS['X']),
            (acc_y, 'Y', self.IMU_COLORS['Y']),
            (acc_z, 'Z', self.IMU_COLORS['Z'])
        ]
        
        for i, (data, label, color) in enumerate(signals):
            axes[i].plot(time_display, data, color=color, alpha=alpha, linewidth=0.5)
            axes[i].set_ylabel(f'ACC_{label}\n(1/64g)', fontsize=10)
            axes[i].grid(True, alpha=0.3)
        
        # Plot magnitude if requested
        if show_magnitude:
            magnitude = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
            axes[3].plot(time_display, magnitude, color=self.IMU_COLORS['magnitude'], 
                        alpha=alpha, linewidth=0.5)
            axes[3].set_ylabel('Magnitude\n(1/64g)', fontsize=10)
            axes[3].grid(True, alpha=0.3)
        
        # Labels and title
        axes[-1].set_xlabel(time_label, fontsize=11)
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
        
        # Add legend if sleep stages provided
        if sleep_stages is not None:
            self._add_stage_legend(fig)
        
        plt.tight_layout()
        return fig
    
    def plot_ppg_signal(
        self,
        time: np.ndarray,
        bvp: np.ndarray,
        title: str = "PPG Blood Volume Pulse Signal",
        hr: Optional[np.ndarray] = None,
        sleep_stages: Optional[np.ndarray] = None,
        figsize: Optional[Tuple[int, int]] = None,
        time_unit: str = 'seconds',
        alpha: float = 0.8,
        show_peaks: bool = False,
        peak_indices: Optional[np.ndarray] = None
    ) -> plt.Figure:
        """
        Plot PPG (Blood Volume Pulse) signal.
        
        Parameters
        ----------
        time : np.ndarray
            Time vector in seconds.
        bvp : np.ndarray
            Blood volume pulse signal.
        title : str
            Plot title.
        hr : np.ndarray, optional
            Heart rate data to plot on secondary axis.
        sleep_stages : np.ndarray, optional
            Sleep stage labels for background shading.
        figsize : Tuple[int, int], optional
            Figure size.
        time_unit : str
            Time axis label.
        alpha : float
            Line transparency.
        show_peaks : bool
            Whether to mark detected peaks.
        peak_indices : np.ndarray, optional
            Indices of peaks to mark.
            
        Returns
        -------
        plt.Figure
            The matplotlib figure object.
        """
        figsize = figsize or self.figsize
        n_subplots = 2 if hr is not None else 1
        
        fig, axes = plt.subplots(n_subplots, 1, figsize=figsize, sharex=True)
        if n_subplots == 1:
            axes = [axes]
        
        time_display, time_label = self._convert_time(time, time_unit)
        
        # Add sleep stage background
        if sleep_stages is not None:
            for ax in axes:
                self._add_stage_background(ax, time_display, sleep_stages)
        
        # Plot BVP
        axes[0].plot(time_display, bvp, color=self.PPG_COLOR, alpha=alpha, linewidth=0.5)
        axes[0].set_ylabel('BVP\n(arbitrary units)', fontsize=10)
        axes[0].grid(True, alpha=0.3)
        
        # Mark peaks if requested
        if show_peaks and peak_indices is not None:
            axes[0].scatter(
                time_display[peak_indices], 
                bvp[peak_indices],
                color='#2ECC71', 
                s=20, 
                zorder=5,
                label='Peaks'
            )
            axes[0].legend(loc='upper right')
        
        # Plot HR if provided
        if hr is not None:
            axes[1].plot(time_display[:len(hr)], hr, color='#E74C3C', alpha=alpha, linewidth=1)
            axes[1].set_ylabel('Heart Rate\n(bpm)', fontsize=10)
            axes[1].grid(True, alpha=0.3)
            axes[1].set_ylim([30, 150])  # Reasonable HR range
        
        axes[-1].set_xlabel(time_label, fontsize=11)
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
        
        if sleep_stages is not None:
            self._add_stage_legend(fig)
        
        plt.tight_layout()
        return fig
    
    def plot_combined_signals(
        self,
        time: np.ndarray,
        acc_x: np.ndarray,
        acc_y: np.ndarray, 
        acc_z: np.ndarray,
        bvp: np.ndarray,
        sleep_stages: Optional[np.ndarray] = None,
        title: str = "Combined IMU and PPG Signals",
        figsize: Optional[Tuple[int, int]] = None,
        time_unit: str = 'seconds'
    ) -> plt.Figure:
        """
        Plot IMU and PPG signals together in a single figure.
        
        Parameters
        ----------
        time : np.ndarray
            Time vector.
        acc_x, acc_y, acc_z : np.ndarray
            Accelerometer data.
        bvp : np.ndarray
            Blood volume pulse data.
        sleep_stages : np.ndarray, optional
            Sleep stage labels.
        title : str
            Plot title.
        figsize : Tuple[int, int], optional
            Figure size.
        time_unit : str
            Time axis unit.
            
        Returns
        -------
        plt.Figure
            The matplotlib figure object.
        """
        figsize = figsize or (self.figsize[0], self.figsize[1] * 1.5)
        
        fig, axes = plt.subplots(5, 1, figsize=figsize, sharex=True)
        time_display, time_label = self._convert_time(time, time_unit)
        
        if sleep_stages is not None:
            for ax in axes:
                self._add_stage_background(ax, time_display, sleep_stages)
        
        # IMU signals
        for i, (data, label, color) in enumerate([
            (acc_x, 'X', self.IMU_COLORS['X']),
            (acc_y, 'Y', self.IMU_COLORS['Y']),
            (acc_z, 'Z', self.IMU_COLORS['Z'])
        ]):
            axes[i].plot(time_display, data, color=color, alpha=0.8, linewidth=0.5)
            axes[i].set_ylabel(f'ACC_{label}', fontsize=9)
            axes[i].grid(True, alpha=0.3)
        
        # Magnitude
        magnitude = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
        axes[3].plot(time_display, magnitude, color=self.IMU_COLORS['magnitude'], 
                    alpha=0.8, linewidth=0.5)
        axes[3].set_ylabel('ACC Mag', fontsize=9)
        axes[3].grid(True, alpha=0.3)
        
        # PPG
        axes[4].plot(time_display, bvp, color=self.PPG_COLOR, alpha=0.8, linewidth=0.5)
        axes[4].set_ylabel('BVP', fontsize=9)
        axes[4].grid(True, alpha=0.3)
        
        axes[-1].set_xlabel(time_label, fontsize=11)
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
        
        if sleep_stages is not None:
            self._add_stage_legend(fig)
        
        plt.tight_layout()
        return fig
    
    def plot_signal_segment(
        self,
        time: np.ndarray,
        signals: Dict[str, np.ndarray],
        start_time: float,
        duration: float,
        title: str = "Signal Segment",
        sleep_stages: Optional[np.ndarray] = None
    ) -> plt.Figure:
        """
        Plot a specific time segment of signals.
        
        Parameters
        ----------
        time : np.ndarray
            Full time vector.
        signals : Dict[str, np.ndarray]
            Dictionary of signal name -> data.
        start_time : float
            Start time in seconds.
        duration : float
            Duration in seconds.
        title : str
            Plot title.
        sleep_stages : np.ndarray, optional
            Sleep stage labels.
            
        Returns
        -------
        plt.Figure
            The matplotlib figure object.
        """
        # Find indices for the segment
        mask = (time >= start_time) & (time < start_time + duration)
        
        n_signals = len(signals)
        fig, axes = plt.subplots(n_signals, 1, figsize=(14, 2.5 * n_signals), sharex=True)
        if n_signals == 1:
            axes = [axes]
        
        time_segment = time[mask]
        
        if sleep_stages is not None:
            stages_segment = sleep_stages[mask] if len(sleep_stages) == len(time) else None
            if stages_segment is not None:
                for ax in axes:
                    self._add_stage_background(ax, time_segment, stages_segment)
        
        colors = plt.cm.tab10(np.linspace(0, 1, n_signals))
        
        for i, (name, data) in enumerate(signals.items()):
            segment = data[mask]
            axes[i].plot(time_segment, segment, color=colors[i], linewidth=0.8)
            axes[i].set_ylabel(name, fontsize=10)
            axes[i].grid(True, alpha=0.3)
        
        axes[-1].set_xlabel('Time (seconds)', fontsize=11)
        fig.suptitle(f"{title} [{start_time:.1f}s - {start_time + duration:.1f}s]", 
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def plot_epoch(
        self,
        epoch_df: pd.DataFrame,
        fs: float = 64.0,
        title: str = "30-Second Epoch"
    ) -> plt.Figure:
        """
        Visualize a single epoch of data (typically 30 seconds).
        
        Parameters
        ----------
        epoch_df : pd.DataFrame
            DataFrame containing epoch data.
        fs : float
            Sampling frequency.
        title : str
            Plot title.
            
        Returns
        -------
        plt.Figure
            The matplotlib figure object.
        """
        time = np.arange(len(epoch_df)) / fs
        
        signals_to_plot = []
        if 'ACC_X' in epoch_df.columns:
            signals_to_plot.extend(['ACC_X', 'ACC_Y', 'ACC_Z'])
        if 'BVP' in epoch_df.columns:
            signals_to_plot.append('BVP')
        
        n_signals = len(signals_to_plot)
        fig, axes = plt.subplots(n_signals, 1, figsize=(12, 2 * n_signals), sharex=True)
        if n_signals == 1:
            axes = [axes]
        
        colors = {
            'ACC_X': self.IMU_COLORS['X'],
            'ACC_Y': self.IMU_COLORS['Y'],
            'ACC_Z': self.IMU_COLORS['Z'],
            'BVP': self.PPG_COLOR
        }
        
        for i, signal_name in enumerate(signals_to_plot):
            color = colors.get(signal_name, '#333333')
            axes[i].plot(time, epoch_df[signal_name].values, color=color, linewidth=0.8)
            axes[i].set_ylabel(signal_name, fontsize=10)
            axes[i].grid(True, alpha=0.3)
        
        # Add sleep stage info if available
        if 'Sleep_Stage' in epoch_df.columns:
            stage = epoch_df['Sleep_Stage'].mode().iloc[0] if len(epoch_df) > 0 else 'Unknown'
            title = f"{title} - Stage: {stage}"
        
        axes[-1].set_xlabel('Time (seconds)', fontsize=11)
        fig.suptitle(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def plot_spectrogram(
        self,
        signal: np.ndarray,
        fs: float,
        title: str = "Spectrogram",
        nperseg: int = 256,
        noverlap: Optional[int] = None,
        figsize: Optional[Tuple[int, int]] = None,
        cmap: str = 'magma'
    ) -> plt.Figure:
        """
        Plot a spectrogram of the signal.
        
        Parameters
        ----------
        signal : np.ndarray
            Input signal.
        fs : float
            Sampling frequency.
        title : str
            Plot title.
        nperseg : int
            Segment length for FFT.
        noverlap : int, optional
            Overlap between segments.
        figsize : Tuple[int, int], optional
            Figure size.
        cmap : str
            Colormap to use.
            
        Returns
        -------
        plt.Figure
            The matplotlib figure object.
        """
        from scipy import signal as sig
        
        figsize = figsize or (self.figsize[0], 4)
        fig, ax = plt.subplots(figsize=figsize)
        
        noverlap = noverlap or nperseg // 2
        
        f, t, Sxx = sig.spectrogram(signal, fs=fs, nperseg=nperseg, noverlap=noverlap)
        
        # Plot in dB scale
        Sxx_db = 10 * np.log10(Sxx + 1e-10)
        
        pcm = ax.pcolormesh(t, f, Sxx_db, shading='gouraud', cmap=cmap)
        ax.set_ylabel('Frequency (Hz)', fontsize=11)
        ax.set_xlabel('Time (seconds)', fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        cbar = fig.colorbar(pcm, ax=ax, label='Power (dB)')
        
        plt.tight_layout()
        return fig
    
    def _convert_time(
        self, 
        time: np.ndarray, 
        unit: str
    ) -> Tuple[np.ndarray, str]:
        """Convert time array to specified unit."""
        if unit == 'minutes':
            return time / 60, 'Time (minutes)'
        elif unit == 'hours':
            return time / 3600, 'Time (hours)'
        else:
            return time, 'Time (seconds)'
    
    def _add_stage_background(
        self,
        ax: plt.Axes,
        time: np.ndarray,
        stages: np.ndarray
    ) -> None:
        """Add colored background regions for sleep stages."""
        if len(stages) != len(time):
            return
        
        # Find stage transitions
        stage_changes = np.where(np.diff(stages.astype(str)) != '0')[0] + 1
        boundaries = np.concatenate([[0], stage_changes, [len(stages)]])
        
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1] - 1
            
            if start_idx >= len(time) or end_idx >= len(time):
                continue
                
            stage = str(stages[start_idx])
            color = self.STAGE_COLORS.get(stage, '#FFFFFF')
            
            ax.axvspan(
                time[start_idx], 
                time[min(end_idx, len(time) - 1)],
                alpha=0.15,
                color=color,
                zorder=0
            )
    
    def _add_stage_legend(self, fig: plt.Figure) -> None:
        """Add a legend for sleep stages."""
        legend_elements = [
            Patch(facecolor=color, alpha=0.5, label=f"{stage}: {name}")
            for stage, color in self.STAGE_COLORS.items()
            for name in [{'W': 'Wake', 'N1': 'NREM1', 'N2': 'NREM2', 
                         'N3': 'NREM3', 'R': 'REM', 'P': 'Prep', 
                         'Missing': 'Missing'}.get(stage, stage)]
        ]
        
        fig.legend(
            handles=legend_elements[:6],  # Main stages only
            loc='upper right',
            bbox_to_anchor=(0.99, 0.99),
            fontsize=8,
            framealpha=0.9
        )
    
    @staticmethod
    def save_figure(
        fig: plt.Figure,
        filepath: str,
        dpi: int = 150,
        transparent: bool = False
    ) -> None:
        """Save figure to file."""
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight', transparent=transparent)
        print(f"Figure saved to: {filepath}")

