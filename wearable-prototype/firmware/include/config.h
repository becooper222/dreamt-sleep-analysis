/**
 * Sleep Monitor Configuration
 * ===========================
 * 
 * Central configuration file for the wearable sleep monitor.
 */

#ifndef CONFIG_H
#define CONFIG_H

// =============================================================================
// Device Information
// =============================================================================

#define DEVICE_NAME         "SleepMonitor"
#define FIRMWARE_VERSION    "0.1.0"
#define HARDWARE_VERSION    "1.0"

// =============================================================================
// Pin Definitions (ESP32-S3-Zero)
// =============================================================================

// I2C Bus
#define I2C_SDA_PIN         1
#define I2C_SCL_PIN         2
#define I2C_FREQUENCY       400000  // 400kHz Fast Mode

// Sensor Interrupts
#define MPU6050_INT_PIN     3
#define MAX30102_INT_PIN    4

// Status LED
#define LED_STATUS_PIN      5

// Battery Monitoring (optional)
#define BATTERY_ADC_PIN     6
#define BATTERY_DIVIDER     2.0     // Voltage divider ratio

// =============================================================================
// Sensor Configuration
// =============================================================================

// IMU (MPU6050) Settings
#define IMU_SAMPLE_RATE_HZ      32      // Samples per second
#define IMU_ACCEL_RANGE         2       // ±2g (0=2g, 1=4g, 2=8g, 3=16g)
#define IMU_GYRO_RANGE          250     // ±250°/s (0=250, 1=500, 2=1000, 3=2000)
#define IMU_BUFFER_SIZE         64      // Samples to buffer before transmit

// PPG (MAX30102) Settings
#define PPG_SAMPLE_RATE_HZ      100     // Samples per second
#define PPG_LED_BRIGHTNESS      0x1F    // LED current (0x00-0xFF)
#define PPG_SAMPLE_AVERAGE      4       // Averaging (1, 2, 4, 8, 16, 32)
#define PPG_LED_MODE            3       // 1=Red only, 2=Red+IR, 3=Red+IR+Green
#define PPG_ADC_RANGE           16384   // ADC range (2048, 4096, 8192, 16384)
#define PPG_BUFFER_SIZE         100     // Samples to buffer

// =============================================================================
// BLE Configuration
// =============================================================================

#define BLE_DEVICE_NAME         "SleepMon"
#define BLE_TX_POWER            ESP_PWR_LVL_P3  // +3dBm

// Custom Service UUIDs
#define SERVICE_UUID            "12345678-1234-1234-1234-123456789abc"
#define IMU_CHAR_UUID           "12345678-1234-1234-1234-123456789001"
#define PPG_CHAR_UUID           "12345678-1234-1234-1234-123456789002"
#define CONTROL_CHAR_UUID       "12345678-1234-1234-1234-123456789003"
#define STATUS_CHAR_UUID        "12345678-1234-1234-1234-123456789004"

// Standard Heart Rate Service
#define HR_SERVICE_UUID         0x180D
#define HR_CHAR_UUID            0x2A37

// Connection parameters
#define BLE_MIN_INTERVAL        16      // 20ms (in 1.25ms units)
#define BLE_MAX_INTERVAL        32      // 40ms
#define BLE_LATENCY             0
#define BLE_TIMEOUT             400     // 4 seconds

// =============================================================================
// WiFi Configuration (for data upload)
// =============================================================================

#define WIFI_ENABLED            false
#define WIFI_SSID               "your_network"
#define WIFI_PASSWORD           "your_password"

// =============================================================================
// Power Management
// =============================================================================

#define SLEEP_TIMEOUT_MS        60000   // Enter deep sleep after 60s inactivity
#define LOW_BATTERY_THRESHOLD   3.3     // Voltage threshold for low battery warning
#define CRITICAL_BATTERY        3.0     // Voltage for shutdown

// =============================================================================
// Data Processing / On-Device Inference
// =============================================================================

#define EPOCH_DURATION_SEC      30      // Sleep staging epoch duration (must match training)
#define FEATURE_WINDOW_SEC      30      // Feature extraction window

// Enable on-device sleep stage classification
// Set to true after deploying the trained model:
//   1. Train model: python scripts/train_tflite_model.py --data_dir ../data/dreamt
//   2. Convert: xxd -i sleep_model.tflite > firmware/include/model_data.h
//   3. Copy scaler_params.h to firmware/include/
//   4. Set ENABLE_EDGE_INFERENCE to true
#define ENABLE_EDGE_INFERENCE   true

// Model file (if loading from SPIFFS instead of embedding)
#define MODEL_FILENAME          "/model.tflite"

// Sleep stage classes (4-class clinical-lite)
// 0: Wake, 1: Light (N1+N2), 2: Deep (N3), 3: REM
#define N_SLEEP_CLASSES         4

// =============================================================================
// Debug Options
// =============================================================================

#define DEBUG_SERIAL            true
#define DEBUG_BAUD_RATE         115200
#define DEBUG_PRINT_INTERVAL_MS 1000    // Print debug info every 1s

// Sensor data logging
#define LOG_TO_SERIAL           true
#define LOG_RAW_IMU             false
#define LOG_RAW_PPG             false
#define LOG_HEART_RATE          true

#endif // CONFIG_H

