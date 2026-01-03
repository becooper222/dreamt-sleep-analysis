/**
 * BLE Communication Handler
 * =========================
 * 
 * NimBLE-based Bluetooth Low Energy handler for data transmission.
 */

#ifndef BLE_HANDLER_H
#define BLE_HANDLER_H

#include <Arduino.h>
#include <NimBLEDevice.h>
#include "../include/config.h"
#include "../sensors/imu_sensor.h"
#include "../sensors/ppg_sensor.h"

/**
 * BLE Handler class
 */
class BLEHandler {
public:
    BLEHandler() : _server(nullptr), _connected(false), _deviceName("") {}
    
    /**
     * Initialize BLE
     */
    bool begin(const char* deviceName) {
        _deviceName = deviceName;
        
        // Initialize NimBLE
        NimBLEDevice::init(_deviceName);
        NimBLEDevice::setPower(BLE_TX_POWER);
        
        // Create server
        _server = NimBLEDevice::createServer();
        _server->setCallbacks(new ServerCallbacks(this));
        
        // Create custom service for sensor data
        NimBLEService* sensorService = _server->createService(SERVICE_UUID);
        
        // IMU data characteristic (notify)
        _imuChar = sensorService->createCharacteristic(
            IMU_CHAR_UUID,
            NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
        );
        _imuChar->setValue("IMU");
        
        // PPG data characteristic (notify)
        _ppgChar = sensorService->createCharacteristic(
            PPG_CHAR_UUID,
            NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
        );
        _ppgChar->setValue("PPG");
        
        // Control characteristic (read/write)
        _controlChar = sensorService->createCharacteristic(
            CONTROL_CHAR_UUID,
            NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::WRITE
        );
        _controlChar->setValue("0");
        _controlChar->setCallbacks(new ControlCallbacks(this));
        
        // Status characteristic (read/notify)
        _statusChar = sensorService->createCharacteristic(
            STATUS_CHAR_UUID,
            NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
        );
        _statusChar->setValue("Ready");
        
        // Start service
        sensorService->start();
        
        // Create Heart Rate service (standard BLE service)
        NimBLEService* hrService = _server->createService(NimBLEUUID((uint16_t)HR_SERVICE_UUID));
        
        _hrChar = hrService->createCharacteristic(
            NimBLEUUID((uint16_t)HR_CHAR_UUID),
            NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
        );
        
        // Heart rate measurement format: 1 byte for HR value
        uint8_t hrValue[2] = {0x00, 60};  // Flag byte + HR
        _hrChar->setValue(hrValue, 2);
        
        hrService->start();
        
        return true;
    }
    
    /**
     * Start advertising
     */
    void startAdvertising() {
        NimBLEAdvertising* advertising = NimBLEDevice::getAdvertising();
        advertising->addServiceUUID(SERVICE_UUID);
        advertising->addServiceUUID(NimBLEUUID((uint16_t)HR_SERVICE_UUID));
        advertising->setScanResponse(true);
        advertising->setMinPreferred(0x06);  // iPhone connection fix
        advertising->setMaxPreferred(0x12);
        advertising->start();
    }
    
    /**
     * Stop advertising
     */
    void stopAdvertising() {
        NimBLEDevice::getAdvertising()->stop();
    }
    
    /**
     * Check if connected
     */
    bool isConnected() {
        return _connected;
    }
    
    /**
     * Send IMU data packet
     */
    void sendIMUData(IMUData* data, uint16_t count) {
        if (!_connected || count == 0) return;
        
        // Pack data into bytes for transmission
        // Format: [timestamp(4), ax(2), ay(2), az(2), gx(2), gy(2), gz(2)] = 16 bytes per sample
        // Send compressed: just the latest few samples
        
        const int SAMPLES_TO_SEND = min((int)count, 4);  // Send last 4 samples
        uint8_t packet[64];
        int offset = 0;
        
        for (int i = count - SAMPLES_TO_SEND; i < count; i++) {
            // Timestamp (truncated to 2 bytes)
            packet[offset++] = (data[i].timestamp >> 8) & 0xFF;
            packet[offset++] = data[i].timestamp & 0xFF;
            
            // Accelerometer (scaled to int16)
            int16_t ax = (int16_t)(data[i].accelX * 1000);
            int16_t ay = (int16_t)(data[i].accelY * 1000);
            int16_t az = (int16_t)(data[i].accelZ * 1000);
            
            packet[offset++] = (ax >> 8) & 0xFF;
            packet[offset++] = ax & 0xFF;
            packet[offset++] = (ay >> 8) & 0xFF;
            packet[offset++] = ay & 0xFF;
            packet[offset++] = (az >> 8) & 0xFF;
            packet[offset++] = az & 0xFF;
            
            // Gyroscope (scaled to int16)
            int16_t gx = (int16_t)(data[i].gyroX * 10);
            int16_t gy = (int16_t)(data[i].gyroY * 10);
            int16_t gz = (int16_t)(data[i].gyroZ * 10);
            
            packet[offset++] = (gx >> 8) & 0xFF;
            packet[offset++] = gx & 0xFF;
            packet[offset++] = (gy >> 8) & 0xFF;
            packet[offset++] = gy & 0xFF;
            packet[offset++] = (gz >> 8) & 0xFF;
            packet[offset++] = gz & 0xFF;
        }
        
        _imuChar->setValue(packet, offset);
        _imuChar->notify();
    }
    
