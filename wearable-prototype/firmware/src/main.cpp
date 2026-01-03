/**
 * Sleep Monitor Wearable - Main Application
 * ==========================================
 * 
 * ESP32-S3 based wearable device for sleep monitoring.
 * Captures IMU and PPG data, runs on-device sleep stage classification,
 * and transmits results via BLE.
 * 
 * Hardware:
 *   - ESP32-S3-Zero (Waveshare)
 *   - MPU6050 (IMU)
 *   - MAX30102 (PPG)
 * 
 * Sleep Stage Classes (4-class clinical-lite):
 *   0: Wake
 *   1: Light Sleep (N1 + N2)
 *   2: Deep Sleep (N3)
 *   3: REM
 */

#include <Arduino.h>
#include <Wire.h>
#include "config.h"
#include "sensors/imu_sensor.h"
#include "sensors/ppg_sensor.h"
#include "ble/ble_handler.h"

// On-device inference components
#if ENABLE_EDGE_INFERENCE
#include "processing/feature_extractor.h"
#include "processing/sleep_classifier.h"
#endif

// =============================================================================
// Global Objects
// =============================================================================

IMUSensor imuSensor;
PPGSensor ppgSensor;
BLEHandler bleHandler;

#if ENABLE_EDGE_INFERENCE
FeatureExtractor featureExtractor;
SleepClassifier sleepClassifier;
EpochFeatures currentFeatures;
SleepStageResult lastSleepStage;
#endif

// Timing variables
unsigned long lastIMURead = 0;
unsigned long lastPPGRead = 0;
unsigned long lastDebugPrint = 0;
unsigned long lastBLETransmit = 0;
unsigned long lastSleepStageUpdate = 0;

// Data buffers
IMUData imuBuffer[IMU_BUFFER_SIZE];
PPGData ppgBuffer[PPG_BUFFER_SIZE];
uint16_t imuBufferIndex = 0;
uint16_t ppgBufferIndex = 0;

// Status
bool sensorsInitialized = false;
bool bleConnected = false;
bool inferenceEnabled = false;

// =============================================================================
// Setup
// =============================================================================

void setup() {
    // Initialize serial for debugging
    #if DEBUG_SERIAL
    Serial.begin(DEBUG_BAUD_RATE);
    delay(1000);  // Wait for serial monitor
    Serial.println("\n========================================");
    Serial.println("   Sleep Monitor Wearable v" FIRMWARE_VERSION);
    Serial.println("========================================\n");
    #endif

    // Initialize status LED
    pinMode(LED_STATUS_PIN, OUTPUT);
    digitalWrite(LED_STATUS_PIN, HIGH);  // LED on during init

    // Initialize I2C
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(I2C_FREQUENCY);
    Serial.println("[I2C] Initialized");

    // Initialize IMU sensor
    Serial.print("[IMU] Initializing MPU6050... ");
    if (imuSensor.begin()) {
        Serial.println("OK");
    } else {
        Serial.println("FAILED!");
    }

    // Initialize PPG sensor
    Serial.print("[PPG] Initializing MAX30102... ");
    if (ppgSensor.begin()) {
        Serial.println("OK");
    } else {
        Serial.println("FAILED!");
    }

    // Check if sensors are ready
    sensorsInitialized = imuSensor.isReady() && ppgSensor.isReady();
    
    if (sensorsInitialized) {
        Serial.println("[SENSORS] All sensors initialized successfully!");
    } else {
        Serial.println("[SENSORS] WARNING: Some sensors failed to initialize");
    }

    // Initialize BLE
    Serial.print("[BLE] Initializing... ");
    if (bleHandler.begin(BLE_DEVICE_NAME)) {
        Serial.println("OK");
        bleHandler.startAdvertising();
        Serial.println("[BLE] Advertising started");
    } else {
        Serial.println("FAILED!");
    }

    // Initialize on-device inference
    #if ENABLE_EDGE_INFERENCE
    Serial.println("\n[INFERENCE] Initializing on-device sleep classification...");
    
    Serial.print("[INFERENCE] Feature extractor... ");
    if (featureExtractor.begin()) {
        Serial.println("OK");
    } else {
        Serial.println("FAILED!");
    }
    
    Serial.print("[INFERENCE] TFLite classifier... ");
    if (sleepClassifier.begin()) {
        Serial.println("OK");
        inferenceEnabled = true;
        Serial.printf("[INFERENCE] Model arena: %d bytes\n", sleepClassifier.getArenaUsed());
    } else {
        Serial.println("FAILED - Running in streaming-only mode");
        inferenceEnabled = false;
    }
    
    // Initialize last sleep stage
    lastSleepStage.valid = false;
    lastSleepStage.predictedClass = 0;
    lastSleepStage.className = "Unknown";
    #else
    Serial.println("\n[INFERENCE] Edge inference DISABLED (streaming mode only)");
    #endif

    // Initialization complete
    digitalWrite(LED_STATUS_PIN, LOW);  // LED off
    Serial.println("\n[SYSTEM] Setup complete. Starting main loop...\n");
}

