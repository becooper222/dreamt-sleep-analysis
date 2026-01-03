# Sensor Calibration Guide

Instructions for calibrating the sleep monitor sensors for optimal accuracy.

## IMU Calibration (MPU6050)

The MPU6050 requires calibration to compensate for manufacturing variations and offset errors.

### When to Calibrate

- After first assembly
- If device has been dropped or physically stressed
- If readings seem consistently offset
- When changing environmental conditions significantly

### Accelerometer Calibration

#### Step 1: Static Offset Calibration

1. Place the device on a perfectly flat, stable surface
2. Ensure the device is completely stationary
3. Run the calibration routine:

```cpp
void calibrateAccelerometer() {
    Serial.println("Calibrating accelerometer...");
    Serial.println("Keep device FLAT and STILL!");
    delay(2000);
    
    const int SAMPLES = 1000;
    float axSum = 0, aySum = 0, azSum = 0;
    
    for (int i = 0; i < SAMPLES; i++) {
        IMUData data = imuSensor.read();
        axSum += data.accelX;
        aySum += data.accelY;
        azSum += data.accelZ;
        delay(5);
    }
    
    // Calculate offsets
    float axOffset = axSum / SAMPLES;
    float ayOffset = aySum / SAMPLES;
    float azOffset = (azSum / SAMPLES) - 1.0;  // Should be 1g
    
    Serial.printf("Offsets: ax=%.4f, ay=%.4f, az=%.4f\n", 
                  axOffset, ayOffset, azOffset);
    
    // Store these values in config or EEPROM
}
```

#### Step 2: Six-Position Calibration (Advanced)

For higher accuracy, calibrate in 6 positions:

1. Z+ up (normal flat position)
2. Z- up (upside down)
3. X+ up (on edge)
4. X- up (opposite edge)
5. Y+ up (on another edge)
6. Y- up (opposite edge)

Record mean values for each position and compute transformation matrix.

### Gyroscope Calibration

The gyroscope primarily needs zero-rate offset calibration.

```cpp
void calibrateGyroscope() {
    Serial.println("Calibrating gyroscope...");
    Serial.println("Keep device completely STILL!");
    delay(2000);
    
    const int SAMPLES = 1000;
    float gxSum = 0, gySum = 0, gzSum = 0;
    
    for (int i = 0; i < SAMPLES; i++) {
        IMUData data = imuSensor.read();
        gxSum += data.gyroX;
        gySum += data.gyroY;
        gzSum += data.gyroZ;
        delay(5);
    }
    
    // These should all be close to 0
    float gxOffset = gxSum / SAMPLES;
    float gyOffset = gySum / SAMPLES;
    float gzOffset = gzSum / SAMPLES;
    
    Serial.printf("Gyro offsets: gx=%.4f, gy=%.4f, gz=%.4f deg/s\n",
                  gxOffset, gyOffset, gzOffset);
}
```

### Storing Calibration Data

Store calibration values in ESP32 NVS (Non-Volatile Storage):

```cpp
#include <Preferences.h>

Preferences preferences;

void saveCalibration(float ax, float ay, float az, 
                     float gx, float gy, float gz) {
    preferences.begin("calibration", false);
    preferences.putFloat("ax_offset", ax);
    preferences.putFloat("ay_offset", ay);
    preferences.putFloat("az_offset", az);
    preferences.putFloat("gx_offset", gx);
    preferences.putFloat("gy_offset", gy);
    preferences.putFloat("gz_offset", gz);
    preferences.end();
}

void loadCalibration() {
    preferences.begin("calibration", true);
    ax_offset = preferences.getFloat("ax_offset", 0);
    ay_offset = preferences.getFloat("ay_offset", 0);
    az_offset = preferences.getFloat("az_offset", 0);
    gx_offset = preferences.getFloat("gx_offset", 0);
    gy_offset = preferences.getFloat("gy_offset", 0);
    gz_offset = preferences.getFloat("gz_offset", 0);
    preferences.end();
}
```

