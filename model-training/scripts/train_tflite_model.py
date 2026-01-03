#!/usr/bin/env python3
"""
Train 4-Class Sleep Stage Model for TFLite Deployment
======================================================

Trains an MLP model using only IMU and PPG features (compatible with ESP32 wearable).

Classes:
    0: Wake (W)
    1: Light Sleep (N1 + N2 merged)
    2: Deep Sleep (N3)
    3: REM (R)

Features:
    - IMU: ACC_X, ACC_Y, ACC_Z statistical features + magnitude
    - PPG: HR, HRV features derived from BVP

Usage:
    python train_tflite_model.py --data_dir ../data/dreamt --output_dir ../models/tflite_4class
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt

from data.loader import DREAMTLoader
from features.extractor import FeatureExtractor
from models.tflite_model import SleepStageMLP


# ============================================================================
# Feature Specification - Must match ESP32 implementation
# ============================================================================

# These are the ONLY features we'll use (IMU + PPG, no EDA/TEMP)
IMU_FEATURE_PREFIXES = ['imu_x', 'imu_y', 'imu_z', 'imu_mag']
PPG_FEATURE_PREFIXES = ['ppg', 'hr', 'hrv']

# Feature suffixes for statistical features
STAT_SUFFIXES = [
    'mean', 'std', 'min', 'max', 'range', 'median', 'iqr',
    'skew', 'kurtosis', 'energy', 'rms', 'zero_crossings'
]

# IMU-specific features
IMU_EXTRA_FEATURES = ['imu_activity_count', 'imu_movement_intensity']

# HRV features
HRV_FEATURES = ['hrv_mean_ibi', 'hrv_sdnn', 'hrv_rmssd', 'hrv_pnn50', 'hrv_pnn20']

# HR features
HR_FEATURES = ['hr_mean', 'hr_std', 'hr_min', 'hr_max', 'hr_range']


def get_feature_list() -> list:
    """
    Get the exact list of features used for training.
    This MUST match what the ESP32 can compute.
    
    Returns
    -------
    list
        Ordered list of feature names.
    """
    features = []
    
    # IMU statistical features (per axis + magnitude)
    for prefix in IMU_FEATURE_PREFIXES:
        for suffix in STAT_SUFFIXES:
            features.append(f'{prefix}_{suffix}')
    
    # IMU extra features
    features.extend(IMU_EXTRA_FEATURES)
    
    # PPG statistical features
    for suffix in STAT_SUFFIXES:
        features.append(f'ppg_{suffix}')
    
    # HR features
    features.extend(HR_FEATURES)
    
    # HRV features
    features.extend(HRV_FEATURES)
    
    return features


def filter_imu_ppg_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter DataFrame to keep only IMU and PPG-derived features.
    Excludes EDA and TEMP features.
    
    Parameters
    ----------
    df : pd.DataFrame
        Full feature DataFrame.
        
    Returns
    -------
    pd.DataFrame
        Filtered DataFrame with only IMU + PPG features.
    """
    # Get target feature list
    target_features = get_feature_list()
    
    # Find available features
    available = [f for f in target_features if f in df.columns]
    missing = [f for f in target_features if f not in df.columns]
    
    if missing:
        print(f"Warning: {len(missing)} features not found in data:")
        for f in missing[:10]:
            print(f"  - {f}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")
    
    print(f"Using {len(available)} features out of {len(target_features)} target features")
    
    # Add Sleep_Stage if present
    if 'Sleep_Stage' in df.columns:
        available.append('Sleep_Stage')
    
    return df[available].copy()


def extract_features_for_participant(
    loader: DREAMTLoader,
    participant_id: str,
    extractor: FeatureExtractor
) -> pd.DataFrame:
    """
    Extract features for a single participant.
    
    Parameters
    ----------
    loader : DREAMTLoader
        Data loader instance.
    participant_id : str
        Participant ID.
    extractor : FeatureExtractor
        Feature extraction instance.
        
    Returns
    -------
    pd.DataFrame
        Extracted features.
    """
    try:
        df = loader.load_participant(participant_id)
        features = extractor.extract_all_features(df, include_imu=True, include_ppg=True)
        features['participant'] = participant_id
        return features
    except Exception as e:
        print(f"Error processing {participant_id}: {e}")
        return pd.DataFrame()


