import os
import subprocess
import pickle
import pandas as pd
from zenml import step, pipeline
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder

@step
def extract_and_prepare_data() -> pd.DataFrame:
    """Run the existing extraction and bridging scripts, then load the data."""
    print("Running data extraction...")
    subprocess.run(["uv", "run", "python3", "src/zscore_extractor/extract_al_cutoffs.py", "-i", "data/raw", "-b", "data/bronze"], check=True)
    print("Generating combinations...")
    subprocess.run(["uv", "run", "python3", "src/generate_combinations.py"], check=True)
    print("Generating bridge tables...")
    subprocess.run(["uv", "run", "python3", "src/generate_bridge.py"], check=True)
    
    print("Loading extracted fact data...")
    df = pd.read_csv("data/bronze/csv/fact_cutoffs.csv")
    return df

@step
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and label encode categorical features for model training."""
    print("Engineering features...")
    df = df.dropna(subset=['CutoffZ'])
    
    le_course = LabelEncoder()
    le_uni = LabelEncoder()
    le_dist = LabelEncoder()
    
    df['Course_Enc'] = le_course.fit_transform(df['CourseName'])
    df['Uni_Enc'] = le_uni.fit_transform(df['UniversityName'])
    df['Dist_Enc'] = le_dist.fit_transform(df['DistrictName'])
    
    os.makedirs("models", exist_ok=True)
    with open("models/encoders.pkl", "wb") as f:
        pickle.dump({"course": le_course, "uni": le_uni, "dist": le_dist}, f)
        
    return df

@step
def train_model(df: pd.DataFrame) -> RandomForestRegressor:
    """Train a Random Forest Regressor to predict CutoffZ."""
    print("Training model...")
    features = ['ExamYear', 'Course_Enc', 'Uni_Enc', 'Dist_Enc']
    X = df[features]
    y = df['CutoffZ']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds, squared=False)
    print(f"Model trained. Validation MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    os.makedirs("models", exist_ok=True)
    with open("models/rf_model.pkl", "wb") as f:
        pickle.dump(model, f)
        
    return model

@pipeline
def al_trends_ml_pipeline():
    """ZenML Pipeline combining extraction, feature engineering, and training."""
    df = extract_and_prepare_data()
    df_features = feature_engineering(df)
    model = train_model(df_features)

if __name__ == "__main__":
    al_trends_ml_pipeline()