## PPG Sensor Calibration (MAX30102)

PPG calibration is more complex as it depends on individual physiology.

### LED Brightness Optimization

Adjust LED brightness based on signal quality:

```cpp
void optimizeLEDBrightness() {
    // Start with low brightness
    uint8_t brightness = 0x10;
    
    while (brightness < 0xFF) {
        // Set new brightness
        sensor.setPulseAmplitudeRed(brightness);
        sensor.setPulseAmplitudeIR(brightness);
        
        delay(500);  // Wait for readings to stabilize
        
        // Check signal amplitude
        uint32_t red = sensor.getRed();
        uint32_t ir = sensor.getIR();
        
        // Check if signal is in optimal range
        if (ir > 50000 && ir < 200000) {
            Serial.printf("Optimal brightness: 0x%02X\n", brightness);
            break;
        }
        
        brightness += 0x10;
    }
}
```

### Ambient Light Rejection

The MAX30102 has built-in ambient light cancellation, but additional filtering helps:

```cpp
// Moving average filter for noise reduction
#define MA_SIZE 4

uint32_t irBuffer[MA_SIZE];
int bufferIndex = 0;

uint32_t filterPPG(uint32_t newValue) {
    irBuffer[bufferIndex] = newValue;
    bufferIndex = (bufferIndex + 1) % MA_SIZE;
    
    uint32_t sum = 0;
    for (int i = 0; i < MA_SIZE; i++) {
        sum += irBuffer[i];
    }
    return sum / MA_SIZE;
}
```

### Heart Rate Validation

Validate heart rate readings are physiologically plausible:

```cpp
float validateHeartRate(float rawHR) {
    // Physiological bounds
    const float MIN_HR = 30.0;   // Bradycardia threshold
    const float MAX_HR = 220.0;  // Maximum possible HR
    
    if (rawHR < MIN_HR || rawHR > MAX_HR) {
        return -1.0;  // Invalid reading
    }
    
    // Additional validation: check for sudden jumps
    static float lastValidHR = 60.0;
    const float MAX_CHANGE = 30.0;  // Max bpm change per reading
    
    if (abs(rawHR - lastValidHR) > MAX_CHANGE) {
        // Likely artifact, use smoothed value
        return lastValidHR * 0.7 + rawHR * 0.3;
    }
    
    lastValidHR = rawHR;
    return rawHR;
}
```

## Quality Metrics

### Signal Quality Index (SQI)

Compute a signal quality metric for data validation:

```cpp
float computeSQI(uint32_t* buffer, int size) {
    // Calculate mean
    float mean = 0;
    for (int i = 0; i < size; i++) {
        mean += buffer[i];
    }
    mean /= size;
    
    // Calculate standard deviation
    float variance = 0;
    for (int i = 0; i < size; i++) {
        float diff = buffer[i] - mean;
        variance += diff * diff;
    }
    float std = sqrt(variance / size);
    
    // SQI based on coefficient of variation
    float cv = std / mean;
    
    // Good signal: CV between 0.01 and 0.1
    if (cv >= 0.01 && cv <= 0.1) {
        return 1.0;  // Excellent
    } else if (cv < 0.01) {
        return 0.5;  // Too flat (no pulse detected)
    } else if (cv <= 0.2) {
        return 0.7;  // Acceptable
    } else {
        return 0.3;  // Poor (motion artifact likely)
    }
}
```

## Troubleshooting Poor Calibration

### IMU Issues

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| Large offset | Poor positioning | Ensure flat, stable surface |
| Drift over time | Temperature change | Re-calibrate after warm-up |
| Noisy readings | Electrical interference | Check grounding, add filtering |

### PPG Issues

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| No pulse detected | Poor skin contact | Adjust strap tension |
| Erratic readings | Motion artifact | Reduce movement, add filtering |
| Very low amplitude | Low perfusion | Try different location, warm up skin |
| Saturated signal | LED too bright | Reduce LED power |

