"""
Feature Extraction for Sleep Stage Classification
==================================================

Extract time-domain and frequency-domain features from IMU and PPG signals.
"""

import numpy as np
import pandas as pd
from scipy import stats, signal
from typing import Dict, List, Optional, Tuple
from ..data.preprocessing import detect_ppg_peaks, compute_ibi_from_peaks


class FeatureExtractor:
    """
    Extract features from IMU and PPG signals for sleep stage classification.
    
    Parameters
    ----------
    epoch_duration : float
        Duration of each epoch in seconds (default 30s).
    fs : float
        Sampling frequency in Hz.
    overlap : float
        Overlap between epochs (0.0 to 1.0).
    """
    
    def __init__(
        self,
        epoch_duration: float = 30.0,
        fs: float = 64.0,
        overlap: float = 0.0
    ):
        self.epoch_duration = epoch_duration
        self.fs = fs
        self.overlap = overlap
        self.samples_per_epoch = int(epoch_duration * fs)
        self.step_size = int(self.samples_per_epoch * (1 - overlap))
    
    def extract_all_features(
        self,
        df: pd.DataFrame,
        include_imu: bool = True,
        include_ppg: bool = True
    ) -> pd.DataFrame:
        """
        Extract all features from a participant's data.
        
        Parameters
        ----------
        df : pd.DataFrame
            Participant data with signal columns.
        include_imu : bool
            Whether to include IMU features.
        include_ppg : bool
            Whether to include PPG features.
            
        Returns
        -------
        pd.DataFrame
            DataFrame with extracted features (one row per epoch).
        """
        n_samples = len(df)
        epochs = []
        
        for start in range(0, n_samples - self.samples_per_epoch + 1, self.step_size):
            end = start + self.samples_per_epoch
            epoch_df = df.iloc[start:end]
            
            features = {}
            
            if include_imu and all(c in df.columns for c in ['ACC_X', 'ACC_Y', 'ACC_Z']):
                imu_features = self._extract_imu_features(epoch_df)
                features.update(imu_features)
            
            if include_ppg and 'BVP' in df.columns:
                ppg_features = self._extract_ppg_features(epoch_df)
                features.update(ppg_features)
            
            # Add sleep stage label if available
            if 'Sleep_Stage' in df.columns:
                features['Sleep_Stage'] = epoch_df['Sleep_Stage'].mode().iloc[0]
            
            epochs.append(features)
        
        return pd.DataFrame(epochs)
    
    def _extract_imu_features(self, epoch_df: pd.DataFrame) -> Dict[str, float]:
        """Extract features from IMU signals."""
        features = {}
        
        for axis in ['X', 'Y', 'Z']:
            col = f'ACC_{axis}'
            if col in epoch_df.columns:
                signal_data = epoch_df[col].values
                axis_features = self._compute_statistical_features(signal_data, f'imu_{axis.lower()}')
                features.update(axis_features)
        
        # Magnitude features
        if all(f'ACC_{a}' in epoch_df.columns for a in ['X', 'Y', 'Z']):
            magnitude = np.sqrt(
                epoch_df['ACC_X'].values**2 + 
                epoch_df['ACC_Y'].values**2 + 
                epoch_df['ACC_Z'].values**2
            )
            mag_features = self._compute_statistical_features(magnitude, 'imu_mag')
            features.update(mag_features)
            
            # Activity-specific features
            features['imu_activity_count'] = np.sum(np.abs(np.diff(magnitude)))
            features['imu_movement_intensity'] = np.std(magnitude)
        
        return features
    
    def _extract_ppg_features(self, epoch_df: pd.DataFrame) -> Dict[str, float]:
        """Extract features from PPG signal."""
        features = {}
        bvp = epoch_df['BVP'].values
        
        # Basic BVP features
        bvp_features = self._compute_statistical_features(bvp, 'ppg')
        features.update(bvp_features)
        
        # Heart rate features from HR column if available
        if 'HR' in epoch_df.columns:
            hr = epoch_df['HR'].values
            hr = hr[~np.isnan(hr)]
            if len(hr) > 0:
                features['hr_mean'] = np.mean(hr)
                features['hr_std'] = np.std(hr)
                features['hr_min'] = np.min(hr)
                features['hr_max'] = np.max(hr)
                features['hr_range'] = np.max(hr) - np.min(hr)
        
        # HRV features from peak detection
        try:
            peaks, _ = detect_ppg_peaks(bvp, self.fs)
            if len(peaks) > 2:
                ibi = compute_ibi_from_peaks(peaks, self.fs)
                hrv_features = self._compute_hrv_features(ibi)
                features.update(hrv_features)
        except Exception:
            pass
        
        return features
    
    def _compute_statistical_features(
        self, 
        signal_data: np.ndarray, 
        prefix: str
    ) -> Dict[str, float]:
        """Compute statistical features from a signal."""
        features = {}
        
        # Handle NaN values
        signal_data = signal_data[~np.isnan(signal_data)]
        if len(signal_data) == 0:
            return features
        
        features[f'{prefix}_mean'] = np.mean(signal_data)
        features[f'{prefix}_std'] = np.std(signal_data)
        features[f'{prefix}_min'] = np.min(signal_data)
        features[f'{prefix}_max'] = np.max(signal_data)
        features[f'{prefix}_range'] = np.ptp(signal_data)
        features[f'{prefix}_median'] = np.median(signal_data)
        
        # IQR
        q75, q25 = np.percentile(signal_data, [75, 25])
        features[f'{prefix}_iqr'] = q75 - q25
        
        # Shape features
        if np.std(signal_data) > 0:
            features[f'{prefix}_skew'] = stats.skew(signal_data)
            features[f'{prefix}_kurtosis'] = stats.kurtosis(signal_data)
        else:
            features[f'{prefix}_skew'] = 0.0
            features[f'{prefix}_kurtosis'] = 0.0
        
        # Energy
        features[f'{prefix}_energy'] = np.sum(signal_data**2)
        features[f'{prefix}_rms'] = np.sqrt(np.mean(signal_data**2))
        
        # Zero crossings
        zero_crossings = np.sum(np.diff(np.signbit(signal_data - np.mean(signal_data))))
        features[f'{prefix}_zero_crossings'] = zero_crossings
        
        return features
    
    def _compute_hrv_features(self, ibi: np.ndarray) -> Dict[str, float]:
        """
        Compute heart rate variability features from inter-beat intervals.
        
        Parameters
        ----------
        ibi : np.ndarray
            Inter-beat intervals in milliseconds.
            
        Returns
        -------
        Dict[str, float]
            HRV features.
        """
        features = {}
        
        if len(ibi) < 2:
            return features
        
        # Remove outliers (physiologically impossible values)
        ibi = ibi[(ibi > 300) & (ibi < 2000)]  # 30-200 bpm range
        
        if len(ibi) < 2:
            return features
        
        # Time-domain HRV features
        features['hrv_mean_ibi'] = np.mean(ibi)
        features['hrv_sdnn'] = np.std(ibi)  # Standard deviation of NN intervals
        
        # RMSSD: Root mean square of successive differences
        successive_diff = np.diff(ibi)
        features['hrv_rmssd'] = np.sqrt(np.mean(successive_diff**2))
        
        # pNN50: Percentage of successive differences > 50ms
        pnn50 = np.sum(np.abs(successive_diff) > 50) / len(successive_diff) * 100
        features['hrv_pnn50'] = pnn50
        
        # pNN20: Percentage of successive differences > 20ms
        pnn20 = np.sum(np.abs(successive_diff) > 20) / len(successive_diff) * 100
        features['hrv_pnn20'] = pnn20
        
        return features
    
    def extract_frequency_features(
        self, 
        signal_data: np.ndarray, 
        prefix: str
    ) -> Dict[str, float]:
        """
        Extract frequency-domain features using FFT.
        
        Parameters
        ----------
        signal_data : np.ndarray
            Input signal.
        prefix : str
            Feature name prefix.
            
        Returns
        -------
        Dict[str, float]
            Frequency features.
        """
        features = {}
        
        # Compute FFT
        n = len(signal_data)
        fft_vals = np.fft.rfft(signal_data)
        fft_freqs = np.fft.rfftfreq(n, 1/self.fs)
        power = np.abs(fft_vals)**2
        
        # Total power
        features[f'{prefix}_total_power'] = np.sum(power)
        
        # Dominant frequency
        dominant_idx = np.argmax(power[1:]) + 1  # Skip DC component
        features[f'{prefix}_dominant_freq'] = fft_freqs[dominant_idx]
        
        # Power in bands
        bands = {
            'vlf': (0.003, 0.04),   # Very low frequency
            'lf': (0.04, 0.15),     # Low frequency
            'hf': (0.15, 0.4),      # High frequency
        }
        
        for band_name, (low, high) in bands.items():
            mask = (fft_freqs >= low) & (fft_freqs < high)
            band_power = np.sum(power[mask])
            features[f'{prefix}_{band_name}_power'] = band_power
        
        # LF/HF ratio
        lf_power = features.get(f'{prefix}_lf_power', 0)
        hf_power = features.get(f'{prefix}_hf_power', 1)
        features[f'{prefix}_lf_hf_ratio'] = lf_power / hf_power if hf_power > 0 else 0
        
        return features

