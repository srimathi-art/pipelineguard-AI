from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from ml_utils import clean_log

def train_and_save_model():
    data_path = Path("data/training_logs.csv")
    if not data_path.exists():
        from generate_data import generate_dataset
        generate_dataset()

    data = pd.read_csv(data_path)
    X = data["log"].astype(str).map(clean_log)
    y = data["severity"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
    print(classification_report(y_test, predictions))

    Path("models").mkdir(exist_ok=True)
    joblib.dump(model, "models/log_classifier.joblib")
    return model

if __name__ == "__main__":
    train_and_save_model()
