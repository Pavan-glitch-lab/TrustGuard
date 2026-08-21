import json
import os
import secrets
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from flask import (
    Flask,
    request,
    jsonify,
    session,
    redirect,
    send_from_directory
)

from flask_cors import CORS

from auth import (
    register_user,
    authenticate_user,
    find_user_by_email,
    create_password_reset_token,
    reset_password
)

from risk_engine import calculate_risk
from ml_predictor import predict_risk
from hybrid_engine import calculate_hybrid_decision


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# TRUSTGUARD APP
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "TRUSTGUARD_SECRET_KEY",
    "trustguard-development-secret-change-this"
)

CORS(
    app,
    supports_credentials=True
)


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

APPROVAL_HISTORY_FILE = os.path.join(
    BASE_DIR,
    "approval_history.json"
)


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

GMAIL_SMTP_SERVER = os.environ.get(
    "GMAIL_SMTP_SERVER",
    "smtp.gmail.com"
)

GMAIL_SMTP_PORT = int(
    os.environ.get(
        "GMAIL_SMTP_PORT",
        "587"
    )
)

GMAIL_USERNAME = os.environ.get(
    "GMAIL_USERNAME",
    ""
)

GMAIL_APP_PASSWORD = os.environ.get(
    "GMAIL_APP_PASSWORD",
    ""
)

GMAIL_FROM_NAME = os.environ.get(
    "GMAIL_FROM_NAME",
    "TrustGuard AI"
)

RESET_URL = os.environ.get(
    "RESET_URL",
    "http://127.0.0.1:5000/reset-password.html"
)


# ============================================================
# SEND PASSWORD RESET EMAIL
# ============================================================

def send_password_reset_email(
    recipient_email,
    reset_url
):

    if not GMAIL_USERNAME:

        raise RuntimeError(
            "GMAIL_USERNAME is not configured in .env"
        )

    if not GMAIL_APP_PASSWORD:

        raise RuntimeError(
            "GMAIL_APP_PASSWORD is not configured in .env"
        )


    subject = "TrustGuard AI - Reset Your Password"


    plain_text = f"""
Hello,

We received a request to reset the password for your TrustGuard AI account.

Click the link below to create a new password:

{reset_url}

This link will expire in 15 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
{GMAIL_FROM_NAME}
"""


    html = f"""
<!DOCTYPE html>

<html>

<head>

    <meta charset="UTF-8">

    <title>Reset Your TrustGuard Password</title>

</head>

<body
    style="
        margin:0;
        padding:0;
        background:#f4f7fb;
        font-family:Arial,sans-serif;
    "
>

    <div
        style="
            max-width:600px;
            margin:40px auto;
            background:#ffffff;
            padding:35px;
            border-radius:12px;
            box-shadow:0 4px 20px rgba(0,0,0,0.08);
        "
    >

        <h2
            style="
                color:#1f2937;
                margin-top:0;
            "
        >
            🛡️ TrustGuard AI
        </h2>

        <h3
            style="
                color:#1f2937;
            "
        >
            Reset Your Password
        </h3>

        <p
            style="
                color:#4b5563;
                line-height:1.6;
            "
        >
            We received a request to reset the password
            for your TrustGuard AI account.
        </p>

        <p
            style="
                color:#4b5563;
                line-height:1.6;
            "
        >
            Click the button below to create a new password.
        </p>

        <p
            style="
                text-align:center;
                margin:30px 0;
            "
        >

            <a
                href="{reset_url}"
                style="
                    display:inline-block;
                    padding:14px 25px;
                    background:#2563eb;
                    color:#ffffff;
                    text-decoration:none;
                    border-radius:8px;
                    font-weight:bold;
                "
            >
                Reset Password
            </a>

        </p>

        <p
            style="
                color:#6b7280;
                font-size:14px;
                line-height:1.6;
            "
        >
            This password reset link will expire in
            <strong>15 minutes</strong>.
        </p>

        <p
            style="
                color:#6b7280;
                font-size:14px;
                line-height:1.6;
            "
        >
            If you did not request a password reset,
            you can safely ignore this email.
        </p>

        <hr
            style="
                border:none;
                border-top:1px solid #e5e7eb;
                margin:30px 0;
            "
        >

        <p
            style="
                color:#9ca3af;
                font-size:12px;
            "
        >
            {GMAIL_FROM_NAME}
        </p>

    </div>

</body>

</html>
"""


    message = MIMEMultipart(
        "alternative"
    )

    message["Subject"] = subject

    message["From"] = (
        f"{GMAIL_FROM_NAME} <{GMAIL_USERNAME}>"
    )

    message["To"] = recipient_email


    message.attach(
        MIMEText(
            plain_text,
            "plain"
        )
    )

    message.attach(
        MIMEText(
            html,
            "html"
        )
    )


    with smtplib.SMTP(
        GMAIL_SMTP_SERVER,
        GMAIL_SMTP_PORT
    ) as server:

        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(
            GMAIL_USERNAME,
            GMAIL_APP_PASSWORD
        )

        server.sendmail(
            GMAIL_USERNAME,
            recipient_email,
            message.as_string()
        )