def main(args):
    print("=" * 70)
    print("4-Class Sleep Stage Model Training for TFLite")
    print("=" * 70)
    print(f"\nClasses: Wake, Light (N1+N2), Deep (N3), REM")
    print(f"Features: IMU + PPG only (no EDA/TEMP)")
    print()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # 1. Load and Extract Features
    # ========================================================================
    print("\n[1/5] Loading DREAMT data and extracting features...")
    
    loader = DREAMTLoader(args.data_dir, resolution=args.resolution)
    print(f"Found {len(loader.participants)} participants")
    
    extractor = FeatureExtractor(
        epoch_duration=args.epoch_duration,
        fs=64.0 if args.resolution == '64Hz' else 100.0,
        overlap=0.0
    )
    
    # Extract features from all participants
    all_features = []
    
    participants = loader.participants[:args.max_participants] if args.max_participants else loader.participants
    
    for pid in tqdm(participants, desc="Extracting features"):
        features = extract_features_for_participant(loader, pid, extractor)
        if len(features) > 0:
            all_features.append(features)
    
    df_all = pd.concat(all_features, ignore_index=True)
    print(f"Total epochs extracted: {len(df_all)}")
    
    # ========================================================================
    # 2. Filter to IMU + PPG Features Only
    # ========================================================================
    print("\n[2/5] Filtering to IMU + PPG features only...")
    
    df_filtered = filter_imu_ppg_features(df_all)
    
    # Remove rows with missing values
    df_clean = df_filtered.dropna()
    print(f"Epochs after removing NaN: {len(df_clean)}")
    
    # Filter out invalid sleep stages
    valid_stages = ['W', 'N1', 'N2', 'N3', 'R']
    df_clean = df_clean[df_clean['Sleep_Stage'].isin(valid_stages)]
    print(f"Epochs with valid sleep stages: {len(df_clean)}")
    
    # Show stage distribution before merging
    print("\nOriginal 5-class distribution:")
    print(df_clean['Sleep_Stage'].value_counts())
    
    # ========================================================================
    # 3. Prepare Training Data
    # ========================================================================
    print("\n[3/5] Preparing training data...")
    
    # Separate features and labels
    feature_cols = [c for c in df_clean.columns if c not in ['Sleep_Stage', 'participant']]
    X = df_clean[feature_cols].values
    y = df_clean['Sleep_Stage'].values
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Number of features: {len(feature_cols)}")
    
    # Save feature list for ESP32
    feature_list_path = output_dir / 'feature_list.txt'
    with open(feature_list_path, 'w') as f:
        f.write("# Feature list for 4-class sleep stage model\n")
        f.write("# Order must match ESP32 feature extraction\n")
        f.write(f"# Total features: {len(feature_cols)}\n\n")
        for i, name in enumerate(feature_cols):
            f.write(f"{i:3d}: {name}\n")
    print(f"Feature list saved: {feature_list_path}")
    
    # Train/test split by participant (avoid data leakage)
    if 'participant' in df_clean.columns:
        participants = df_clean['participant'].unique()
        np.random.seed(42)
        np.random.shuffle(participants)
        
        n_train = int(len(participants) * 0.8)
        train_pids = participants[:n_train]
        test_pids = participants[n_train:]
        
        train_mask = df_clean['participant'].isin(train_pids)
        test_mask = df_clean['participant'].isin(test_pids)
        
        X_train = df_clean.loc[train_mask, feature_cols].values
        y_train = df_clean.loc[train_mask, 'Sleep_Stage'].values
        X_test = df_clean.loc[test_mask, feature_cols].values
        y_test = df_clean.loc[test_mask, 'Sleep_Stage'].values
        
        print(f"Train participants: {len(train_pids)}, Test participants: {len(test_pids)}")
    else:
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    
    print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    # ========================================================================
    # 4. Train Model
    # ========================================================================
    print("\n[4/5] Training MLP model...")
    
    model = SleepStageMLP(
        input_dim=len(feature_cols),
        hidden_layers=args.hidden_layers,
        dropout_rate=args.dropout,
        l2_reg=args.l2_reg
    )
    model.feature_names = feature_cols
    model.compile(learning_rate=args.learning_rate)
    
    print("\nModel Architecture:")
    model.summary()
    
    history = model.fit(
        X_train, y_train,
        validation_split=0.15,
        epochs=args.epochs,
        batch_size=args.batch_size,
        early_stopping_patience=args.patience,
        verbose=1
    )
    
    # Plot training history
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    axes[0].plot(history.history['loss'], label='Train')
    axes[0].plot(history.history['val_loss'], label='Validation')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(history.history['accuracy'], label='Train')
    axes[1].plot(history.history['val_accuracy'], label='Validation')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Training Accuracy')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'training_history.png', dpi=150)
    plt.close()
    print(f"Training history plot saved: {output_dir / 'training_history.png'}")
    
    # ========================================================================
    # 5. Evaluate and Export
    # ========================================================================
    print("\n[5/5] Evaluating and exporting model...")
    
    # Evaluate on test set
    metrics = model.evaluate(X_test, y_test, verbose=True)
    
    # Save metrics
    import json
    with open(output_dir / 'metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Save Keras model
    model.save(str(output_dir / 'keras_model'))
    
    # Convert to TFLite (with quantization for ESP32)
    tflite_path = str(output_dir / 'sleep_model.tflite')
    model.convert_to_tflite(
        tflite_path,
        quantize=args.quantize,
        representative_data=X_train[:1000] if args.quantize else None
    )
    
    # Export scaler for C++
    scaler_path = str(output_dir / 'scaler_params.h')
    model.export_scaler_for_cpp(scaler_path)
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    print(f"\nOutput files in: {output_dir}")
    print(f"  - keras_model/           : Full Keras model")
    print(f"  - sleep_model.tflite     : TFLite model for ESP32")
    print(f"  - scaler_params.h        : C++ header with scaler params")
    print(f"  - feature_list.txt       : Feature ordering specification")
    print(f"  - metrics.json           : Evaluation metrics")
    print(f"  - training_history.png   : Loss/accuracy plots")
    print(f"\nModel Performance:")
    print(f"  - Accuracy:   {metrics['accuracy']:.1%}")
    print(f"  - Macro F1:   {metrics['f1_macro']:.3f}")
    print(f"  - Cohen's κ:  {metrics['kappa']:.3f}")
    print("\nNext steps:")
    print("  1. Copy sleep_model.tflite to ESP32 (SPIFFS or embed in firmware)")
    print("  2. Copy scaler_params.h to firmware/include/")
    print("  3. Implement feature extraction in C++ matching feature_list.txt")
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Train 4-class sleep stage model for TFLite deployment'
    )
    
    # Data arguments
    parser.add_argument(
        '--data_dir', type=str, required=True,
        help='Path to DREAMT dataset directory'
    )
    parser.add_argument(
        '--output_dir', type=str, default='../models/tflite_4class',
        help='Output directory for trained model'
    )
    parser.add_argument(
        '--resolution', type=str, default='64Hz', choices=['64Hz', '100Hz'],
        help='Data resolution to use'
    )
    parser.add_argument(
        '--epoch_duration', type=float, default=30.0,
        help='Epoch duration in seconds'
    )
    parser.add_argument(
        '--max_participants', type=int, default=None,
        help='Maximum participants to use (for testing)'
    )
    
    # Model arguments
    parser.add_argument(
        '--hidden_layers', type=int, nargs='+', default=[64, 32, 16],
        help='Hidden layer sizes'
    )
    parser.add_argument(
        '--dropout', type=float, default=0.3,
        help='Dropout rate'
    )
    parser.add_argument(
        '--l2_reg', type=float, default=0.001,
        help='L2 regularization strength'
    )
    
    # Training arguments
    parser.add_argument(
        '--epochs', type=int, default=100,
        help='Maximum training epochs'
    )
    parser.add_argument(
        '--batch_size', type=int, default=64,
        help='Training batch size'
    )
    parser.add_argument(
        '--learning_rate', type=float, default=0.001,
        help='Initial learning rate'
    )
    parser.add_argument(
        '--patience', type=int, default=15,
        help='Early stopping patience'
    )
    parser.add_argument(
        '--quantize', action='store_true', default=True,
        help='Apply INT8 quantization for smaller model'
    )
    parser.add_argument(
        '--no-quantize', dest='quantize', action='store_false',
        help='Skip quantization'
    )
    
    args = parser.parse_args()
    main(args)

