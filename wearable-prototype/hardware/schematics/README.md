# Hardware Schematics

This directory contains the circuit schematics for the sleep monitor wearable.

## Files

- `sleep_monitor.kicad_pro` - KiCad project file
- `sleep_monitor.kicad_sch` - Main schematic
- `sleep_monitor.pdf` - PDF export of schematic

## Schematic Overview

### Power Section
- USB-C input with ESD protection
- TP4056 LiPo charging circuit
- 3.3V LDO regulator
- Battery monitoring ADC

### MCU Section
- ESP32-S3-Zero module
- USB data lines
- Boot mode circuitry

### Sensor Section
- I2C bus with pull-ups
- MPU6050 IMU connection
- MAX30102 PPG sensor connection
- Optional EDA sensor pads

### LED and UI
- Status RGB LED
- Button for user input

## Bill of Materials

| Qty | Part | Package | Value | Notes |
|-----|------|---------|-------|-------|
| 1 | ESP32-S3-Zero | Module | - | Waveshare |
| 1 | MPU6050 | Module | - | 6-axis IMU |
| 1 | MAX30102 | Module | - | PPG sensor |
| 1 | TP4056 | Module | - | LiPo charger |
| 1 | LiPo Battery | - | 500mAh | 3.7V |
| 2 | Resistor | 0603 | 4.7kΩ | I2C pullups |
| 1 | Resistor | 0603 | 330Ω | LED current limit |
| 1 | LED | 0805 | Blue | Status indicator |
| 1 | Capacitor | 0603 | 100nF | Decoupling |
| 1 | Capacitor | 0805 | 10µF | Power filter |

## Design Notes

1. **I2C Pull-ups**: 4.7kΩ recommended for 400kHz operation
2. **Power Decoupling**: 100nF ceramic close to each IC
3. **PPG Placement**: Sensor must be flush with enclosure for skin contact
4. **Antenna Clearance**: Keep ground plane away from ESP32 antenna area

