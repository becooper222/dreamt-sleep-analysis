# Hardware Assembly Guide

Step-by-step instructions for assembling the sleep monitor wearable.

## Required Components

### Core Components

1. **ESP32-S3-Zero** (Waveshare)
   - Compact form factor with built-in USB-C
   - 240MHz dual-core processor
   - Built-in WiFi and Bluetooth 5.0

2. **MPU6050 Module**
   - 6-axis IMU (accelerometer + gyroscope)
   - I2C interface
   - 3.3V operation

3. **MAX30102 Module**
   - PPG sensor for heart rate and SpO2
   - I2C interface
   - Integrated LEDs

4. **LiPo Battery** (3.7V, 500mAh recommended)
   - JST connector preferred
   - Rechargeable lithium polymer

5. **TP4056 Charging Module** (optional)
   - USB-C or Micro-USB input
   - Charging and protection circuit

### Additional Materials

- Jumper wires (22 AWG recommended)
- Prototype PCB or breadboard for testing
- Soldering iron and solder
- Heat shrink tubing
- Wrist strap or enclosure

## Pin Connections

### I2C Bus (Shared)

| ESP32-S3-Zero | MPU6050 | MAX30102 |
|---------------|---------|----------|
| GPIO1 (SDA)   | SDA     | SDA      |
| GPIO2 (SCL)   | SCL     | SCL      |
| 3V3           | VCC     | VCC      |
| GND           | GND     | GND      |

### Interrupts (Optional)

| ESP32-S3-Zero | Sensor  | Purpose |
|---------------|---------|---------|
| GPIO3         | MPU6050 INT | Motion detection |
| GPIO4         | MAX30102 INT | Data ready |

### Status LED

| ESP32-S3-Zero | Component |
|---------------|-----------|
| GPIO5         | LED + 330Ω resistor to GND |

### Power (with TP4056)

| TP4056 | ESP32-S3-Zero | Battery |
|--------|---------------|---------|
| OUT+   | 5V/VIN        | -       |
| OUT-   | GND           | -       |
| BAT+   | -             | + (Red) |
| BAT-   | -             | - (Black) |

## Assembly Steps

### Step 1: Test Components

Before soldering, test each component individually:

1. Connect ESP32-S3-Zero via USB and verify it appears as a serial device
2. Test I2C sensors with a scanner sketch:

```cpp
#include <Wire.h>

void setup() {
    Serial.begin(115200);
    Wire.begin(1, 2);  // SDA, SCL
    
    Serial.println("I2C Scanner");
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("Found device at 0x%02X\n", addr);
        }
    }
}

void loop() {}
```

Expected addresses:
- MPU6050: 0x68 (or 0x69 if AD0 is HIGH)
- MAX30102: 0x57

### Step 2: Wire I2C Bus

1. Connect all SDA pins together (GPIO1)
2. Connect all SCL pins together (GPIO2)
3. Add 4.7kΩ pull-up resistors from SDA and SCL to 3.3V
   - Most modules have built-in pull-ups, but adding external ones improves reliability

### Step 3: Connect Power

1. Connect all VCC pins to 3V3
2. Connect all GND pins to GND
3. Double-check polarity before powering on!

### Step 4: Add Status LED

1. Connect LED anode (+) through a 330Ω resistor to GPIO5
2. Connect LED cathode (-) to GND

### Step 5: Flash Firmware

1. Connect ESP32-S3-Zero via USB
2. Open the firmware project in PlatformIO
3. Build and upload:

```bash
cd wearable-prototype/firmware
pio run --target upload
```

4. Open serial monitor to verify:

```bash
pio device monitor
```

### Step 6: Battery Power (Optional)

1. Solder TP4056 module to battery
2. Connect TP4056 output to ESP32-S3-Zero power input
3. Test charging via USB
4. Verify battery protection works (don't over-discharge!)

## Wiring Diagram

```
                    ┌─────────────────┐
                    │  ESP32-S3-Zero  │
                    │                 │
    ┌───────────────┤ GPIO1 (SDA)     │
    │   ┌───────────┤ GPIO2 (SCL)     │
    │   │           │ GPIO5           ├──── LED + R ──── GND
    │   │           │ 3V3             ├──┬──────────────────┐
    │   │           │ GND             ├──┼──────────────┬───┤
    │   │           └─────────────────┘  │              │   │
    │   │                                │              │   │
    │   │   ┌───────────────┐            │              │   │
    │   │   │   MPU6050     │            │              │   │
    │   ├───┤ SCL           │            │              │   │
    ├───────┤ SDA           │            │              │   │
    │   │   │ VCC           ├────────────┘              │   │
    │   │   │ GND           ├───────────────────────────┼───┤
    │   │   └───────────────┘                           │   │
    │   │                                               │   │
    │   │   ┌───────────────┐                           │   │
    │   │   │   MAX30102    │                           │   │
    │   └───┤ SCL           │                           │   │
    └───────┤ SDA           │                           │   │
            │ VCC           ├───────────────────────────┘   │
            │ GND           ├───────────────────────────────┘
            └───────────────┘
```

## Troubleshooting

### I2C Device Not Found

- Check wiring connections
- Verify power supply is stable at 3.3V
- Try lowering I2C clock speed to 100kHz
- Check for shorts between SDA and SCL

### PPG Readings Invalid

- Ensure sensor is flush against skin
- Check that LEDs are facing the skin
- Clean sensor surface
- Try different finger or wrist position

### IMU Drift

- Run calibration routine with device stationary
- Allow sensor to warm up for 1-2 minutes
- Keep device away from magnetic interference

### BLE Connection Issues

- Ensure device is advertising
- Check that phone has Bluetooth enabled
- Try restarting both devices
- Update phone's BLE stack if needed

## Next Steps

After successful assembly:

1. Run sensor calibration routines
2. Test BLE data streaming to phone
3. Verify battery life meets requirements
4. Design and print enclosure

