# Sleep Stage Model Training

Machine learning toolkit for sleep stage estimation using wearable sensor data from the DREAMT dataset.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Overview

This module contains all the machine learning infrastructure for training sleep stage classification models using IMU and PPG data from wearable devices.

### Dataset: DREAMT

The **DREAMT** (Dataset for Real-time sleep stage EstimAtion using Multisensor wearable Technology) dataset from PhysioNet contains:

- **100 participants** with sleep apnea
- **Wearable E4 sensor data**: BVP, ACC (X/Y/Z), EDA, TEMP, HR
- **Sleep stage labels**: W (Wake), N1, N2, N3, R (REM)

## Directory Structure

```
model-training/
├── configs/                # Training configurations
│   └── default_config.yaml
├── data/                   # Dataset storage (symlink to main data/)
├── models/                 # Saved trained models
├── notebooks/              # Jupyter notebooks for exploration
│   └── 01_explore_dreamt_data.ipynb
├── scripts/                # Training and evaluation scripts
├── src/                    # Source code
│   ├── data/              # Data loading utilities
│   │   ├── loader.py      # DREAMT data loader
│   │   └── preprocessing.py
│   ├── features/          # Feature extraction
│   │   └── extractor.py
│   ├── models/            # Model definitions
│   │   └── classifiers.py
│   ├── visualization/     # Plotting tools
│   │   ├── signals.py
│   │   └── sleep.py
│   └── utils/             # Helper functions
├── requirements.txt
└── README.md
```

## Installation

```bash
cd model-training
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

### 1. Load Data

```python
from src.data.loader import DREAMTLoader

loader = DREAMTLoader('data/dreamt', resolution='64Hz')
df = loader.load_participant('P001')
```

### 2. Extract Features

```python
from src.features.extractor import FeatureExtractor

extractor = FeatureExtractor(epoch_duration=30.0, fs=64.0)
features = extractor.extract_all_features(df)
```

### 3. Train Model

```python
from src.models.classifiers import SleepStageClassifier

model = SleepStageClassifier(model_type='xgboost')
model.fit(X_train, y_train)
```

## Features Extracted

### IMU Features (per epoch)
- Statistical: mean, std, min, max, range, IQR
- Shape: skewness, kurtosis
- Activity: energy, zero crossings, peak count

### PPG Features (per epoch)
- Heart rate: mean HR, std HR, min HR, max HR
- HRV time-domain: RMSSD, SDNN, pNN50
- HRV frequency-domain: LF power, HF power, LF/HF ratio

## Sleep Stages

| Stage | Description | Typical Duration |
|-------|-------------|------------------|
| W | Wake | Variable |
| N1 | Light sleep | 5-10% of night |
| N2 | Medium sleep | 45-55% of night |
| N3 | Deep sleep | 15-25% of night |
| R | REM sleep | 20-25% of night |

## Model Performance

Target metrics for sleep stage classification:

| Model | Accuracy | Macro F1 | Cohen's κ |
|-------|----------|----------|-----------|
| XGBoost | ~75% | ~0.65 | ~0.60 |
| LightGBM | ~75% | ~0.65 | ~0.60 |
| Random Forest | ~72% | ~0.60 | ~0.55 |

## References

- [DREAMT Paper (CHIL 2024)](https://proceedings.mlr.press/v248/wang24a.html)
- [PhysioNet Dataset](https://physionet.org/content/dreamt/)
- [DREAMT_FE Feature Extraction](https://github.com/WillKeWang/DREAMT_FE)

