/**
 * Feature Extractor for Sleep Stage Classification
 * =================================================
 * 
 * Extracts statistical features from IMU and PPG signals for 4-class
 * sleep stage classification (Wake, Light, Deep, REM).
 * 
 * Features must match the Python training pipeline exactly.
 * See: model-training/scripts/train_tflite_model.py
 */

#ifndef FEATURE_EXTRACTOR_H
#define FEATURE_EXTRACTOR_H

#include <Arduino.h>
#include <math.h>
#include "../sensors/imu_sensor.h"
#include "../sensors/ppg_sensor.h"
#include "../config.h"

// ============================================================================
// Configuration
// ============================================================================

// Epoch configuration (must match training)
#define EPOCH_SAMPLES_IMU    (EPOCH_DURATION_SEC * IMU_SAMPLE_RATE_HZ)   // 30 * 32 = 960
#define EPOCH_SAMPLES_PPG    (EPOCH_DURATION_SEC * PPG_SAMPLE_RATE_HZ)   // 30 * 100 = 3000

// Feature counts
#define N_STAT_FEATURES     12   // mean, std, min, max, range, median, iqr, skew, kurtosis, energy, rms, zero_crossings
#define N_IMU_AXES          4    // X, Y, Z, Magnitude
#define N_IMU_EXTRA         2    // activity_count, movement_intensity
#define N_PPG_STAT          12   // Same stats for PPG
#define N_HR_FEATURES       5    // mean, std, min, max, range
#define N_HRV_FEATURES      5    // mean_ibi, sdnn, rmssd, pnn50, pnn20

// Total feature count
// IMU: 4 axes * 12 stats + 2 extra = 50
// PPG: 12 stats + 5 HR + 5 HRV = 22
// Total: 72 features
#define N_TOTAL_FEATURES    (N_IMU_AXES * N_STAT_FEATURES + N_IMU_EXTRA + N_PPG_STAT + N_HR_FEATURES + N_HRV_FEATURES)


// ============================================================================
// Feature Buffer Structure
// ============================================================================

/**
 * Container for extracted features from one epoch.
 */
struct EpochFeatures {
    float features[N_TOTAL_FEATURES];
    bool valid;
    uint32_t timestamp;
    
    // Feature indices for easier access
    static const int IDX_IMU_X_START = 0;
    static const int IDX_IMU_Y_START = N_STAT_FEATURES;
    static const int IDX_IMU_Z_START = N_STAT_FEATURES * 2;
    static const int IDX_IMU_MAG_START = N_STAT_FEATURES * 3;
    static const int IDX_IMU_EXTRA = N_STAT_FEATURES * 4;
    static const int IDX_PPG_START = N_STAT_FEATURES * 4 + N_IMU_EXTRA;
    static const int IDX_HR_START = IDX_PPG_START + N_PPG_STAT;
    static const int IDX_HRV_START = IDX_HR_START + N_HR_FEATURES;
};


// ============================================================================
// Statistical Functions
// ============================================================================

/**
 * Compute statistical features from a signal buffer.
 * 
 * @param data Input signal array
 * @param length Number of samples
 * @param output Output array for 12 features
 */
