"""
Helper Utilities
================

General utility functions for the DREAMT analysis toolkit.
"""

import numpy as np
from typing import Tuple


def get_sampling_rate(resolution: str) -> float:
    """
    Get the sampling rate for a given resolution.
    
    Parameters
    ----------
    resolution : str
        Data resolution ('64Hz' or '100Hz').
        
    Returns
    -------
    float
        Sampling rate in Hz.
    """
    resolution_map = {
        '64Hz': 64.0,
        '100Hz': 100.0
    }
    
    if resolution not in resolution_map:
        raise ValueError(f"Unknown resolution: {resolution}. Use '64Hz' or '100Hz'.")
    
    return resolution_map[resolution]


def create_time_vector(n_samples: int, fs: float, start_time: float = 0.0) -> np.ndarray:
    """
    Create a time vector for signal data.
    
    Parameters
    ----------
    n_samples : int
        Number of samples.
    fs : float
        Sampling frequency in Hz.
    start_time : float
        Starting time in seconds.
        
    Returns
    -------
    np.ndarray
        Time vector in seconds.
    """
    return np.arange(n_samples) / fs + start_time


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Parameters
    ----------
    seconds : float
        Duration in seconds.
        
    Returns
    -------
    str
        Formatted duration string.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def samples_to_time(n_samples: int, fs: float) -> Tuple[float, str]:
    """
    Convert number of samples to time and formatted string.
    
    Parameters
    ----------
    n_samples : int
        Number of samples.
    fs : float
        Sampling frequency.
        
    Returns
    -------
    Tuple[float, str]
        Duration in seconds and formatted string.
    """
    duration_sec = n_samples / fs
    return duration_sec, format_duration(duration_sec)


def time_to_samples(time_sec: float, fs: float) -> int:
    """
    Convert time in seconds to number of samples.
    
    Parameters
    ----------
    time_sec : float
        Time in seconds.
    fs : float
        Sampling frequency.
        
    Returns
    -------
    int
        Number of samples.
    """
    return int(time_sec * fs)