# ============================================================
# GOOGLE OAUTH CONFIGURATION
# ============================================================

GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_CLIENT_ID",
    ""
)

GOOGLE_CLIENT_SECRET = os.environ.get(
    "GOOGLE_CLIENT_SECRET",
    ""
)

GOOGLE_REDIRECT_URI = (
    "http://127.0.0.1:5000/auth/google/callback"
)

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]


# ============================================================
# APPROVAL HISTORY
# ============================================================

def ensure_approval_history_file():

    if not os.path.exists(
        APPROVAL_HISTORY_FILE
    ):

        with open(
            APPROVAL_HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                [],
                file,
                indent=4
            )


def load_approval_history():

    ensure_approval_history_file()

    try:

        with open(
            APPROVAL_HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            history = json.load(file)

            if isinstance(history, list):
                return history

            return []

    except (
        json.JSONDecodeError,
        OSError
    ):

        return []


def save_approval_history(history):

    with open(
        APPROVAL_HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            indent=4
        )


# ============================================================
# LOGIN REQUIRED
# ============================================================

def login_required(function):

    @wraps(function)
    def decorated_function(
        *args,
        **kwargs
    ):

        if "user_id" not in session:

            return jsonify({

                "error":
                    "Authentication required.",

                "authenticated":
                    False

            }), 401

        return function(
            *args,
            **kwargs
        )

    return decorated_function


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_DIR = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "frontend"
    )
)


@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_DIR,
        "login.html"
    )


@app.route("/<path:filename>")
def frontend_files(filename):

    return send_from_directory(
        FRONTEND_DIR,
        filename
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/api/register",
    methods=["POST"]
)
def register():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    full_name = (
        data.get(
            "full_name",
            ""
        )
        .strip()
    )

    email = (
        data.get(
            "email",
            ""
        )
        .strip()
        .lower()
    )

    mobile = (
        data.get(
            "mobile",
            ""
        )
        .strip()
    )

    password = data.get(
        "password",
        ""
    )

    confirm_password = data.get(
        "confirm_password",
        ""
    )


    if not full_name:

        return jsonify({
            "error":
                "Full name is required."
        }), 400


    if not email:

        return jsonify({
            "error":
                "Email is required."
        }), 400


    if not password:

        return jsonify({
            "error":
                "Password is required."
        }), 400


    if password != confirm_password:

        return jsonify({
            "error":
                "Passwords do not match."
        }), 400


    success, result = register_user(
        full_name,
        email,
        mobile,
        password
    )


    if not success:

        return jsonify(
            result
        ), 400


    return jsonify({

        "message":
            "Account created successfully.",

        "user":
            result

    }), 201


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/api/login",
    methods=["POST"]
)
def login():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    email = (
        data.get(
            "email",
            ""
        )
        .strip()
        .lower()
    )

    password = data.get(
        "password",
        ""
    )


    if not email:

        return jsonify({
            "error":
                "Email is required."
        }), 400


    if not password:

        return jsonify({
            "error":
                "Password is required."
        }), 400


    user = authenticate_user(
        email,
        password
    )


    if user is None:

        return jsonify({
            "error":
                "Invalid email or password.",
            "authenticated":
                False
        }), 401


    session.clear()

    session["user_id"] = user["id"]

    session["user_email"] = user["email"]

    session["user_name"] = user["full_name"]

    session["login_method"] = "password"


    return jsonify({

        "message":
            "Login successful.",

        "authenticated":
            True,

        "user":
            user

    }), 200


