import os
import pickle
import pandas as pd
from dagster import asset, get_dagster_logger
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

@asset
def engineered_features(denormalized_fact_data: pd.DataFrame) -> pd.DataFrame:
    """Clean data and label encode categorical features for model training."""
    logger = get_dagster_logger()
    df = denormalized_fact_data.copy()
    
    initial_count = len(df)
    df = df.dropna(subset=['CutoffZ']).copy()
    dropped_count = initial_count - len(df)
    
    if dropped_count / initial_count > 0.25:
        raise ValueError(f"Data Quality Alert: Dropped {dropped_count} rows due to missing CutoffZ (exceeds 25% threshold).")
    
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    df[['Course_Enc', 'Uni_Enc', 'Dist_Enc']] = encoder.fit_transform(df[['CourseName', 'UniversityName', 'DistrictName']])
    
    os.makedirs("models", exist_ok=True)
    with open("models/encoders.pkl", "wb") as f:
        pickle.dump(encoder, f)
        
    logger.info(f"Engineered features for {len(df)} records.")
    return df

@asset
def rf_model(engineered_features: pd.DataFrame) -> None:
    """Train a Random Forest Regressor to predict CutoffZ."""
    logger = get_dagster_logger()
    df = engineered_features
    
    features = ['ExamYear', 'Course_Enc', 'Uni_Enc', 'Dist_Enc']
    X = df[features]
    y = df['CutoffZ']
    
    # Time-based split to avoid data leakage
    latest_year = df['ExamYear'].max()
    train_mask = df['ExamYear'] < latest_year
    test_mask = df['ExamYear'] == latest_year
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds) ** 0.5
    
    logger.info(f"Model trained. Validation (Year {latest_year}) MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    os.makedirs("models", exist_ok=True)
    with open("models/rf_model.pkl", "wb") as f:
        pickle.dump(model, f)