void computeStatFeatures(const float* data, int length, float* output) {
    if (length == 0) {
        for (int i = 0; i < N_STAT_FEATURES; i++) output[i] = 0.0f;
        return;
    }
    
    // ---- Basic statistics ----
    
    // Mean
    float sum = 0.0f;
    for (int i = 0; i < length; i++) {
        sum += data[i];
    }
    float mean = sum / length;
    output[0] = mean;
    
    // Variance and standard deviation
    float sumSq = 0.0f;
    for (int i = 0; i < length; i++) {
        float diff = data[i] - mean;
        sumSq += diff * diff;
    }
    float variance = sumSq / length;
    float std = sqrtf(variance);
    output[1] = std;
    
    // Min, Max, Range
    float minVal = data[0];
    float maxVal = data[0];
    for (int i = 1; i < length; i++) {
        if (data[i] < minVal) minVal = data[i];
        if (data[i] > maxVal) maxVal = data[i];
    }
    output[2] = minVal;
    output[3] = maxVal;
    output[4] = maxVal - minVal;  // Range
    
    // ---- Median and IQR (requires sorting) ----
    // Use a simple selection for Q1, median (Q2), Q3
    // For efficiency, we'll use a simplified approach
    
    // Create sorted copy (partial sort for quartiles)
    float* sorted = (float*)malloc(length * sizeof(float));
    memcpy(sorted, data, length * sizeof(float));
    
    // Simple insertion sort (acceptable for 960-3000 samples per epoch)
    for (int i = 1; i < length; i++) {
        float key = sorted[i];
        int j = i - 1;
        while (j >= 0 && sorted[j] > key) {
            sorted[j + 1] = sorted[j];
            j--;
        }
        sorted[j + 1] = key;
    }
    
    int q1Idx = length / 4;
    int q2Idx = length / 2;
    int q3Idx = (3 * length) / 4;
    
    output[5] = sorted[q2Idx];  // Median
    output[6] = sorted[q3Idx] - sorted[q1Idx];  // IQR
    
    free(sorted);
    
    // ---- Higher moments ----
    
    // Skewness and Kurtosis
    if (std > 0.0001f) {
        float sumCube = 0.0f;
        float sumQuad = 0.0f;
        for (int i = 0; i < length; i++) {
            float z = (data[i] - mean) / std;
            sumCube += z * z * z;
            sumQuad += z * z * z * z;
        }
        output[7] = sumCube / length;  // Skewness
        output[8] = (sumQuad / length) - 3.0f;  // Excess Kurtosis
    } else {
        output[7] = 0.0f;
        output[8] = 0.0f;
    }
    
    // ---- Energy features ----
    
    // Energy (sum of squares)
    float energy = 0.0f;
    for (int i = 0; i < length; i++) {
        energy += data[i] * data[i];
    }
    output[9] = energy;
    
    // RMS
    output[10] = sqrtf(energy / length);
    
    // ---- Zero crossings ----
    int zeroCrossings = 0;
    for (int i = 1; i < length; i++) {
        // Count crossings relative to mean
        bool prevAbove = (data[i-1] > mean);
        bool currAbove = (data[i] > mean);
        if (prevAbove != currAbove) {
            zeroCrossings++;
        }
    }
    output[11] = (float)zeroCrossings;
}


/**
 * Compute magnitude from 3-axis accelerometer data.
 */
void computeMagnitude(const float* x, const float* y, const float* z, 
                      float* mag, int length) {
    for (int i = 0; i < length; i++) {
        mag[i] = sqrtf(x[i]*x[i] + y[i]*y[i] + z[i]*z[i]);
    }
}


// ============================================================================
// Feature Extractor Class
// ============================================================================

class FeatureExtractor {
public:
    FeatureExtractor() : _epochReady(false) {}
    
    /**
     * Initialize the feature extractor.
     */
    bool begin() {
        _imuIndex = 0;
        _ppgIndex = 0;
        _epochReady = false;
        
        // Allocate buffers
        _accX = (float*)malloc(EPOCH_SAMPLES_IMU * sizeof(float));
        _accY = (float*)malloc(EPOCH_SAMPLES_IMU * sizeof(float));
        _accZ = (float*)malloc(EPOCH_SAMPLES_IMU * sizeof(float));
        _accMag = (float*)malloc(EPOCH_SAMPLES_IMU * sizeof(float));
        _ppgBuffer = (float*)malloc(EPOCH_SAMPLES_PPG * sizeof(float));
        _hrBuffer = (float*)malloc(EPOCH_SAMPLES_PPG * sizeof(float));
        _ibiBuffer = (float*)malloc(256 * sizeof(float));  // Max ~256 beats per 30s
        
        if (!_accX || !_accY || !_accZ || !_accMag || !_ppgBuffer || !_hrBuffer || !_ibiBuffer) {
            Serial.println("[FEAT] Memory allocation failed!");
            return false;
        }
        
        Serial.printf("[FEAT] Initialized: %d IMU samples, %d PPG samples per epoch\n",
                      EPOCH_SAMPLES_IMU, EPOCH_SAMPLES_PPG);
        Serial.printf("[FEAT] Feature vector size: %d\n", N_TOTAL_FEATURES);
        
        return true;
    }
    