# ============================================================
# CURRENT USER
# ============================================================

@app.route(
    "/api/me",
    methods=["GET"]
)
def current_user():

    if "user_id" not in session:

        return jsonify({

            "authenticated":
                False,

            "user":
                None

        }), 200


    return jsonify({

        "authenticated":
            True,

        "user": {

            "id":
                session.get(
                    "user_id"
                ),

            "full_name":
                session.get(
                    "user_name"
                ),

            "email":
                session.get(
                    "user_email"
                ),

            "login_method":
                session.get(
                    "login_method",
                    "password"
                )
        }

    }), 200


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/api/logout",
    methods=["POST"]
)
def logout():

    session.clear()

    return jsonify({

        "message":
            "Logged out successfully.",

        "authenticated":
            False

    }), 200


# ============================================================
# DASHBOARD
# ============================================================

@app.route(
    "/api/dashboard",
    methods=["GET"]
)
@login_required
def dashboard():

    return jsonify({

        "message":
            "Welcome to the TrustGuard dashboard.",

        "user": {

            "id":
                session.get(
                    "user_id"
                ),

            "full_name":
                session.get(
                    "user_name"
                ),

            "email":
                session.get(
                    "user_email"
                )
        }

    }), 200


# ============================================================
# ANALYZE ACTION
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
@login_required
def analyze():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    action = (
        data.get(
            "action",
            ""
        )
        .strip()
    )


    if not action:

        return jsonify({
            "error":
                "Action is required."
        }), 400


    # --------------------------------------------------------
    # RULE ENGINE
    # --------------------------------------------------------

    rule_result = calculate_risk(
        action
    )


    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    ml_risk = predict_risk(
        action
    )


    # --------------------------------------------------------
    # HYBRID DECISION
    # --------------------------------------------------------

    hybrid_result = calculate_hybrid_decision(
        rule_result,
        ml_risk
    )


    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return jsonify({

        "action":
            action,

        "risk_level":
            hybrid_result[
                "final_risk_level"
            ],

        "decision":
            hybrid_result[
                "final_decision"
            ],

        "rule_risk_level":
            rule_result[
                "risk_level"
            ],

        "rule_decision":
            rule_result[
                "decision"
            ],

        "total_score":
            rule_result[
                "total_score"
            ],

        "risk_factors":
            rule_result[
                "risk_factors"
            ],

        "explanation":
            rule_result[
                "explanation"
            ],

        "ml_prediction":
            ml_risk,

        "hybrid_analysis":
            hybrid_result

    }), 200


# ============================================================
# GET APPROVAL HISTORY
# ============================================================

@app.route(
    "/approval-history",
    methods=["GET"]
)
@login_required
def get_approval_history():

    history = load_approval_history()


    user_id = session.get(
        "user_id"
    )


    user_history = [

        item

        for item in history

        if str(
            item.get("user_id", "")
        ) == str(user_id)

    ]


    return jsonify({

        "history":
            user_history

    }), 200


# ============================================================
# SAVE APPROVAL HISTORY
# ============================================================

