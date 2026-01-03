"""
DREAMT Dataset Loader
=====================

Utilities for loading and parsing the DREAMT dataset from PhysioNet.
The dataset contains wearable sensor data (E4) for sleep stage estimation.

Dataset structure:
- data_64Hz/: E4 signals resampled to 64 Hz
- data_100Hz/: E4 + PSG signals resampled to 100 Hz

Wearable E4 Signals:
- BVP (64 Hz): Blood Volume Pulse from PPG sensor
- ACC_X, ACC_Y, ACC_Z (32 Hz): Triaxial accelerometry
- EDA (4 Hz): Electrodermal Activity
- TEMP (4 Hz): Skin Temperature
- HR (1 Hz): Heart Rate
- IBI: Inter-beat Interval
- Sleep_Stage: W, N1, N2, N3, R, P, Missing
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from tqdm import tqdm


class DREAMTLoader:
    """
    Data loader for the DREAMT (Dataset for Real-time sleep stage 
    EstimAtion using Multisensor wearable Technology) dataset.
    
    Parameters
    ----------
    data_dir : str or Path
        Path to the root directory of the DREAMT dataset.
    resolution : str, optional
        Data resolution to use: '64Hz' or '100Hz'. Default is '64Hz'.
    
    Attributes
    ----------
    data_dir : Path
        Root directory of the dataset.
    resolution : str
        Selected data resolution.
    participants : List[str]
        List of available participant IDs.
        
    Examples
    --------
    >>> loader = DREAMTLoader('/path/to/dreamt')
    >>> df = loader.load_participant('P001')
    >>> imu_data = loader.get_imu_signals(df)
    >>> ppg_data = loader.get_ppg_signals(df)
    """
    
    # Signal column definitions
    IMU_COLUMNS = ['ACC_X', 'ACC_Y', 'ACC_Z']
    PPG_COLUMNS = ['BVP']
    DERIVED_COLUMNS = ['HR', 'IBI']
    OTHER_COLUMNS = ['EDA', 'TEMP']
    LABEL_COLUMN = 'Sleep_Stage'
    TIMESTAMP_COLUMN = 'TIMESTAMP'
    
    # Sleep stage mapping
    SLEEP_STAGES = {
        'P': 'Preparation',
        'W': 'Wake',
        'N1': 'NREM Stage 1',
        'N2': 'NREM Stage 2', 
        'N3': 'NREM Stage 3',
        'R': 'REM',
        'Missing': 'Missing'
    }
    
    # Numeric encoding for sleep stages
    STAGE_ENCODING = {
        'P': -1,
        'W': 0,
        'N1': 1,
        'N2': 2,
        'N3': 3,
        'R': 4,
        'Missing': -2
    }
    
    def __init__(self, data_dir: Union[str, Path], resolution: str = '64Hz'):
        """Initialize the DREAMT data loader."""
        self.data_dir = Path(data_dir)
        self.resolution = resolution
        self._validate_data_dir()
        self.participants = self._discover_participants()
        
    def _validate_data_dir(self) -> None:
        """Validate the data directory structure."""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        resolution_dir = self.data_dir / f"data_{self.resolution}"
        if not resolution_dir.exists():
            # Try to find available resolutions
            available = [d.name for d in self.data_dir.iterdir() 
                        if d.is_dir() and d.name.startswith('data_')]
            if available:
                raise ValueError(
                    f"Resolution '{self.resolution}' not found. "
                    f"Available: {available}"
                )
            else:
                raise FileNotFoundError(
                    f"No data folders found in {self.data_dir}. "
                    f"Expected 'data_64Hz' or 'data_100Hz' folders."
                )
    
    def _discover_participants(self) -> List[str]:
        """Discover available participant files in the dataset."""
        data_path = self.data_dir / f"data_{self.resolution}"
        participants = []
        
        for f in sorted(data_path.iterdir()):
            if f.is_file() and f.suffix == '.csv':
                participants.append(f.stem)
        
        return participants
    
    def load_participant(
        self, 
        participant_id: str,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Load data for a specific participant.
        
        Parameters
        ----------
        participant_id : str
            The participant identifier (e.g., 'P001' or just the filename stem).
        columns : List[str], optional
            Specific columns to load. If None, loads all columns.
            
        Returns
        -------
        pd.DataFrame
            DataFrame containing the participant's data.
        """
        file_path = self.data_dir / f"data_{self.resolution}" / f"{participant_id}.csv"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Participant data not found: {file_path}")
        
        df = pd.read_csv(file_path, usecols=columns)
        return df
    
    def load_all_participants(
        self,
        columns: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Load data for all participants.
        
        Parameters
        ----------
        columns : List[str], optional
            Specific columns to load.
        show_progress : bool
            Whether to show a progress bar.
            
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary mapping participant IDs to their DataFrames.
        """
        data = {}
        iterator = tqdm(self.participants) if show_progress else self.participants
        
        for pid in iterator:
            try:
                data[pid] = self.load_participant(pid, columns)
            except Exception as e:
                print(f"Warning: Failed to load {pid}: {e}")
                
        return data
    
    def get_imu_signals(
        self, 
        df: pd.DataFrame,
        include_timestamp: bool = True
    ) -> pd.DataFrame:
        """
        Extract IMU (accelerometer) signals from a participant DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            Participant data DataFrame.
        include_timestamp : bool
            Whether to include the timestamp column.
            
        Returns
        -------
        pd.DataFrame
            DataFrame with ACC_X, ACC_Y, ACC_Z columns (and optionally TIMESTAMP).
        """
        cols = self.IMU_COLUMNS.copy()
        if include_timestamp and self.TIMESTAMP_COLUMN in df.columns:
            cols = [self.TIMESTAMP_COLUMN] + cols
            
        available_cols = [c for c in cols if c in df.columns]
        return df[available_cols].copy()
    
    def get_ppg_signals(
        self, 
        df: pd.DataFrame,
        include_derived: bool = True,
        include_timestamp: bool = True
    ) -> pd.DataFrame:
        """
        Extract PPG (BVP) signals from a participant DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            Participant data DataFrame.
        include_derived : bool
            Whether to include HR and IBI if available.
        include_timestamp : bool
            Whether to include the timestamp column.
            
        Returns
        -------
        pd.DataFrame
            DataFrame with BVP (and optionally HR, IBI, TIMESTAMP).
        """
        cols = self.PPG_COLUMNS.copy()
        if include_derived:
            cols.extend([c for c in self.DERIVED_COLUMNS if c in df.columns])
        if include_timestamp and self.TIMESTAMP_COLUMN in df.columns:
            cols = [self.TIMESTAMP_COLUMN] + cols
            
        available_cols = [c for c in cols if c in df.columns]
        return df[available_cols].copy()
    
    def get_sleep_stages(
        self, 
        df: pd.DataFrame,
        as_numeric: bool = False
    ) -> pd.Series:
        """
        Extract sleep stage labels.
        
        Parameters
        ----------
        df : pd.DataFrame
            Participant data DataFrame.
        as_numeric : bool
            If True, convert stages to numeric encoding.
            
        Returns
        -------
        pd.Series
            Sleep stage labels.
        """
        if self.LABEL_COLUMN not in df.columns:
            raise ValueError(f"Sleep stage column '{self.LABEL_COLUMN}' not found")
            
        stages = df[self.LABEL_COLUMN].copy()
        
        if as_numeric:
            stages = stages.map(self.STAGE_ENCODING)
            
        return stages
    
    def get_time_vector(self, df: pd.DataFrame) -> np.ndarray:
        """Get the timestamp vector in seconds."""
        if self.TIMESTAMP_COLUMN in df.columns:
            return df[self.TIMESTAMP_COLUMN].values
        else:
            # Create time vector based on sampling rate
            sr = 64 if self.resolution == '64Hz' else 100
            return np.arange(len(df)) / sr
    
    def compute_imu_magnitude(self, df: pd.DataFrame) -> np.ndarray:
        """
        Compute the magnitude of the acceleration vector.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing ACC_X, ACC_Y, ACC_Z columns.
            
        Returns
        -------
        np.ndarray
            Acceleration magnitude at each time point.
        """
        acc_x = df['ACC_X'].values
        acc_y = df['ACC_Y'].values
        acc_z = df['ACC_Z'].values
        
        return np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
    
    def get_epoch_data(
        self,
        df: pd.DataFrame,
        epoch_duration: float = 30.0
    ) -> List[pd.DataFrame]:
        """
        Split data into epochs (commonly 30 seconds for sleep staging).
        
        Parameters
        ----------
        df : pd.DataFrame
            Participant data DataFrame.
        epoch_duration : float
            Duration of each epoch in seconds.
            
        Returns
        -------
        List[pd.DataFrame]
            List of DataFrames, one per epoch.
        """
        time = self.get_time_vector(df)
        sr = 64 if self.resolution == '64Hz' else 100
        samples_per_epoch = int(epoch_duration * sr)
        
        epochs = []
        for i in range(0, len(df), samples_per_epoch):
            epoch = df.iloc[i:i + samples_per_epoch].copy()
            if len(epoch) == samples_per_epoch:
                epochs.append(epoch)
                
        return epochs
    
    def get_participant_info(self) -> Optional[pd.DataFrame]:
        """
        Load participant metadata if available.
        
        Returns
        -------
        pd.DataFrame or None
            Participant information DataFrame, or None if not found.
        """
        info_path = self.data_dir / 'participant_info.csv'
        if info_path.exists():
            return pd.read_csv(info_path)
        return None
    
    def __repr__(self) -> str:
        return (
            f"DREAMTLoader(data_dir='{self.data_dir}', "
            f"resolution='{self.resolution}', "
            f"n_participants={len(self.participants)})"
        )