    /**
     * Add IMU sample to buffer.
     */
    void addIMUSample(const IMUData& data) {
        if (_imuIndex < EPOCH_SAMPLES_IMU) {
            _accX[_imuIndex] = data.accelX;
            _accY[_imuIndex] = data.accelY;
            _accZ[_imuIndex] = data.accelZ;
            _imuIndex++;
        }
    }
    
    /**
     * Add PPG sample to buffer.
     */
    void addPPGSample(const PPGData& data, float heartRate) {
        if (_ppgIndex < EPOCH_SAMPLES_PPG) {
            // Use IR signal as BVP proxy
            _ppgBuffer[_ppgIndex] = (float)data.ir;
            _hrBuffer[_ppgIndex] = heartRate;
            _ppgIndex++;
        }
    }
    
    /**
     * Add detected IBI (inter-beat interval) for HRV computation.
     */
    void addIBI(float ibiMs) {
        if (_ibiCount < 256) {
            _ibiBuffer[_ibiCount++] = ibiMs;
        }
    }
    
    /**
     * Check if epoch buffer is full and ready for feature extraction.
     */
    bool isEpochReady() const {
        return (_imuIndex >= EPOCH_SAMPLES_IMU && _ppgIndex >= EPOCH_SAMPLES_PPG);
    }
    
    /**
     * Extract all features from current epoch buffers.
     * 
     * @param features Output structure for extracted features
     * @return true if extraction successful
     */
    bool extractFeatures(EpochFeatures& features) {
        if (!isEpochReady()) {
            features.valid = false;
            return false;
        }
        
        int idx = 0;
        
        // ====== IMU Features ======
        
        // Compute magnitude
        computeMagnitude(_accX, _accY, _accZ, _accMag, EPOCH_SAMPLES_IMU);
        
        // X-axis statistics
        computeStatFeatures(_accX, EPOCH_SAMPLES_IMU, &features.features[idx]);
        idx += N_STAT_FEATURES;
        
        // Y-axis statistics
        computeStatFeatures(_accY, EPOCH_SAMPLES_IMU, &features.features[idx]);
        idx += N_STAT_FEATURES;
        
        // Z-axis statistics
        computeStatFeatures(_accZ, EPOCH_SAMPLES_IMU, &features.features[idx]);
        idx += N_STAT_FEATURES;
        
        // Magnitude statistics
        computeStatFeatures(_accMag, EPOCH_SAMPLES_IMU, &features.features[idx]);
        idx += N_STAT_FEATURES;
        
        // IMU extra features
        features.features[idx++] = computeActivityCount();
        features.features[idx++] = computeMovementIntensity();
        
        // ====== PPG Features ======
        
        // PPG signal statistics
        computeStatFeatures(_ppgBuffer, EPOCH_SAMPLES_PPG, &features.features[idx]);
        idx += N_STAT_FEATURES;
        
        // HR features
        computeHRFeatures(&features.features[idx]);
        idx += N_HR_FEATURES;
        
        // HRV features
        computeHRVFeatures(&features.features[idx]);
        idx += N_HRV_FEATURES;
        
        // Mark as valid and add timestamp
        features.valid = true;
        features.timestamp = millis();
        
        // Reset buffers for next epoch
        resetBuffers();
        
        return true;
    }
    
    /**
     * Reset buffers for next epoch.
     */
    void resetBuffers() {
        _imuIndex = 0;
        _ppgIndex = 0;
        _ibiCount = 0;
    }
    
    /**
     * Get current buffer fill percentage.
     */
    float getBufferProgress() const {
        float imuPct = (float)_imuIndex / EPOCH_SAMPLES_IMU;
        float ppgPct = (float)_ppgIndex / EPOCH_SAMPLES_PPG;
        return min(imuPct, ppgPct) * 100.0f;
    }
    
private:
    // Buffers
    float* _accX;
    float* _accY;
    float* _accZ;
    float* _accMag;
    float* _ppgBuffer;
    float* _hrBuffer;
    float* _ibiBuffer;
    
    // Buffer indices
    int _imuIndex;
    int _ppgIndex;
    int _ibiCount;
    
    bool _epochReady;
    
