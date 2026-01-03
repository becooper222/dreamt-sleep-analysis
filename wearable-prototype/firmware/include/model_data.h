/**
 * TFLite Model Data (Placeholder)
 * ================================
 * 
 * This file should be generated from your trained model using:
 *   xxd -i sleep_model.tflite > model_data.h
 * 
 * Then replace this placeholder with the generated content.
 * 
 * After training:
 *   1. Run: python scripts/train_tflite_model.py --data_dir ../data/dreamt
 *   2. Convert: xxd -i models/tflite_4class/sleep_model.tflite > firmware/include/model_data.h
 *   3. Copy scaler_params.h to firmware/include/
 */

#ifndef MODEL_DATA_H
#define MODEL_DATA_H

// Placeholder - replace with actual model bytes after training
// The trained model will be ~10-50 KB depending on architecture

unsigned char sleep_model_tflite[] = {
    // Model bytes will go here after running xxd -i
    0x00  // Placeholder
};

unsigned int sleep_model_tflite_len = 1;

#endif // MODEL_DATA_H

