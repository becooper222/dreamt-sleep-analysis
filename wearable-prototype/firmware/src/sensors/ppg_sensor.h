/**
 * PPG Sensor Driver (MAX30102)
 * ============================
 * 
 * Driver for the MAX30102 pulse oximeter and heart rate sensor.
 */

#ifndef PPG_SENSOR_H
#define PPG_SENSOR_H

#include <Arduino.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include "../include/config.h"

/**
 * PPG data structure
 */
struct PPGData {
    uint32_t timestamp;     // Timestamp in milliseconds
    uint32_t red;           // Red LED reading
    uint32_t ir;            // IR LED reading
    uint32_t green;         // Green LED reading (if available)
};

/**
 * PPG Sensor class
 */
class PPGSensor {
public:
    PPGSensor() : _initialized(false), _lastHeartRate(0), _lastSpO2(0) {}
    
    /**
     * Initialize the sensor
     */
    bool begin() {
        // Initialize sensor
        if (!_sensor.begin(Wire, I2C_SPEED_FAST)) {
            Serial.println("[PPG] MAX30102 not found!");
            return false;
        }
        
        // Configure sensor
        byte ledBrightness = PPG_LED_BRIGHTNESS;  // 0-255
        byte sampleAverage = PPG_SAMPLE_AVERAGE;  // 1, 2, 4, 8, 16, 32
        byte ledMode = PPG_LED_MODE;              // 1=Red only, 2=Red+IR, 3=Red+IR+Green
        int sampleRate = PPG_SAMPLE_RATE_HZ;      // 50, 100, 200, 400, 800, 1000, 1600, 3200
        int pulseWidth = 411;                      // 69, 118, 215, 411
        int adcRange = PPG_ADC_RANGE;             // 2048, 4096, 8192, 16384
        
        _sensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange);
        
        // Enable temperature readings
        _sensor.enableDIETEMPRDY();
        
        // Initialize heart rate detection buffers
        for (int i = 0; i < RATE_SIZE; i++) {
            _rates[i] = 0;
        }
        _rateSpot = 0;
        _beatAvg = 0;
        
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
    PPGData read() {
        PPGData data;
        data.timestamp = millis();
        
        if (!_initialized) {
            return data;
        }
        
        // Read available samples
        _sensor.check();
        
        while (_sensor.available()) {
            data.red = _sensor.getRed();
            data.ir = _sensor.getIR();
            data.green = _sensor.getGreen();
            
            // Process for heart rate detection
            _processHeartRate(data.ir);
            
            _sensor.nextSample();
        }
        
        return data;
    }
    
    /**
     * Calculate heart rate from buffer of samples
     */
    float calculateHeartRate(PPGData* buffer, uint16_t count) {
        if (count < 10) return 0;
        
        // Simple peak detection for heart rate
        int peaks = 0;
        uint32_t threshold = 0;
        
        // Calculate threshold as 80% of max IR value
        uint32_t maxIR = 0;
        for (uint16_t i = 0; i < count; i++) {
            if (buffer[i].ir > maxIR) maxIR = buffer[i].ir;
        }
        threshold = maxIR * 0.8;
        
        // Count peaks
        bool aboveThreshold = false;
        for (uint16_t i = 0; i < count; i++) {
            if (buffer[i].ir > threshold && !aboveThreshold) {
                peaks++;
                aboveThreshold = true;
            } else if (buffer[i].ir < threshold * 0.9) {
                aboveThreshold = false;
            }
        }
        
        // Calculate heart rate
        float duration = (buffer[count-1].timestamp - buffer[0].timestamp) / 1000.0f;
        if (duration > 0 && peaks > 1) {
            _lastHeartRate = (peaks - 1) * 60.0f / duration;
            return _lastHeartRate;
        }
        
        return _lastHeartRate;
    }
    
    /**
     * Get the last calculated heart rate
     */
    float getLastHeartRate() {
        return _beatAvg > 0 ? _beatAvg : _lastHeartRate;
    }
    
    /**
     * Get SpO2 level (requires proper calibration)
     */
    float getSpO2() {
        return _lastSpO2;
    }
    
    /**
     * Get sensor temperature
     */
    float getTemperature() {
        if (!_initialized) return 0;
        return _sensor.readTemperature();
    }
    
    /**
     * Check if finger is detected
     */
    bool isFingerDetected() {
        if (!_initialized) return false;
        
        // Check if IR reading is above minimum threshold
        return _sensor.getIR() > 50000;
    }
    
    /**
     * Put sensor to sleep
     */
    void sleep() {
        if (_initialized) {
            _sensor.shutDown();
        }
    }
    
    /**
     * Wake sensor from sleep
     */
    void wake() {
        if (_initialized) {
            _sensor.wakeUp();
        }
    }

private:
    MAX30105 _sensor;
    bool _initialized;
    float _lastHeartRate;
    float _lastSpO2;
    
    // Heart rate detection
    static const int RATE_SIZE = 4;
    byte _rates[RATE_SIZE];
    byte _rateSpot;
    long _lastBeat;
    float _beatAvg;
    
    /**
     * Process IR reading for heart rate detection
     */
    void _processHeartRate(uint32_t irValue) {
        if (checkForBeat(irValue)) {
            long delta = millis() - _lastBeat;
            _lastBeat = millis();
            
            float beatsPerMinute = 60 / (delta / 1000.0);
            
            if (beatsPerMinute < 255 && beatsPerMinute > 20) {
                _rates[_rateSpot++] = (byte)beatsPerMinute;
                _rateSpot %= RATE_SIZE;
                
                // Calculate average
                _beatAvg = 0;
                for (byte i = 0; i < RATE_SIZE; i++) {
                    _beatAvg += _rates[i];
                }
                _beatAvg /= RATE_SIZE;
            }
        }
    }
};

#endif // PPG_SENSOR_H

