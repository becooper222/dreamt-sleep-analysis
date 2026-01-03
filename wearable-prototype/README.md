# Wearable Sleep Monitor Prototype

Hardware and firmware for a wearable sleep monitoring device using ESP32-S3.

## Overview

This directory contains everything needed to build a wearable device that captures IMU and PPG signals for real-time sleep stage estimation. The device is designed to interface with the trained sleep stage classification models.

## Hardware Components

Based on the Hardware Build guide, the prototype uses:

### Core Components

| Component | Model | Purpose |
|-----------|-------|---------|
| **Microcontroller** | [ESP32-S3-Zero](https://www.waveshare.com/esp32-s3-zero.htm) | Main processor with BLE/WiFi |
| **IMU Sensor** | MPU6050 / LSM6DS3 | 6-axis accelerometer + gyroscope |
| **PPG Sensor** | MAX30102 / MAX30105 | Heart rate and SpO2 sensor |
| **Power** | LiPo 3.7V 500mAh | Rechargeable battery |
| **Charging** | TP4056 module | USB-C charging circuit |

### Optional Components

| Component | Purpose |
|-----------|---------|
| EDA Sensor | Skin conductance measurement |
| Temperature Sensor | Skin temperature |
| OLED Display | Status/debug display |
| MicroSD Card | Local data logging |

## Directory Structure

```
wearable-prototype/
├── firmware/               # ESP32-S3 firmware (PlatformIO)
│   ├── src/               # Source code
│   │   ├── main.cpp       # Entry point
│   │   ├── sensors/       # Sensor drivers
│   │   ├── ble/          # BLE communication
│   │   └── processing/   # Signal processing
│   ├── lib/              # Libraries
│   ├── include/          # Header files
│   └── platformio.ini    # PlatformIO configuration
├── hardware/              # Hardware design files
│   ├── schematics/       # Circuit schematics (KiCad)
│   ├── pcb/             # PCB design files
│   └── enclosure/       # 3D printable enclosure
├── docs/                 # Documentation
│   ├── assembly.md      # Assembly instructions
│   ├── pinout.md        # Pin connections
│   └── calibration.md   # Sensor calibration
└── tests/               # Hardware test scripts
```

## Getting Started

### 1. Hardware Assembly

See [docs/assembly.md](docs/assembly.md) for step-by-step assembly instructions.

### 2. Firmware Setup

#### Install PlatformIO

```bash
# Using pip
pip install platformio

# Or using VS Code extension
# Install "PlatformIO IDE" from VS Code marketplace
```

#### Build and Flash

```bash
cd firmware

# Build the project
pio run

# Upload to ESP32-S3
pio run --target upload

# Monitor serial output
pio device monitor
```

### 3. Configure WiFi/BLE

Edit `firmware/src/config.h` with your settings:

```cpp
#define WIFI_SSID "your_network"
#define WIFI_PASSWORD "your_password"
#define BLE_DEVICE_NAME "SleepMonitor"
```

## Pin Connections

### ESP32-S3-Zero Pinout

| Pin | Function | Connected To |
|-----|----------|--------------|
| GPIO1 | I2C SDA | MPU6050 SDA, MAX30102 SDA |
| GPIO2 | I2C SCL | MPU6050 SCL, MAX30102 SCL |
| GPIO3 | INT | MPU6050 INT |
| GPIO4 | INT | MAX30102 INT |
| GPIO5 | LED | Status LED |
| 3V3 | Power | Sensors VCC |
| GND | Ground | Sensors GND |

## Data Format

### BLE Characteristics

The device exposes these BLE characteristics:

| UUID | Name | Description |
|------|------|-------------|
| 0x2A37 | Heart Rate | Real-time heart rate (bpm) |
| Custom | IMU Data | 6-axis accelerometer/gyro data |
| Custom | PPG Raw | Raw PPG signal for processing |
| Custom | Sleep Stage | Predicted sleep stage |

### Data Packet Structure

```
IMU Packet (20 bytes):
  [0-1]  timestamp (ms, uint16)
  [2-3]  acc_x (int16)
  [4-5]  acc_y (int16)
  [6-7]  acc_z (int16)
  [8-9]  gyro_x (int16)
  [10-11] gyro_y (int16)
  [12-13] gyro_z (int16)
  [14-17] reserved
  [18-19] checksum

PPG Packet (12 bytes):
  [0-1]  timestamp (ms, uint16)
  [2-5]  red_led (uint32)
  [6-9]  ir_led (uint32)
  [10-11] checksum
```

## Power Consumption

| Mode | Current | Battery Life (500mAh) |
|------|---------|----------------------|
| Active sensing | ~50mA | ~10 hours |
| BLE connected | ~30mA | ~16 hours |
| Deep sleep | ~10µA | ~5 years |

## Development Roadmap

- [x] Basic sensor reading
- [x] BLE data streaming
- [ ] On-device signal processing
- [ ] Edge inference with TFLite
- [ ] Sleep stage classification
- [ ] Mobile app integration
- [ ] PCB design
- [ ] 3D printed enclosure

## References

- [ESP32-S3-Zero Datasheet](https://www.waveshare.com/wiki/ESP32-S3-Zero)
- [MAX30102 Application Guide](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX30102.pdf)
- [MPU6050 Datasheet](https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/)

## License

MIT License - See LICENSE file for details.

