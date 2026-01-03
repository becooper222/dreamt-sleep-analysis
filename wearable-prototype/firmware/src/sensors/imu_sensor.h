/**
 * IMU Sensor Driver (MPU6050)
 * ===========================
 * 
 * Driver for the MPU6050 6-axis accelerometer/gyroscope.
 */

#ifndef IMU_SENSOR_H
#define IMU_SENSOR_H

#include <Arduino.h>
#include <Wire.h>
#include <MPU6050.h>
#include "../include/config.h"

/**
 * IMU data structure
 */
struct IMUData {
    uint32_t timestamp;     // Timestamp in milliseconds
    float accelX;           // Acceleration X (g)
    float accelY;           // Acceleration Y (g)
    float accelZ;           // Acceleration Z (g)
    float gyroX;            // Gyroscope X (deg/s)
    float gyroY;            // Gyroscope Y (deg/s)
    float gyroZ;            // Gyroscope Z (deg/s)
    float temperature;      // Temperature (°C)
};

/**
 * IMU Sensor class
 */
class IMUSensor {
public:
    IMUSensor() : _initialized(false), _mpu() {}
    
    /**
     * Initialize the sensor
     */
    bool begin() {
        _mpu.initialize();
        
        // Check connection
        if (!_mpu.testConnection()) {
            Serial.println("[IMU] MPU6050 connection failed!");
            return false;
        }
        
        // Configure accelerometer range
        _mpu.setFullScaleAccelRange(IMU_ACCEL_RANGE);
        
        // Configure gyroscope range
        _mpu.setFullScaleGyroRange(IMU_GYRO_RANGE);
        
        // Set sample rate divider (if needed)
        // Default is 8kHz internal, divider = 8000/rate - 1
        // For 32Hz: divider = 249
        _mpu.setRate(250 - 1);  // ~32 Hz
        
        // Enable data ready interrupt (optional)
        _mpu.setIntDataReadyEnabled(true);
        
        _initialized = true;
        return true;
    }
    
    /**
     * Check if sensor is ready
     */
    bool isReady() {
        return _initialized;
    }
    
    /**
     * Read sensor data
     */
    IMUData read() {
        IMUData data;
        data.timestamp = millis();
        
        if (!_initialized) {
            return data;
        }
        
        int16_t ax, ay, az, gx, gy, gz;
        _mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        
        // Convert to physical units
        // Accelerometer: LSB/g depends on range
        // Range 0 (±2g): 16384 LSB/g
        // Range 1 (±4g): 8192 LSB/g
        // Range 2 (±8g): 4096 LSB/g
        // Range 3 (±16g): 2048 LSB/g
        float accelScale = 16384.0f / (1 << IMU_ACCEL_RANGE);
        data.accelX = ax / accelScale;
        data.accelY = ay / accelScale;
        data.accelZ = az / accelScale;
        
        // Gyroscope: LSB/(deg/s) depends on range
        // Range 0 (±250°/s): 131 LSB/(°/s)
        // Range 1 (±500°/s): 65.5 LSB/(°/s)
        // Range 2 (±1000°/s): 32.8 LSB/(°/s)
        // Range 3 (±2000°/s): 16.4 LSB/(°/s)
        float gyroScale = 131.0f / (1 << IMU_GYRO_RANGE);
        data.gyroX = gx / gyroScale;
        data.gyroY = gy / gyroScale;
        data.gyroZ = gz / gyroScale;
        
        // Temperature
        data.temperature = _mpu.getTemperature() / 340.0f + 36.53f;
        
        return data;
    }
    
    /**
     * Get acceleration magnitude
     */
    float getAccelMagnitude(const IMUData& data) {
        return sqrt(data.accelX * data.accelX + 
                   data.accelY * data.accelY + 
                   data.accelZ * data.accelZ);
    }
    
    /**
     * Put sensor to sleep
     */
    void sleep() {
        if (_initialized) {
            _mpu.setSleepEnabled(true);
        }
    }
    
    /**
     * Wake sensor from sleep
     */
    void wake() {
        if (_initialized) {
            _mpu.setSleepEnabled(false);
        }
    }
    
    /**
     * Calibrate sensor offsets
     */
    void calibrate(int samples = 100) {
        if (!_initialized) return;
        
        Serial.println("[IMU] Calibrating... keep device still!");
        delay(1000);
        
        int32_t axSum = 0, aySum = 0, azSum = 0;
        int32_t gxSum = 0, gySum = 0, gzSum = 0;
        
        for (int i = 0; i < samples; i++) {
            int16_t ax, ay, az, gx, gy, gz;
            _mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
            
            axSum += ax;
            aySum += ay;
            azSum += az - 16384;  // Subtract 1g from Z (assuming flat)
            gxSum += gx;
            gySum += gy;
            gzSum += gz;
            
            delay(10);
        }
        
        // Set offsets
        _mpu.setXAccelOffset(-axSum / samples / 8);
        _mpu.setYAccelOffset(-aySum / samples / 8);
        _mpu.setZAccelOffset(-azSum / samples / 8);
        _mpu.setXGyroOffset(-gxSum / samples / 4);
        _mpu.setYGyroOffset(-gySum / samples / 4);
        _mpu.setZGyroOffset(-gzSum / samples / 4);
        
        Serial.println("[IMU] Calibration complete!");
    }

private:
    bool _initialized;
    MPU6050 _mpu;
};

#endif // IMU_SENSOR_H