@app.route(
    "/approval-history",
    methods=["POST"]
)
@login_required
def add_approval_history():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    action = (
        data.get(
            "action",
            ""
        )
        .strip()
    )

    risk = (
        data.get(
            "risk",
            ""
        )
        .strip()
    )

    decision = (
        data.get(
            "decision",
            ""
        )
        .strip()
    )

    ml_prediction = (
        data.get(
            "ml_prediction",
            ""
        )
        .strip()
    )

    human_decision = (
        data.get(
            "human_decision",
            ""
        )
        .strip()
        .upper()
    )


    if not action:

        return jsonify({
            "error":
                "Action is required."
        }), 400


    allowed_human_decisions = {
        "",
        "APPROVED",
        "REJECTED",
        "CANCELLED",
        "PENDING"
    }


    if (
        human_decision
        not in allowed_human_decisions
    ):

        return jsonify({

            "error":
                "Invalid human decision."

        }), 400


    history = load_approval_history()


    record = {

        "id":
            datetime.now().strftime(
                "%Y%m%d%H%M%S%f"
            ),

        "action":
            action,

        "risk":
            risk,

        "decision":
            decision,

        "ml_prediction":
            ml_prediction,

        "human_decision":
            human_decision,

        "user_id":
            session.get(
                "user_id"
            ),

        "timestamp":
            datetime.now().isoformat(
                timespec="seconds"
            )
    }


    history.append(
        record
    )


    save_approval_history(
        history
    )


    return jsonify({

        "message":
            "Approval history saved.",

        "record":
            record

    }), 201


# ============================================================
# GOOGLE LOGIN
# ============================================================

@app.route(
    "/auth/google",
    methods=["GET"]
)
def google_login():

    if not GOOGLE_CLIENT_ID:

        return jsonify({

            "error":
                "Google OAuth is not configured.",

            "setup":
                "Set GOOGLE_CLIENT_ID before using Google login."

        }), 503


    if not GOOGLE_CLIENT_SECRET:

        return jsonify({

            "error":
                "Google OAuth client secret is not configured."

        }), 503


    state = secrets.token_urlsafe(
        32
    )

    session["google_oauth_state"] = (
        state
    )


    authorization_endpoint = (
        "https://accounts.google.com/o/oauth2/v2/auth"
    )


    params = {

        "client_id":
            GOOGLE_CLIENT_ID,

        "redirect_uri":
            GOOGLE_REDIRECT_URI,

        "response_type":
            "code",

        "scope":
            " ".join(
                GOOGLE_SCOPES
            ),

        "state":
            state,

        "access_type":
            "offline",

        "prompt":
            "select_account"
    }


    authorization_url = (
        authorization_endpoint
        + "?"
        + urlencode(params)
    )


    return redirect(
        authorization_url
    )


# ============================================================
# GOOGLE CALLBACK
# ============================================================

