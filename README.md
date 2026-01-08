# Sleep Stage Monitoring System

A complete system for real-time sleep stage estimation using wearable sensor technology.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![PlatformIO](https://img.shields.io/badge/platformio-ESP32--S3-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🌙 Overview

This project combines machine learning model training with wearable hardware prototyping to create an end-to-end sleep monitoring system. The system uses IMU (accelerometer) and PPG (photoplethysmography) sensors to classify sleep stages in real-time.

### Key Features

- **Machine Learning Pipeline**: Train and evaluate sleep stage classification models
- **Wearable Device**: ESP32-S3 based prototype with IMU and PPG sensors
- **Real-time Classification**: On-device or BLE-streamed inference
- **DREAMT Dataset Integration**: Compatible with the PhysioNet DREAMT dataset

## 📁 Repository Structure

This repository is organized into two main components:

```
Capstone/
├── model-training/          # Machine Learning & Data Science
│   ├── src/                # Source code
│   │   ├── data/          # Data loading & preprocessing
│   │   ├── features/      # Feature extraction
│   │   ├── models/        # ML classifiers
│   │   ├── visualization/ # Plotting tools
│   │   └── utils/         # Helper functions
│   ├── notebooks/          # Jupyter notebooks
│   ├── configs/            # Training configurations
│   ├── models/             # Saved trained models
│   └── requirements.txt    # Python dependencies
│
├── wearable-prototype/      # Hardware & Firmware
│   ├── firmware/           # ESP32-S3 firmware (PlatformIO)
│   │   ├── src/           # Main application code
│   │   ├── include/       # Header files
│   │   └── platformio.ini # Build configuration
│   ├── hardware/           # Hardware design files
│   │   ├── schematics/    # Circuit schematics
│   │   ├── pcb/           # PCB layout
│   │   └── enclosure/     # 3D printable case
│   └── docs/               # Hardware documentation
│
├── Hardware Build.pdf       # Hardware build guide
└── README.md               # This file
```

## 🚀 Quick Start

### Model Training

```bash
# Navigate to model training directory
cd model-training

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch Jupyter notebook
jupyter notebook notebooks/01_explore_dreamt_data.ipynb
```

### Wearable Firmware

```bash
# Navigate to firmware directory
cd wearable-prototype/firmware

# Install PlatformIO CLI (if not installed)
pip install platformio

# Build and upload to ESP32-S3
pio run --target upload

# Monitor serial output
pio device monitor
```

## 📊 Model Training

### Dataset: DREAMT

The system is trained on the [DREAMT dataset](https://physionet.org/content/dreamt/) from PhysioNet:

- **100 participants** with sleep apnea
- **Wearable E4 signals**: BVP (64Hz), ACC (32Hz), EDA, TEMP, HR
- **Sleep stages**: Wake (W), N1, N2, N3, REM (R)

### Training Pipeline

```python
from src.data.loader import DREAMTLoader
from src.features.extractor import FeatureExtractor
from src.models.classifiers import SleepStageClassifier

# Load data
loader = DREAMTLoader('data/dreamt', resolution='64Hz')
df = loader.load_participant('P001')

# Extract features
extractor = FeatureExtractor(epoch_duration=30.0, fs=64.0)
features = extractor.extract_all_features(df)

# Train model
model = SleepStageClassifier(model_type='xgboost')
model.fit(X_train, y_train)

# Evaluate
metrics = model.evaluate(X_test, y_test)
```

## 🔧 Wearable Prototype

### Hardware Components

| Component | Model         | Purpose          |
| --------- | ------------- | ---------------- |
| MCU       | ESP32-S3-Zero | Processing + BLE |
| IMU       | MPU6050       | Motion sensing   |
| PPG       | MAX30102      | Heart rate       |
| Battery   | LiPo 500mAh   | Power            |

### System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Wearable Device                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────────────┐  │
│  │ MPU6050 │  │MAX30102 │  │      ESP32-S3-Zero      │  │
│  │  (IMU)  │  │  (PPG)  │  │  ┌───────────────────┐  │  │
│  └────┬────┘  └────┬────┘  │  │ Signal Processing │  │  │
│       │            │       │  └─────────┬─────────┘  │  │
│       └────────────┴───────┤  ┌─────────▼─────────┐  │  │
│                 I2C        │  │   BLE Streaming   │  │  │
│                            │  └─────────┬─────────┘  │  │
│                            └────────────┼────────────┘  │
└─────────────────────────────────────────┼───────────────┘
                                          │ Bluetooth
┌─────────────────────────────────────────▼───────────────┐
│                      Mobile App                          │
│  ┌─────────────────┐  ┌─────────────────────────────┐   │
│  │  Data Reception │─▶│   Sleep Stage Classifier    │   │
│  └─────────────────┘  └───────────────┬─────────────┘   │
│                                       ▼                  │
│                            ┌─────────────────┐          │
│                            │ Sleep Analysis  │          │
│                            └─────────────────┘          │
└──────────────────────────────────────────────────────────┘
```

## Device Specifications

| Metric        | Value                 |
| ------------- | --------------------- |
| Sampling Rate | IMU: 32Hz, PPG: 100Hz |
| Battery Life  | ~10 hours active      |
| BLE Range     | ~10 meters            |
| Data Rate     | ~2 kB/s streaming     |

## 📚 Documentation

- [Model Training README](model-training/README.md)
- [Wearable Prototype README](wearable-prototype/README.md)
- [Hardware Assembly Guide](wearable-prototype/docs/assembly.md)
- [Pin Connections](wearable-prototype/docs/pinout.md)
- [Sensor Calibration](wearable-prototype/docs/calibration.md)

## 🔬 References

### Dataset

```bibtex
@article{wang2024dreamt,
  title={DREAMT: Dataset for Real-time sleep stage EstimAtion 
         using Multisensor wearable Technology},
  author={Wang, Will Ke and others},
  booktitle={CHIL 2024},
  year={2024}
}
```

### Links

- [DREAMT on PhysioNet](https://physionet.org/content/dreamt/)
- [DREAMT Paper](https://proceedings.mlr.press/v248/wang24a.html)
- [ESP32-S3-Zero](https://www.waveshare.com/esp32-s3-zero.htm)

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 👥 Contributors

UCLA Capstone Project Team