    /**
     * Send PPG data packet
     */
    void sendPPGData(PPGData* data, uint16_t count) {
        if (!_connected || count == 0) return;
        
        // Send last few samples
        const int SAMPLES_TO_SEND = min((int)count, 8);
        uint8_t packet[80];
        int offset = 0;
        
        for (int i = count - SAMPLES_TO_SEND; i < count; i++) {
            // Timestamp
            packet[offset++] = (data[i].timestamp >> 8) & 0xFF;
            packet[offset++] = data[i].timestamp & 0xFF;
            
            // Red LED (3 bytes - 24 bit value)
            packet[offset++] = (data[i].red >> 16) & 0xFF;
            packet[offset++] = (data[i].red >> 8) & 0xFF;
            packet[offset++] = data[i].red & 0xFF;
            
            // IR LED
            packet[offset++] = (data[i].ir >> 16) & 0xFF;
            packet[offset++] = (data[i].ir >> 8) & 0xFF;
            packet[offset++] = data[i].ir & 0xFF;
        }
        
        _ppgChar->setValue(packet, offset);
        _ppgChar->notify();
    }
    
    /**
     * Send heart rate measurement
     */
    void sendHeartRate(uint8_t heartRate) {
        if (!_connected) return;
        
        // Heart Rate Measurement characteristic format
        // Byte 0: Flags (0x00 = HR is uint8, contact not supported)
        // Byte 1: Heart Rate Value
        uint8_t hrValue[2] = {0x00, heartRate};
        _hrChar->setValue(hrValue, 2);
        _hrChar->notify();
    }
    
    /**
     * Update status message
     */
    void setStatus(const char* status) {
        if (_statusChar) {
            _statusChar->setValue(status);
            if (_connected) {
                _statusChar->notify();
            }
        }
    }
    
    /**
     * Handle control commands
     */
    void handleCommand(const std::string& command) {
        Serial.printf("[BLE] Received command: %s\n", command.c_str());
        
        if (command == "START") {
            // Start data collection
            setStatus("Streaming");
        } else if (command == "STOP") {
            // Stop data collection
            setStatus("Stopped");
        } else if (command == "CALIBRATE") {
            // Trigger calibration
            setStatus("Calibrating");
        }
    }

private:
    NimBLEServer* _server;
    NimBLECharacteristic* _imuChar;
    NimBLECharacteristic* _ppgChar;
    NimBLECharacteristic* _controlChar;
    NimBLECharacteristic* _statusChar;
    NimBLECharacteristic* _hrChar;
    bool _connected;
    const char* _deviceName;
    
    /**
     * Server connection callbacks
     */
    class ServerCallbacks : public NimBLEServerCallbacks {
    public:
        ServerCallbacks(BLEHandler* handler) : _handler(handler) {}
        
        void onConnect(NimBLEServer* server) override {
            _handler->_connected = true;
            Serial.println("[BLE] Client connected");
            
            // Optimize connection parameters for sensor data
            // server->updateConnParams(address, BLE_MIN_INTERVAL, BLE_MAX_INTERVAL, BLE_LATENCY, BLE_TIMEOUT);
        }
        
        void onDisconnect(NimBLEServer* server) override {
            _handler->_connected = false;
            Serial.println("[BLE] Client disconnected");
            
            // Restart advertising
            _handler->startAdvertising();
        }
        
    private:
        BLEHandler* _handler;
    };
    
    /**
     * Control characteristic callbacks
     */
    class ControlCallbacks : public NimBLECharacteristicCallbacks {
    public:
        ControlCallbacks(BLEHandler* handler) : _handler(handler) {}
        
        void onWrite(NimBLECharacteristic* characteristic) override {
            std::string value = characteristic->getValue();
            _handler->handleCommand(value);
        }
        
    private:
        BLEHandler* _handler;
    };
};

#endif // BLE_HANDLER_H

