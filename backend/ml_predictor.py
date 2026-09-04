import os
import re
import joblib


# ============================================================
# TRUSTGUARD ML PREDICTOR
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "trustguard_ml_model.joblib"
)


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

try:
    model = joblib.load(
        MODEL_PATH
    )

    MODEL_LOADED = True

    print(
        "TrustGuard ML model loaded successfully."
    )

except Exception as error:
    model = None
    MODEL_LOADED = False

    print(
        "WARNING: TrustGuard ML model could not be loaded."
    )

    print(
        "ML error:",
        error
    )


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_action(action):

    return re.sub(
        r"\s+",
        " ",
        str(action or "")
        .strip()
        .lower()
    )


# ============================================================
# CLEARLY LOW-RISK ACTIONS
# ============================================================

def is_clearly_low_risk(action):

    text = normalize_action(
        action
    )

    if not text:
        return False


    # --------------------------------------------------------
    # Simple communication / reminder actions
    # --------------------------------------------------------

    low_risk_patterns = [

        r"\bcreate a reminder\b",
        r"\bcreates a reminder\b",

        r"\bsend a reminder\b",
        r"\bsend reminder\b",

        r"\bsend an email\b",
        r"\bsend email\b",

        r"\bsend a notification\b",
        r"\bsend notification\b",

        r"\bsend a message\b",
        r"\bsend message\b",

        r"\bnotify the user\b",
        r"\bnotify a user\b",

        r"\bremind the user\b",
        r"\bremind a user\b",

        r"\bshow a notification\b",
        r"\bdisplay a notification\b",

        r"\bsend appointment reminder\b",
        r"\bsend a meeting reminder\b",
        r"\bsend a calendar reminder\b"
    ]


    for pattern in low_risk_patterns:

        if re.search(
            pattern,
            text
        ):
            return True


    # --------------------------------------------------------
    # Informational actions
    # --------------------------------------------------------

    informational_patterns = [

        r"\bshow information\b",
        r"\bdisplay information\b",

        r"\bshow the user\b",
        r"\bdisplay the user\b",

        r"\bprovide information\b",
        r"\bprovide details\b",

        r"\bexplain\b",

        r"\bsummarize\b",
        r"\bsummarise\b"
    ]


    for pattern in informational_patterns:

        if re.search(
            pattern,
            text
        ):
            return True


    return False


# ============================================================
# CLEARLY HIGH-RISK ACTIONS
# ============================================================

def is_clearly_high_risk(action):

    text = normalize_action(
        action
    )

    if not text:
        return False


    high_risk_patterns = [

        # ----------------------------------------------------
        # Financial
        # ----------------------------------------------------

        r"\btransfer\s+\$?\d+",
        r"\btransfer\s+₹?\d+",

        r"\btransfer money\b",
        r"\btransfer funds\b",
        r"\bmove money\b",

        r"\bwithdraw money\b",

        r"\bmake a payment\b",
        r"\bmake payment\b",

        r"\bapprove a loan\b",
        r"\bapprove loan\b",


        # ----------------------------------------------------
        # Account / security
        # ----------------------------------------------------

        r"\bdelete the account\b",
        r"\bdelete an account\b",
        r"\bdelete user account\b",

        r"\bdisable security\b",
        r"\bdisable authentication\b",
        r"\bdisable 2fa\b",
        r"\bdisable two-factor\b",


        # ----------------------------------------------------
        # Irreversible actions
        # ----------------------------------------------------

        r"\bpermanently delete\b",
        r"\bpermanently remove\b",
        r"\bdelete permanently\b",


        # ----------------------------------------------------
        # External / high-impact actions
        # ----------------------------------------------------

        r"\bterminate employment\b",
        r"\bfire the employee\b",
        r"\bfire an employee\b",

        r"\bdeny insurance\b",
        r"\bdeny a claim\b",

        r"\bapprove surgery\b",
        r"\bprescribe medication\b",
        r"\bdiagnose the patient\b"
    ]


    for pattern in high_risk_patterns:

        if re.search(
            pattern,
            text
        ):
            return True


    return False


# ============================================================
# MODEL PREDICTION
# ============================================================

def get_model_prediction(action):

    if not MODEL_LOADED:
        return "Medium"


    try:

        prediction = model.predict(
            [action]
        )[0]

        prediction = str(
            prediction
        ).strip()


        # ----------------------------------------------------
        # Normalize model output
        # ----------------------------------------------------

        normalized = prediction.lower()


        if "high" in normalized:
            return "High"


        if "medium" in normalized:
            return "Medium"


        if "low" in normalized:
            return "Low"


        # ----------------------------------------------------
        # Unknown model output
        # ----------------------------------------------------

        return "Medium"


    except Exception as error:

        print(
            "ML prediction error:",
            error
        )

        return "Medium"


# ============================================================
# PUBLIC PREDICTION FUNCTION
# ============================================================

def predict_risk(action):

    """
    Predict the risk level of a TrustGuard action.

    Returns:

        Low
        Medium
        High

    The predictor keeps the trained ML model,

    while protecting clearly obvious low-risk and
    high-risk actions from unreasonable model output.
    """


    action = str(
        action or ""
    ).strip()


    # --------------------------------------------------------
    # Empty action
    # --------------------------------------------------------

    if not action:
        return "Low"


    # --------------------------------------------------------
    # Clearly high-risk actions
    #
    # These should never be downgraded by an ML mistake.
    # --------------------------------------------------------

    if is_clearly_high_risk(
        action
    ):
        return "High"


    # --------------------------------------------------------
    # Clearly low-risk actions
    #
    # Prevents simple actions such as:
    #
    # "Create a reminder..."
    # "Send a reminder..."
    # "Explain..."
    #
    # from being incorrectly classified as High
    # by the trained model.
    # --------------------------------------------------------

    if is_clearly_low_risk(
        action
    ):
        return "Low"


    # --------------------------------------------------------
    # Everything else goes through the trained model
    # --------------------------------------------------------

    return get_model_prediction(
        action
    )