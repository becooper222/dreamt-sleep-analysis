# ESP32-S3-Zero Pinout Reference

Pin mapping for the sleep monitor wearable.

## ESP32-S3-Zero Module

The Waveshare ESP32-S3-Zero is a compact development board with the ESP32-S3 chip.

### Key Specifications

| Feature | Specification |
|---------|---------------|
| MCU | ESP32-S3 (Xtensa LX7 dual-core) |
| Frequency | 240 MHz |
| Flash | 4-16 MB |
| RAM | 512 KB SRAM |
| Wireless | WiFi 802.11 b/g/n, Bluetooth 5 (LE) |
| USB | Native USB-OTG (USB-C connector) |

## Pin Assignments

### Used Pins

| GPIO | Function | Direction | Description |
|------|----------|-----------|-------------|
| 0 | BOOT | Input | Boot mode select (pull low for flash) |
| 1 | I2C_SDA | Bidirectional | I2C data line (sensors) |
| 2 | I2C_SCL | Output | I2C clock line (sensors) |
| 3 | MPU_INT | Input | MPU6050 interrupt |
| 4 | PPG_INT | Input | MAX30102 interrupt |
| 5 | LED_STATUS | Output | Status LED |
| 6 | BATT_ADC | Input | Battery voltage monitor |

### Available Pins

These pins are available for expansion:

| GPIO | Notes |
|------|-------|
| 7-14 | General purpose I/O |
| 15-16 | Can be used for SPI |
| 17-18 | UART TX/RX available |
| 19-21 | USB (default use, can be freed) |

### Special Pins

| GPIO | Function |
|------|----------|
| 0 | Boot mode (strapping pin) |
| 19 | USB D- |
| 20 | USB D+ |
| 21 | USB JTAG |

## I2C Bus

The I2C bus is shared between sensors:

```
3.3V ─┬─── 4.7kΩ ──┬─── SDA ─── GPIO1
      │            │
      └─── 4.7kΩ ──┴─── SCL ─── GPIO2
```

### Connected Devices

| Address | Device | Description |
|---------|--------|-------------|
| 0x57 | MAX30102 | PPG sensor |
| 0x68 | MPU6050 | IMU (AD0 low) |
| 0x69 | MPU6050 | IMU (AD0 high) |

## Power Pins

| Pin | Voltage | Max Current | Notes |
|-----|---------|-------------|-------|
| 3V3 | 3.3V | 500mA | Regulated output |
| 5V/VIN | 5V | - | USB input or battery |
| GND | 0V | - | Ground reference |

## Sensor Connections

### MPU6050 (IMU)

| MPU6050 Pin | ESP32 Pin | Notes |
|-------------|-----------|-------|
| VCC | 3V3 | 3.3V power |
| GND | GND | Ground |
| SCL | GPIO2 | I2C clock |
| SDA | GPIO1 | I2C data |
| INT | GPIO3 | Interrupt (optional) |
| AD0 | GND | Address select (0x68) |

### MAX30102 (PPG)

| MAX30102 Pin | ESP32 Pin | Notes |
|--------------|-----------|-------|
| VIN | 3V3 | 3.3V power |
| GND | GND | Ground |
| SCL | GPIO2 | I2C clock |
| SDA | GPIO1 | I2C data |
| INT | GPIO4 | Interrupt (optional) |

## GPIO Configuration Code

```cpp
// Pin definitions
#define I2C_SDA_PIN         1
#define I2C_SCL_PIN         2
#define MPU6050_INT_PIN     3
#define MAX30102_INT_PIN    4
#define LED_STATUS_PIN      5
#define BATTERY_ADC_PIN     6

void setupPins() {
    // Status LED
    pinMode(LED_STATUS_PIN, OUTPUT);
    digitalWrite(LED_STATUS_PIN, LOW);
    
    // Interrupt pins
    pinMode(MPU6050_INT_PIN, INPUT);
    pinMode(MAX30102_INT_PIN, INPUT);
    
    // I2C (configured by Wire library)
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    
    // Battery ADC
    analogReadResolution(12);  // 12-bit ADC
    analogSetAttenuation(ADC_11db);  // Full 3.3V range
}
```

## Power Consumption

| Mode | Current Draw |
|------|-------------|
| Active (CPU + sensors) | ~50 mA |
| BLE advertising | ~30 mA |
| BLE connected streaming | ~40 mA |
| Light sleep | ~1 mA |
| Deep sleep | ~10 µA |

## Expansion Options

### SPI Interface (for SD card or display)

| Function | GPIO |
|----------|------|
| MOSI | 11 |
| MISO | 13 |
| SCK | 12 |
| CS | 10 |

### UART (for debugging or external module)

| Function | GPIO |
|----------|------|
| TX | 17 |
| RX | 18 |

