# DREAMT Sleep Stage Analysis

A Python toolkit for analyzing IMU and PPG signals from the **DREAMT** dataset for real-time sleep stage estimation research.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Overview

This repository provides tools for working with the **DREAMT** (Dataset for Real-time sleep stage EstimAtion using Multisensor wearable Technology) dataset from PhysioNet. The dataset contains wearable sensor data from 100 participants with sleep apnea.

### Dataset Signals

| Signal | Sampling Rate | Description |
|--------|--------------|-------------|
| **BVP** | 64 Hz | Blood Volume Pulse (PPG) |
| **ACC_X/Y/Z** | 32 Hz | Triaxial accelerometry (IMU) |
| **EDA** | 4 Hz | Electrodermal Activity |
| **TEMP** | 4 Hz | Skin Temperature |
| **HR** | 1 Hz | Heart Rate (derived) |
| **IBI** | Variable | Inter-beat Interval (derived) |

### Sleep Stages

- **W**: Wake
- **N1**: NREM Stage 1 (Light Sleep)
- **N2**: NREM Stage 2 (Medium Sleep)
- **N3**: NREM Stage 3 (Deep Sleep)
- **R**: REM (Rapid Eye Movement)

## Installation

### 1. Clone the Repository

```bash
cd /path/to/your/projects
git clone <your-repo-url>
cd Capstone
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the DREAMT Dataset

1. Go to [PhysioNet DREAMT Dataset](https://physionet.org/content/dreamt/)
2. Sign the data use agreement
3. Download the dataset
4. Extract to `data/dreamt/` in this repository

Expected structure:
```
Capstone/
├── data/
│   └── dreamt/
│       ├── data_64Hz/
│       │   ├── P001.csv
│       │   ├── P002.csv
│       │   └── ...
│       ├── data_100Hz/
│       │   └── ...
│       └── participant_info.csv
├── src/
├── notebooks/
└── ...
```

## Quick Start

### Using the Jupyter Notebook

```bash
jupyter notebook notebooks/01_explore_dreamt_data.ipynb
```

### Using Python Scripts

```python
from src.data.loader import DREAMTLoader
from src.visualization.signals import SignalVisualizer

# Load data
loader = DREAMTLoader('data/dreamt', resolution='64Hz')
df = loader.load_participant('P001')

# Extract signals
imu_data = loader.get_imu_signals(df)
ppg_data = loader.get_ppg_signals(df)
time = loader.get_time_vector(df)

# Visualize
viz = SignalVisualizer()
fig = viz.plot_imu_signals(
    time,
    imu_data['ACC_X'].values,
    imu_data['ACC_Y'].values,
    imu_data['ACC_Z'].values,
    title="IMU Signals"
)
```

## Project Structure

```
Capstone/
├── data/                   # Dataset storage (not tracked in git)
│   └── dreamt/
├── notebooks/              # Jupyter notebooks for exploration
│   └── 01_explore_dreamt_data.ipynb
├── src/                    # Source code
│   ├── data/              # Data loading utilities
│   │   ├── loader.py      # DREAMT data loader
│   │   └── preprocessing.py
│   ├── visualization/     # Plotting tools
│   │   ├── signals.py     # IMU/PPG visualization
│   │   └── sleep.py       # Hypnograms and sleep metrics
│   └── utils/             # Helper functions
├── scripts/               # Standalone scripts
├── configs/               # Configuration files
├── requirements.txt       # Python dependencies
└── README.md
```

## Features

### Data Loading (`src/data/loader.py`)

- Load single or multiple participants
- Extract IMU, PPG, and sleep stage data
- Compute epoch-based features
- Handle both 64Hz and 100Hz resolutions

### Signal Preprocessing (`src/data/preprocessing.py`)

- Signal resampling
- Normalization (z-score, min-max, robust)
- Bandpass/lowpass filtering
- PPG peak detection
- Activity count computation

### Visualization (`src/visualization/`)

- **IMU Signals**: Plot accelerometer data with sleep stage overlays
- **PPG Signals**: Visualize blood volume pulse with heart rate
- **Combined Views**: Multi-signal synchronized plots
- **Hypnograms**: Sleep architecture visualization
- **Stage Distribution**: Bar charts and pie charts
- **Spectrograms**: Frequency analysis

### Sleep Metrics (`src/visualization/sleep.py`)

Compute standard sleep metrics:
- Total Sleep Time (TST)
- Sleep Onset Latency (SOL)
- Wake After Sleep Onset (WASO)
- Sleep Efficiency
- REM Latency
- Time in each stage

## Usage Examples

### Load and Explore Data

```python
from src.data.loader import DREAMTLoader

loader = DREAMTLoader('data/dreamt', resolution='64Hz')
print(f"Found {len(loader.participants)} participants")

# Load first participant
df = loader.load_participant(loader.participants[0])
print(f"Columns: {df.columns.tolist()}")
print(f"Duration: {len(df) / 64 / 3600:.1f} hours")
```

### Visualize Sleep Hypnogram

```python
from src.visualization.sleep import plot_hypnogram, compute_sleep_metrics
import numpy as np

# Get epoch-level stages
epochs = loader.get_epoch_data(df)
stages = np.array([e['Sleep_Stage'].mode().iloc[0] for e in epochs])

# Plot
fig = plot_hypnogram(stages, title="Sleep Stages")

# Compute metrics
metrics = compute_sleep_metrics(stages)
print(f"Sleep Efficiency: {metrics['sleep_efficiency_pct']:.1f}%")
```

### Filter PPG Signal

```python
from src.data.preprocessing import bandpass_filter

bvp = df['BVP'].values
fs = 64  # Hz

# Bandpass filter for heart rate range (0.5-4 Hz = 30-240 bpm)
bvp_filtered = bandpass_filter(bvp, lowcut=0.5, highcut=4.0, fs=fs)
```

## References

### Dataset Citation

```bibtex
@article{wang2024dreamt,
  title={DREAMT: Dataset for Real-time sleep stage EstimAtion using Multisensor wearable Technology},
  author={Wang, Will Ke and Yang, Jiamu and Hershkovich, Leeor and Jeong, Hayoung and Chen, Bill and Singh, Karnika and Roghanizad, Ali R and Shandhi, Md Mobashir Hasan and Spector, Andrew R and Dunn, Jessilyn},
  booktitle={Proceedings of the fifth Conference on Health, Inference, and Learning},
  pages={380--396},
  year={2024},
  organization={PMLR}
}
```

### Useful Links

- [DREAMT on PhysioNet](https://physionet.org/content/dreamt/)
- [DREAMT Paper (CHIL 2024)](https://proceedings.mlr.press/v248/wang24a.html)
- [DREAMT_FE Feature Extraction](https://github.com/WillKeWang/DREAMT_FE)

## License

This project is licensed under the MIT License. The DREAMT dataset has its own license - please refer to PhysioNet for data usage terms.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