// =============================================================================
// Main Loop
// =============================================================================

void loop() {
    unsigned long currentTime = millis();
    
    // -------------------------------------------------------------------------
    // Read IMU data at configured rate
    // -------------------------------------------------------------------------
    if (currentTime - lastIMURead >= (1000 / IMU_SAMPLE_RATE_HZ)) {
        lastIMURead = currentTime;
        
        if (imuSensor.isReady()) {
            IMUData data = imuSensor.read();
            
            // Store in buffer for BLE streaming
            if (imuBufferIndex < IMU_BUFFER_SIZE) {
                imuBuffer[imuBufferIndex++] = data;
            }
            
            // Add to feature extractor for inference
            #if ENABLE_EDGE_INFERENCE
            if (inferenceEnabled) {
                featureExtractor.addIMUSample(data);
            }
            #endif
            
            #if LOG_RAW_IMU && DEBUG_SERIAL
            Serial.printf("[IMU] ax=%+.2f ay=%+.2f az=%+.2f gx=%+.2f gy=%+.2f gz=%+.2f\n",
                         data.accelX, data.accelY, data.accelZ,
                         data.gyroX, data.gyroY, data.gyroZ);
            #endif
        }
    }

    // -------------------------------------------------------------------------
    // Read PPG data at configured rate
    // -------------------------------------------------------------------------
    if (currentTime - lastPPGRead >= (1000 / PPG_SAMPLE_RATE_HZ)) {
        lastPPGRead = currentTime;
        
        if (ppgSensor.isReady()) {
            PPGData data = ppgSensor.read();
            float heartRate = ppgSensor.getLastHeartRate();
            
            // Store in buffer for BLE streaming
            if (ppgBufferIndex < PPG_BUFFER_SIZE) {
                ppgBuffer[ppgBufferIndex++] = data;
            }
            
            // Add to feature extractor for inference
            #if ENABLE_EDGE_INFERENCE
            if (inferenceEnabled) {
                featureExtractor.addPPGSample(data, heartRate);
            }
            #endif
            
            #if LOG_RAW_PPG && DEBUG_SERIAL
            Serial.printf("[PPG] red=%lu ir=%lu\n", data.red, data.ir);
            #endif
        }
    }

    // -------------------------------------------------------------------------
    // Run sleep stage inference when epoch is ready (every 30 seconds)
    // -------------------------------------------------------------------------
    #if ENABLE_EDGE_INFERENCE
    if (inferenceEnabled && featureExtractor.isEpochReady()) {
        // Extract features
        if (featureExtractor.extractFeatures(currentFeatures)) {
            // Run inference
            if (sleepClassifier.classify(currentFeatures, lastSleepStage)) {
                lastSleepStageUpdate = currentTime;
                
                Serial.printf("[SLEEP] Stage: %s (confidence: %.1f%%, inference: %.2fms)\n",
                             lastSleepStage.className,
                             lastSleepStage.confidence * 100.0f,
                             lastSleepStage.inferenceTimeMs);
                Serial.printf("[SLEEP] Probabilities: W=%.2f L=%.2f D=%.2f R=%.2f\n",
                             lastSleepStage.probabilities[0],
                             lastSleepStage.probabilities[1],
                             lastSleepStage.probabilities[2],
                             lastSleepStage.probabilities[3]);
                
                // Send sleep stage via BLE
                if (bleConnected) {
                    bleHandler.sendSleepStage(lastSleepStage.predictedClass, 
                                             lastSleepStage.confidence);
                }
            }
        }
    }
    #endif

    // -------------------------------------------------------------------------
    // Transmit data via BLE when buffers are full
    // -------------------------------------------------------------------------
    bleConnected = bleHandler.isConnected();
    
    if (bleConnected) {
        // Transmit IMU buffer
        if (imuBufferIndex >= IMU_BUFFER_SIZE) {
            bleHandler.sendIMUData(imuBuffer, imuBufferIndex);
            imuBufferIndex = 0;
        }
        
        // Transmit PPG buffer
        if (ppgBufferIndex >= PPG_BUFFER_SIZE) {
            // Calculate heart rate from buffer
            float heartRate = ppgSensor.calculateHeartRate(ppgBuffer, ppgBufferIndex);
            bleHandler.sendHeartRate((uint8_t)heartRate);
            bleHandler.sendPPGData(ppgBuffer, ppgBufferIndex);
            ppgBufferIndex = 0;
        }
    }

    // -------------------------------------------------------------------------
    // Status LED blink
    // -------------------------------------------------------------------------
    static unsigned long lastBlink = 0;
    static bool ledState = false;
    
    unsigned long blinkInterval = bleConnected ? 1000 : 2000;  // Fast when connected
    
    if (currentTime - lastBlink >= blinkInterval) {
        lastBlink = currentTime;
        ledState = !ledState;
        digitalWrite(LED_STATUS_PIN, ledState);
    }

    // -------------------------------------------------------------------------
    // Debug output
    // -------------------------------------------------------------------------
    #if DEBUG_SERIAL
    if (currentTime - lastDebugPrint >= DEBUG_PRINT_INTERVAL_MS) {
        lastDebugPrint = currentTime;
        
        float heartRate = ppgSensor.getLastHeartRate();
        float batteryVoltage = readBatteryVoltage();
        
        #if ENABLE_EDGE_INFERENCE
        float epochProgress = inferenceEnabled ? featureExtractor.getBufferProgress() : 0.0f;
        const char* sleepStage = lastSleepStage.valid ? lastSleepStage.className : "---";
        
        Serial.printf("[STATUS] HR=%.0f | Sleep=%s | Epoch=%.0f%% | BLE=%s | Batt=%.2fV\n",
                     heartRate,
                     sleepStage,
                     epochProgress,
                     bleConnected ? "connected" : "advertising",
                     batteryVoltage);
        #else
        Serial.printf("[STATUS] HR=%.0f bpm | IMU buf=%d | PPG buf=%d | BLE=%s | Batt=%.2fV\n",
                     heartRate,
                     imuBufferIndex,
                     ppgBufferIndex,
                     bleConnected ? "connected" : "advertising",
                     batteryVoltage);
        #endif
    }
    #endif

    // Small delay to prevent CPU hogging
    delay(1);
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Read battery voltage from ADC
 */
float readBatteryVoltage() {
    #ifdef BATTERY_ADC_PIN
    int adcValue = analogRead(BATTERY_ADC_PIN);
    float voltage = (adcValue / 4095.0) * 3.3 * BATTERY_DIVIDER;
    return voltage;
    #else
    return 0.0;
    #endif
}

/**
 * Enter deep sleep mode
 */
void enterDeepSleep(uint64_t sleepTimeUs) {
    Serial.println("[POWER] Entering deep sleep...");
    
    // Disable sensors
    imuSensor.sleep();
    ppgSensor.sleep();
    
    // Configure wake-up sources
    // esp_sleep_enable_ext0_wakeup(GPIO_NUM_X, 1);  // Wake on button press
    esp_sleep_enable_timer_wakeup(sleepTimeUs);
    
    // Enter deep sleep
    esp_deep_sleep_start();
}