@app.route(
    "/auth/google/callback",
    methods=["GET"]
)
def google_callback():

    if not GOOGLE_CLIENT_ID:

        return (
            "Google OAuth is not configured.",
            503
        )


    if not GOOGLE_CLIENT_SECRET:

        return (
            "Google OAuth client secret is not configured.",
            503
        )


    returned_state = request.args.get(
        "state"
    )

    saved_state = session.get(
        "google_oauth_state"
    )


    if (
        not returned_state
        or returned_state != saved_state
    ):

        return jsonify({

            "error":
                "Invalid OAuth state."

        }), 400


    code = request.args.get(
        "code"
    )


    if not code:

        error = request.args.get(
            "error",
            "Google authentication was cancelled."
        )

        return jsonify({

            "error":
                error

        }), 400


    # --------------------------------------------------------
    # Exchange Google authorization code
    # --------------------------------------------------------

    token_response = requests.post(

        "https://oauth2.googleapis.com/token",

        data={

            "code":
                code,

            "client_id":
                GOOGLE_CLIENT_ID,

            "client_secret":
                GOOGLE_CLIENT_SECRET,

            "redirect_uri":
                GOOGLE_REDIRECT_URI,

            "grant_type":
                "authorization_code"
        },

        timeout=15
    )


    if not token_response.ok:

        return jsonify({

            "error":
                "Google token exchange failed."

        }), 400


    token_data = (
        token_response.json()
    )


    access_token = token_data.get(
        "access_token"
    )


    if not access_token:

        return jsonify({

            "error":
                "Google did not return an access token."

        }), 400


    # --------------------------------------------------------
    # Get Google user information
    # --------------------------------------------------------

    user_response = requests.get(

        "https://openidconnect.googleapis.com/v1/userinfo",

        headers={

            "Authorization":
                f"Bearer {access_token}"

        },

        timeout=15
    )


    if not user_response.ok:

        return jsonify({

            "error":
                "Could not retrieve Google account information."

        }), 400


    google_user = (
        user_response.json()
    )


    google_id = google_user.get(
        "sub"
    )

    email = (
        google_user.get(
            "email",
            ""
        )
        .strip()
        .lower()
    )

    name = (
        google_user.get(
            "name",
            "Google User"
        )
        .strip()
    )


    if not google_id or not email:

        return jsonify({

            "error":
                "Google account information is incomplete."

        }), 400


    # --------------------------------------------------------
    # Find or create TrustGuard account
    # --------------------------------------------------------

    user = find_user_by_email(
        email
    )


    if user is None:

        success, result = register_user(

            name,

            email,

            "",

            secrets.token_urlsafe(
                32
            )
        )


        if not success:

            return jsonify(
                result
            ), 400


        user = result


    # --------------------------------------------------------
    # Create TrustGuard session
    # --------------------------------------------------------

    session.clear()

    session["user_id"] = user["id"]

    session["user_email"] = user["email"]

    session["user_name"] = user["full_name"]

    session["login_method"] = "google"


    return redirect(
        "/index.html"
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@app.route(
    "/api/forgot-password",
    methods=["POST"]
)
def forgot_password():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    email = (
        data.get(
            "email",
            ""
        )
        .strip()
        .lower()
    )


    if not email:

        return jsonify({

            "error":
                "Email is required."

        }), 400


    token = create_password_reset_token(
        email
    )


    response = {

        "message":
            "If an account exists for this email, a password reset link has been sent."

    }


    # --------------------------------------------------------
    # SEND RESET EMAIL
    # --------------------------------------------------------

    if token:

        reset_url = (
            RESET_URL
            + (
                "&"
                if "?" in RESET_URL
                else "?"
            )
            + urlencode({
                "token": token
            })
        )


        try:

            send_password_reset_email(
                email,
                reset_url
            )

            print(
                f"Password reset email sent to {email}"
            )

        except Exception as error:

            print(
                "Password reset email error:",
                error
            )


    return jsonify(
        response
    ), 200


# ============================================================
# RESET PASSWORD
# ============================================================

@app.route(
    "/api/reset-password",
    methods=["POST"]
)
def reset_password_endpoint():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    token = (
        data.get(
            "token",
            ""
        )
        .strip()
    )

    new_password = data.get(
        "new_password",
        ""
    )

    confirm_password = data.get(
        "confirm_password",
        ""
    )


    if not token:

        return jsonify({

            "error":
                "Reset token is required."

        }), 400


    if not new_password:

        return jsonify({

            "error":
                "New password is required."

        }), 400


    if new_password != confirm_password:

        return jsonify({

            "error":
                "Passwords do not match."

        }), 400


    success, result = reset_password(

        token,

        new_password

    )


    if not success:

        return jsonify(
            result
        ), 400


    return jsonify(
        result
    ), 200


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status":
            "ok",

        "service":
            "TrustGuard Backend"

    }), 200


# ============================================================
# START FLASK
# ============================================================

if __name__ == "__main__":

    print("")
    print("========================================")
    print("       TRUSTGUARD BACKEND")
    print("========================================")

    print(
        "Server: http://127.0.0.1:5000"
    )

    print("")

    print("Authentication:")
    print("POST /api/register")
    print("POST /api/login")
    print("GET  /api/me")
    print("POST /api/logout")

    print("")

    print("Google:")
    print("GET  /auth/google")
    print("GET  /auth/google/callback")

    print("")

    print("Password Reset:")
    print("POST /api/forgot-password")
    print("POST /api/reset-password")

    print("")

    print("TrustGuard:")
    print("POST /analyze")
    print("GET  /approval-history")
    print("POST /approval-history")

    print("")

    print("Health:")
    print("GET  /health")

    print("========================================")
    print("")


    app.run(
    host="0.0.0.0",
    port=5000,
    debug=True
)