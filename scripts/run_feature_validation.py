"""Quick script to run feature validation."""
import pandas as pd
from pathlib import Path
from preprocessing.validate_features import validate_features

# Load training data
train_df = pd.read_csv('data/processed/train/train.csv', index_col=0)
print(f'Loaded training data: {len(train_df)} rows, {len(train_df.columns)} columns')

# Run validation
results = validate_features(
    train_df,
    Path('config/feature_schema.yaml'),
    Path('artifacts/reports'),
)

print('\nValidation Results:')
print(f'  Schema valid: {results["schema_valid"]}')
print(f'  Constant features: {results["constant_features_count"]}')
print(f'  High correlation pairs: {results["high_corr_pairs_count"]}')
print(f'  Family coverage: {results["family_coverage"]}')
print('\nReports generated:')
print('  - artifacts/reports/feature_validation.md')
print('  - artifacts/reports/feature_validation.json')
