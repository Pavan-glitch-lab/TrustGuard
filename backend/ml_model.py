import os
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib


# -----------------------------
# Paths
# -----------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "development.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "backend",
    "models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "trustguard_ml_model.joblib"
)


# -----------------------------
# Load dataset
# -----------------------------

print("Loading TrustGuard dataset...")

df = pd.read_csv(DATASET_PATH)

print(f"Total scenarios: {len(df)}")


# -----------------------------
# Prepare data
# -----------------------------

X = df["action"].astype(str)
y = df["risk_level"].astype(str)


# -----------------------------
# Train / test split
# -----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}")


# -----------------------------
# Build ML pipeline
# -----------------------------

model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2)
        )
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1000
        )
    )
])


# -----------------------------
# Train model
# -----------------------------

print("\nTraining TrustGuard ML model...")

model.fit(X_train, y_train)


# -----------------------------
# Evaluate model
# -----------------------------

predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\n==============================")
print("TrustGuard ML Evaluation")
print("==============================")

print(f"Accuracy: {accuracy:.4f}")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# -----------------------------
# Save model
# -----------------------------

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)

joblib.dump(
    model,
    MODEL_PATH
)

print("\n==============================")
print("Model saved successfully!")
print("==============================")

print(MODEL_PATH)