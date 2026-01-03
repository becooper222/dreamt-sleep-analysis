# On-Device Sleep Stage Detection - Implementation Guide

This guide documents the complete pipeline for running real-time sleep stage classification on the ESP32-S3 wearable device.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ESP32-S3 Wearable Device                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌────────────────────┐    ┌───────────────────┐   │
│  │   SENSORS    │    │  FEATURE EXTRACTOR │    │  TFLITE MICRO     │   │
│  │              │    │                    │    │                   │   │
│  │  MPU6050     │───▶│  72 Features       │───▶│  4-Class MLP      │   │
│  │  (IMU)       │    │  - 50 IMU features │    │  - Wake           │   │
│  │              │    │  - 22 PPG features │    │  - Light (N1+N2)  │   │
│  │  MAX30102    │    │                    │    │  - Deep (N3)      │   │
│  │  (PPG)       │    │  30-second epochs  │    │  - REM            │   │
│  └──────────────┘    └────────────────────┘    └─────────┬─────────┘   │
│                                                          │             │
│                                                          ▼             │
│                                              ┌───────────────────┐     │
│                                              │   BLE Broadcast   │     │
│                                              │   Sleep Stage +   │     │
│                                              │   Confidence      │     │
│                                              └───────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Classification Scheme

| Class | Label | Description | Sleep Stages |
|-------|-------|-------------|--------------|
| 0 | Wake | Awake | W |
| 1 | Light | Light Sleep | N1 + N2 |
| 2 | Deep | Deep Sleep | N3 |
| 3 | REM | REM Sleep | R |

This 4-class "clinical-lite" scheme merges N1 and N2 into a single "Light Sleep" category, which is more practical for wearable devices since distinguishing N1 from N2 is challenging even with EEG.

## Feature Set (72 features)

### IMU Features (50 features)

For each axis (X, Y, Z) and magnitude, we compute 12 statistical features:

| Feature | Description |
|---------|-------------|
| mean | Average value |
| std | Standard deviation |
| min | Minimum value |
| max | Maximum value |
| range | Max - Min |
| median | Median value |
| iqr | Interquartile range (Q3 - Q1) |
| skew | Skewness (asymmetry) |
| kurtosis | Kurtosis (tailedness) |
| energy | Sum of squares |
| rms | Root mean square |
| zero_crossings | Crossings around mean |

Plus 2 activity-specific features:
- `imu_activity_count`: Sum of absolute differences in magnitude
- `imu_movement_intensity`: Std of magnitude

### PPG Features (22 features)

| Category | Features |
|----------|----------|
| PPG Signal (12) | Same 12 stats as IMU applied to raw PPG |
| Heart Rate (5) | hr_mean, hr_std, hr_min, hr_max, hr_range |
| HRV (5) | hrv_mean_ibi, hrv_sdnn, hrv_rmssd, hrv_pnn50, hrv_pnn20 |

## Step-by-Step Deployment

### Step 1: Train the Model

```bash
cd model-training

# Activate virtual environment
source venv/bin/activate

# Install TensorFlow (if not already)
pip install tensorflow>=2.13.0

# Train the model
python scripts/train_tflite_model.py \
    --data_dir ../data/dreamt \
    --output_dir ../models/tflite_4class \
    --epochs 100 \
    --hidden_layers 64 32 16 \
    --quantize
```

This produces:
- `keras_model/` - Full Keras model for further development
- `sleep_model.tflite` - Quantized TFLite model (~10-30 KB)
- `scaler_params.h` - C++ header with normalization parameters
- `feature_list.txt` - Feature ordering specification
- `metrics.json` - Model performance metrics

### Step 2: Convert Model to C Header

```bash
# Convert TFLite model to C array
xxd -i models/tflite_4class/sleep_model.tflite > \
    wearable-prototype/firmware/include/model_data.h
```

### Step 3: Copy Scaler Parameters

