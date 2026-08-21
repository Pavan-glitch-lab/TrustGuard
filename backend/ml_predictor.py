import os
import joblib


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "trustguard_ml_model.joblib"
)


# Load the trained TrustGuard ML model
model = joblib.load(MODEL_PATH)


def predict_risk(action):
    """
    Predict the risk level of a user action.

    Returns:
        Low, Medium, or High
    """

    if not action:
        return "Low"

    prediction = model.predict([action])[0]

    return prediction