    /**
     * Compute activity count (sum of absolute differences in magnitude).
     */
    float computeActivityCount() {
        float sum = 0.0f;
        for (int i = 1; i < _imuIndex; i++) {
            sum += fabsf(_accMag[i] - _accMag[i-1]);
        }
        return sum;
    }
    
    /**
     * Compute movement intensity (std of magnitude).
     */
    float computeMovementIntensity() {
        float sum = 0.0f;
        for (int i = 0; i < _imuIndex; i++) {
            sum += _accMag[i];
        }
        float mean = sum / _imuIndex;
        
        float sumSq = 0.0f;
        for (int i = 0; i < _imuIndex; i++) {
            float diff = _accMag[i] - mean;
            sumSq += diff * diff;
        }
        return sqrtf(sumSq / _imuIndex);
    }
    
    /**
     * Compute HR statistical features.
     */
    void computeHRFeatures(float* output) {
        // Filter out invalid HR values
        float validHR[EPOCH_SAMPLES_PPG];
        int validCount = 0;
        
        for (int i = 0; i < _ppgIndex; i++) {
            if (_hrBuffer[i] > 30.0f && _hrBuffer[i] < 200.0f) {
                validHR[validCount++] = _hrBuffer[i];
            }
        }
        
        if (validCount == 0) {
            for (int i = 0; i < N_HR_FEATURES; i++) output[i] = 0.0f;
            return;
        }
        
        // Mean
        float sum = 0.0f;
        for (int i = 0; i < validCount; i++) sum += validHR[i];
        float mean = sum / validCount;
        output[0] = mean;
        
        // Std
        float sumSq = 0.0f;
        for (int i = 0; i < validCount; i++) {
            float diff = validHR[i] - mean;
            sumSq += diff * diff;
        }
        output[1] = sqrtf(sumSq / validCount);
        
        // Min, Max, Range
        float minVal = validHR[0], maxVal = validHR[0];
        for (int i = 1; i < validCount; i++) {
            if (validHR[i] < minVal) minVal = validHR[i];
            if (validHR[i] > maxVal) maxVal = validHR[i];
        }
        output[2] = minVal;
        output[3] = maxVal;
        output[4] = maxVal - minVal;
    }
    
    /**
     * Compute HRV features from IBI buffer.
     */
    void computeHRVFeatures(float* output) {
        // Filter outliers (physiologically impossible values)
        float validIBI[256];
        int validCount = 0;
        
        for (int i = 0; i < _ibiCount; i++) {
            if (_ibiBuffer[i] > 300.0f && _ibiBuffer[i] < 2000.0f) {
                validIBI[validCount++] = _ibiBuffer[i];
            }
        }
        
        if (validCount < 2) {
            for (int i = 0; i < N_HRV_FEATURES; i++) output[i] = 0.0f;
            return;
        }
        
        // Mean IBI
        float sum = 0.0f;
        for (int i = 0; i < validCount; i++) sum += validIBI[i];
        float meanIBI = sum / validCount;
        output[0] = meanIBI;
        
        // SDNN (standard deviation of NN intervals)
        float sumSq = 0.0f;
        for (int i = 0; i < validCount; i++) {
            float diff = validIBI[i] - meanIBI;
            sumSq += diff * diff;
        }
        output[1] = sqrtf(sumSq / validCount);  // SDNN
        
        // RMSSD (root mean square of successive differences)
        float sumSqDiff = 0.0f;
        int pnn50Count = 0;
        int pnn20Count = 0;
        
        for (int i = 1; i < validCount; i++) {
            float diff = validIBI[i] - validIBI[i-1];
            sumSqDiff += diff * diff;
            
            if (fabsf(diff) > 50.0f) pnn50Count++;
            if (fabsf(diff) > 20.0f) pnn20Count++;
        }
        output[2] = sqrtf(sumSqDiff / (validCount - 1));  // RMSSD
        
        // pNN50 and pNN20 (percentage)
        output[3] = (float)pnn50Count / (validCount - 1) * 100.0f;  // pNN50
        output[4] = (float)pnn20Count / (validCount - 1) * 100.0f;  // pNN20
    }
};

#endif // FEATURE_EXTRACTOR_H