```bash
cp models/tflite_4class/scaler_params.h \
   wearable-prototype/firmware/include/scaler_params.h
```

### Step 4: Build and Flash Firmware

```bash
cd wearable-prototype/firmware

# Build with edge inference enabled
pio run

# Upload to ESP32-S3
pio run --target upload

# Monitor serial output
pio device monitor
```

### Step 5: Verify Operation

You should see output like:
```
[SYSTEM] Sleep Monitor Wearable v0.1.0
[IMU] Initializing MPU6050... OK
[PPG] Initializing MAX30102... OK
[BLE] Initializing... OK
[INFERENCE] Feature extractor... OK
[INFERENCE] TFLite classifier... OK
[INFERENCE] Model arena: 8192 bytes

[STATUS] HR=72 | Sleep=--- | Epoch=15% | BLE=advertising
[STATUS] HR=71 | Sleep=--- | Epoch=48% | BLE=advertising
[STATUS] HR=70 | Sleep=--- | Epoch=82% | BLE=connected
[SLEEP] Stage: Light (confidence: 78.5%, inference: 12.34ms)
[SLEEP] Probabilities: W=0.12 L=0.79 D=0.05 R=0.04
```

## Memory Budget

| Component | RAM Usage | Flash Usage |
|-----------|-----------|-------------|
| Feature Buffers | ~20 KB | - |
| TFLite Arena | ~32 KB | - |
| Model Weights | - | ~15-30 KB |
| Scaler Params | ~1 KB | ~1 KB |
| **Total** | **~53 KB** | **~16-31 KB** |

ESP32-S3 has 512 KB SRAM, so this fits comfortably.

## Configuration Options

Edit `firmware/include/config.h`:

```cpp
// Enable/disable on-device inference
#define ENABLE_EDGE_INFERENCE   true

// Epoch duration (must match training)
#define EPOCH_DURATION_SEC      30

// Sensor sample rates
#define IMU_SAMPLE_RATE_HZ      32
#define PPG_SAMPLE_RATE_HZ      100
```

## Troubleshooting

### Model fails to initialize
- Check that `model_data.h` contains actual model bytes (not placeholder)
- Verify TFLite library is installed correctly
- Increase `TENSOR_ARENA_SIZE` if "Arena allocation failed"

### Features don't match training
- Verify sensor sample rates match Python training config
- Check that feature order in C++ matches `feature_list.txt`
- Ensure scaler params are from the same training run

### Poor accuracy
- Collect more training data
- Tune hyperparameters (hidden layers, dropout, etc.)
- Check for sensor noise/artifacts
- Consider longer epochs (60s instead of 30s)

## Files Reference

### Model Training (`model-training/`)
- `src/models/tflite_model.py` - TensorFlow MLP class
- `scripts/train_tflite_model.py` - Training script
- `src/features/extractor.py` - Python feature extraction

### Firmware (`wearable-prototype/firmware/`)
- `src/processing/feature_extractor.h` - C++ feature extraction
- `src/processing/sleep_classifier.h` - TFLite inference wrapper
- `include/model_data.h` - Model bytes (generated)
- `include/scaler_params.h` - Normalization params (generated)
- `include/config.h` - Configuration options

## Next Steps

1. **BLE Sleep Stage Characteristic** - Add a custom BLE characteristic to broadcast sleep stage predictions
2. **Mobile App** - Build a companion app to receive and display sleep data
3. **Sleep History** - Add local storage (SPIFFS/SD) for overnight recording
4. **Power Optimization** - Reduce sample rates during light sleep periods
5. **Model Improvements** - Experiment with larger models, different architectures

## References

- [DREAMT Dataset (PhysioNet)](https://physionet.org/content/dreamt/)
- [TensorFlow Lite for Microcontrollers](https://www.tensorflow.org/lite/microcontrollers)
- [ESP32-S3 TFLite Guide](https://github.com/espressif/esp-tflite-micro)

