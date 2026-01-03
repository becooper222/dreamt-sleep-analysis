"""
Signal Preprocessing Utilities
==============================

Functions for preprocessing IMU and PPG signals from the DREAMT dataset.
"""

import numpy as np
from scipy import signal
from scipy.interpolate import interp1d
from typing import Optional, Tuple, Union


def resample_signal(
    data: np.ndarray,
    original_sr: float,
    target_sr: float,
    method: str = 'linear'
) -> np.ndarray:
    """
    Resample a signal to a new sampling rate.
    
    Parameters
    ----------
    data : np.ndarray
        Input signal.
    original_sr : float
        Original sampling rate in Hz.
    target_sr : float
        Target sampling rate in Hz.
    method : str
        Interpolation method ('linear', 'cubic', 'nearest').
        
    Returns
    -------
    np.ndarray
        Resampled signal.
    """
    if original_sr == target_sr:
        return data.copy()
    
    # Create time vectors
    n_samples = len(data)
    t_original = np.arange(n_samples) / original_sr
    t_target = np.arange(0, t_original[-1], 1 / target_sr)
    
    # Interpolate
    interpolator = interp1d(t_original, data, kind=method, fill_value='extrapolate')
    return interpolator(t_target)


def normalize_signal(
    data: np.ndarray,
    method: str = 'zscore',
    axis: Optional[int] = None
) -> np.ndarray:
    """
    Normalize a signal.
    
    Parameters
    ----------
    data : np.ndarray
        Input signal.
    method : str
        Normalization method:
        - 'zscore': (x - mean) / std
        - 'minmax': (x - min) / (max - min)
        - 'robust': (x - median) / IQR
    axis : int, optional
        Axis along which to normalize.
        
    Returns
    -------
    np.ndarray
        Normalized signal.
    """
    if method == 'zscore':
        mean = np.mean(data, axis=axis, keepdims=True)
        std = np.std(data, axis=axis, keepdims=True)
        std = np.where(std == 0, 1, std)  # Avoid division by zero
        return (data - mean) / std
    
    elif method == 'minmax':
        min_val = np.min(data, axis=axis, keepdims=True)
        max_val = np.max(data, axis=axis, keepdims=True)
        range_val = max_val - min_val
        range_val = np.where(range_val == 0, 1, range_val)
        return (data - min_val) / range_val
    
    elif method == 'robust':
        median = np.median(data, axis=axis, keepdims=True)
        q75 = np.percentile(data, 75, axis=axis, keepdims=True)
        q25 = np.percentile(data, 25, axis=axis, keepdims=True)
        iqr = q75 - q25
        iqr = np.where(iqr == 0, 1, iqr)
        return (data - median) / iqr
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def bandpass_filter(
    data: np.ndarray,
    lowcut: float,
    highcut: float,
    fs: float,
    order: int = 4
) -> np.ndarray:
    """
    Apply a Butterworth bandpass filter.
    
    Parameters
    ----------
    data : np.ndarray
        Input signal.
    lowcut : float
        Low cutoff frequency in Hz.
    highcut : float
        High cutoff frequency in Hz.
    fs : float
        Sampling frequency in Hz.
    order : int
        Filter order.
        
    Returns
    -------
    np.ndarray
        Filtered signal.
    """
    nyquist = fs / 2
    low = lowcut / nyquist
    high = highcut / nyquist
    
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data)


def lowpass_filter(
    data: np.ndarray,
    cutoff: float,
    fs: float,
    order: int = 4
) -> np.ndarray:
    """
    Apply a Butterworth lowpass filter.
    
    Parameters
    ----------
    data : np.ndarray
        Input signal.
    cutoff : float
        Cutoff frequency in Hz.
    fs : float
        Sampling frequency in Hz.
    order : int
        Filter order.
        
    Returns
    -------
    np.ndarray
        Filtered signal.
    """
    nyquist = fs / 2
    normalized_cutoff = cutoff / nyquist
    
    b, a = signal.butter(order, normalized_cutoff, btype='low')
    return signal.filtfilt(b, a, data)


def remove_gravity(
    acc_data: np.ndarray,
    fs: float,
    cutoff: float = 0.5
) -> np.ndarray:
    """
    Remove gravitational component from accelerometer data using high-pass filter.
    
    Parameters
    ----------
    acc_data : np.ndarray
        Accelerometer data (can be 1D or multi-axis).
    fs : float
        Sampling frequency in Hz.
    cutoff : float
        High-pass cutoff frequency in Hz (default 0.5 Hz).
        
    Returns
    -------
    np.ndarray
        Accelerometer data with gravity removed.
    """
    nyquist = fs / 2
    normalized_cutoff = cutoff / nyquist
    
    b, a = signal.butter(4, normalized_cutoff, btype='high')
    
    if acc_data.ndim == 1:
        return signal.filtfilt(b, a, acc_data)
    else:
        return np.apply_along_axis(lambda x: signal.filtfilt(b, a, x), 0, acc_data)


def compute_activity_counts(
    acc_magnitude: np.ndarray,
    fs: float,
    epoch_duration: float = 1.0
) -> np.ndarray:
    """
    Compute activity counts from acceleration magnitude.
    
    Parameters
    ----------
    acc_magnitude : np.ndarray
        Acceleration magnitude signal.
    fs : float
        Sampling frequency in Hz.
    epoch_duration : float
        Epoch duration in seconds for counting.
        
    Returns
    -------
    np.ndarray
        Activity counts per epoch.
    """
    samples_per_epoch = int(epoch_duration * fs)
    n_epochs = len(acc_magnitude) // samples_per_epoch
    
    counts = np.zeros(n_epochs)
    for i in range(n_epochs):
        start = i * samples_per_epoch
        end = start + samples_per_epoch
        epoch_data = acc_magnitude[start:end]
        # Sum of absolute values (simplified activity count)
        counts[i] = np.sum(np.abs(epoch_data - np.mean(epoch_data)))
    
    return counts


def detect_ppg_peaks(
    bvp: np.ndarray,
    fs: float,
    min_distance: float = 0.4
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect peaks in the PPG (BVP) signal.
    
    Parameters
    ----------
    bvp : np.ndarray
        Blood volume pulse signal.
    fs : float
        Sampling frequency in Hz.
    min_distance : float
        Minimum distance between peaks in seconds (based on max HR ~150 bpm).
        
    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        Peak indices and peak values.
    """
    min_samples = int(min_distance * fs)
    
    # Find peaks
    peaks, properties = signal.find_peaks(
        bvp,
        distance=min_samples,
        prominence=np.std(bvp) * 0.3
    )
    
    return peaks, bvp[peaks]


def compute_ibi_from_peaks(
    peak_indices: np.ndarray,
    fs: float
) -> np.ndarray:
    """
    Compute inter-beat intervals from peak indices.
    
    Parameters
    ----------
    peak_indices : np.ndarray
        Indices of detected peaks.
    fs : float
        Sampling frequency in Hz.
        
    Returns
    -------
    np.ndarray
        Inter-beat intervals in milliseconds.
    """
    ibi_samples = np.diff(peak_indices)
    ibi_ms = (ibi_samples / fs) * 1000
    return ibi_ms

