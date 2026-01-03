#!/usr/bin/env python3
"""
Sleep Stage Model Training Script

Train and evaluate sleep stage classification models on the DREAMT dataset.

Usage:
    python train_model.py --data-dir data/dreamt --model xgboost --output models/

Arguments:
    --data-dir: Path to DREAMT dataset
    --model: Model type (xgboost, lightgbm, random_forest)
    --output: Directory to save trained model
    --cv: Number of cross-validation folds
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import numpy as np
import pandas as pd
from tqdm import tqdm

from data.loader import DREAMTLoader
from features.extractor import FeatureExtractor
from models.classifiers import SleepStageClassifier


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Train sleep stage classification model'
    )
    parser.add_argument(
        '--data-dir', 
        type=str, 
        default='data/dreamt',
        help='Path to DREAMT dataset'
    )
    parser.add_argument(
        '--model', 
        type=str, 
        default='xgboost',
        choices=['xgboost', 'lightgbm', 'random_forest', 'svm'],
        help='Model type to train'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='models/',
        help='Output directory for saved model'
    )
    parser.add_argument(
        '--cv', 
        type=int, 
        default=5,
        help='Number of cross-validation folds'
    )
    parser.add_argument(
        '--participants', 
        type=int, 
        default=10,
        help='Number of participants to use (for quick testing)'
    )
    parser.add_argument(
        '--resolution', 
        type=str, 
        default='64Hz',
        choices=['64Hz', '100Hz'],
        help='Data resolution'
    )
    return parser.parse_args()


def main():
    """Main training routine."""
    args = parse_args()
    
    print("=" * 60)
    print("Sleep Stage Model Training")
    print("=" * 60)
    print(f"Data directory: {args.data_dir}")
    print(f"Model type: {args.model}")
    print(f"Resolution: {args.resolution}")
    print(f"CV folds: {args.cv}")
    print()
    
    # Check data directory
    data_path = Path(args.data_dir)
    if not data_path.exists():
        print(f"Error: Data directory not found: {data_path}")
        print("Please download the DREAMT dataset from PhysioNet.")
        sys.exit(1)
    
    # Initialize loader
    print("Loading data...")
    try:
        loader = DREAMTLoader(data_path, resolution=args.resolution)
        print(f"Found {len(loader.participants)} participants")
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
    
    # Select participants
    participants = loader.participants[:args.participants]
    print(f"Using {len(participants)} participants for training")
    
    # Extract features for all participants
    print("\nExtracting features...")
    extractor = FeatureExtractor(epoch_duration=30.0, fs=64.0)
    
    all_features = []
    for pid in tqdm(participants, desc="Processing"):
        try:
            df = loader.load_participant(pid)
            features = extractor.extract_all_features(df)
            features['participant'] = pid
            all_features.append(features)
        except Exception as e:
            print(f"Warning: Failed to process {pid}: {e}")
    
    # Combine all features
    if not all_features:
        print("Error: No features extracted!")
        sys.exit(1)
    
    combined = pd.concat(all_features, ignore_index=True)
    print(f"\nTotal epochs: {len(combined)}")
    print(f"Features: {combined.shape[1] - 2}")  # Exclude Sleep_Stage and participant
    
    # Prepare training data
    feature_cols = [c for c in combined.columns 
                   if c not in ['Sleep_Stage', 'participant']]
    
    X = combined[feature_cols].values
    y = combined['Sleep_Stage'].values
    
    # Handle missing values
    X = np.nan_to_num(X, nan=0.0)
    
    # Remove samples with missing labels
    valid_mask = ~pd.isna(y)
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"\nTraining samples: {len(X)}")
    print(f"Class distribution:")
    for stage in np.unique(y):
        count = np.sum(y == stage)
        pct = count / len(y) * 100
        print(f"  {stage}: {count} ({pct:.1f}%)")
    
    # Initialize model
    print(f"\nTraining {args.model} model...")
    model = SleepStageClassifier(model_type=args.model)
    
    # Cross-validation
    print(f"\nRunning {args.cv}-fold cross-validation...")
    cv_results = model.cross_validate(X, y, cv=args.cv)
    
    print(f"\nCV Results:")
    print(f"  Accuracy: {cv_results['cv_accuracy_mean']:.4f} ± {cv_results['cv_accuracy_std']:.4f}")
    
    # Train final model on all data
    print("\nTraining final model on all data...")
    model.fit(X, y)
    
    # Evaluate on training data (for reference)
    print("\nTraining set performance:")
    metrics = model.evaluate(X, y, verbose=True)
    
    # Get feature importance
    importance = model.get_feature_importance()
    if importance is not None:
        print("\nTop 10 Important Features:")
        print(importance.head(10).to_string(index=False))
    
    # Save model
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = output_dir / f"sleep_stage_{args.model}.joblib"
    model.save(str(model_path))
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print(f"Model saved to: {model_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

