import json
import os
import re
import secrets
from datetime import datetime, timedelta

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

USERS_FILE = os.path.join(
    BASE_DIR,
    "users.json"
)


# ============================================================
# USERS FILE
# ============================================================

def ensure_users_file():

    if not os.path.exists(USERS_FILE):

        with open(
            USERS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                [],
                file,
                indent=4
            )


def load_users():

    ensure_users_file()

    try:

        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            users = json.load(file)

            if isinstance(users, list):
                return users

            return []

    except (
        json.JSONDecodeError,
        OSError
    ):

        return []


def save_users(users):

    with open(
        USERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            users,
            file,
            indent=4
        )


# ============================================================
# VALIDATION
# ============================================================

def normalize_email(email):

    return (
        email or ""
    ).strip().lower()


def validate_email(email):

    pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}$"
    )

    return re.match(
        pattern,
        email
    ) is not None


def validate_password(password):

    return (
        isinstance(password, str)
        and len(password) >= 8
    )


# ============================================================
# REGISTER USER
# ============================================================

def register_user(
    full_name,
    email,
    mobile,
    password
):

    full_name = (
        full_name or ""
    ).strip()

    email = normalize_email(
        email
    )

    mobile = (
        mobile or ""
    ).strip()

    password = (
        password or ""
    )


    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    if not full_name:

        return False, {
            "error":
                "Full name is required."
        }


    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    if not email:

        return False, {
            "error":
                "Email is required."
        }


    if not validate_email(email):

        return False, {
            "error":
                "Please enter a valid email address."
        }


    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------

    if not validate_password(password):

        return False, {
            "error":
                "Password must contain at least 8 characters."
        }


    # --------------------------------------------------------
    # CHECK EXISTING USER
    # --------------------------------------------------------

    users = load_users()

    for user in users:

        existing_email = normalize_email(
            user.get(
                "email",
                ""
            )
        )

        if existing_email == email:

            return False, {
                "error":
                    "An account with this email already exists."
            }


    # --------------------------------------------------------
    # CREATE USER ID
    # --------------------------------------------------------

    user_id = datetime.now().strftime(
        "%Y%m%d%H%M%S%f"
    )


    # --------------------------------------------------------
    # HASH PASSWORD
    # --------------------------------------------------------

    password_hash = generate_password_hash(
        password
    )


    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    new_user = {

        "id":
            user_id,

        "full_name":
            full_name,

        "email":
            email,

        "mobile":
            mobile,

        "password_hash":
            password_hash,

        "created_at":
            datetime.now().isoformat(
                timespec="seconds"
            )
    }


    # --------------------------------------------------------
    # SAVE USER
    # --------------------------------------------------------

    users.append(
        new_user
    )

    save_users(
        users
    )


    # --------------------------------------------------------
    # RETURN SAFE USER DATA
    # DO NOT RETURN PASSWORD HASH
    # --------------------------------------------------------

    return True, {

        "id":
            new_user["id"],

        "full_name":
            new_user["full_name"],

        "email":
            new_user["email"],

        "mobile":
            new_user["mobile"],

        "created_at":
            new_user["created_at"]
    }


# ============================================================
# LOGIN
# ============================================================

def authenticate_user(
    email,
    password
):

    email = normalize_email(
        email
    )

    password = (
        password or ""
    )


    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if not email or not password:
        return None


    # --------------------------------------------------------
    # LOAD USERS
    # --------------------------------------------------------

    users = load_users()


    # --------------------------------------------------------
    # FIND USER
    # --------------------------------------------------------

    for user in users:

        stored_email = normalize_email(
            user.get(
                "email",
                ""
            )
        )

        if stored_email != email:
            continue


        # ----------------------------------------------------
        # GET PASSWORD HASH
        # ----------------------------------------------------

        password_hash = user.get(
            "password_hash",
            ""
        )


        if not password_hash:

            print(
                "LOGIN ERROR: User exists but has no password_hash:",
                email
            )

            return None


        # ----------------------------------------------------
        # CHECK PASSWORD
        # ----------------------------------------------------

        try:

            password_is_correct = (
                check_password_hash(
                    password_hash,
                    password
                )
            )

        except Exception as error:

            print(
                "LOGIN PASSWORD CHECK ERROR:",
                error
            )

            return None


        if password_is_correct:

            print(
                "LOGIN SUCCESS:",
                email
            )

            return {

                "id":
                    user.get(
                        "id"
                    ),

                "full_name":
                    user.get(
                        "full_name"
                    ),

                "email":
                    user.get(
                        "email"
                    ),

                "mobile":
                    user.get(
                        "mobile"
                    ),

                "created_at":
                    user.get(
                        "created_at"
                    )
            }


        # ----------------------------------------------------
        # EMAIL EXISTS BUT PASSWORD IS WRONG
        # ----------------------------------------------------

        print(
            "LOGIN FAILED: Incorrect password for:",
            email
        )

        return None


    # --------------------------------------------------------
    # USER NOT FOUND
    # --------------------------------------------------------

    print(
        "LOGIN FAILED: User not found:",
        email
    )

    return None


# ============================================================
# FIND USER BY EMAIL
# ============================================================

def find_user_by_email(email):

    email = normalize_email(
        email
    )

    users = load_users()

    for user in users:

        if normalize_email(
            user.get(
                "email",
                ""
            )
        ) == email:

            return user

    return None


# ============================================================
# CREATE PASSWORD RESET TOKEN
# ============================================================

def create_password_reset_token(email):

    email = normalize_email(
        email
    )

    users = load_users()

    for user in users:

        if normalize_email(
            user.get(
                "email",
                ""
            )
        ) != email:

            continue


        token = secrets.token_urlsafe(
            32
        )


        expires_at = (
            datetime.utcnow()
            + timedelta(
                minutes=15
            )
        ).isoformat()


        user["reset_token"] = token

        user["reset_expires"] = (
            expires_at
        )


        save_users(
            users
        )


        return token


    return None


# ============================================================
# RESET PASSWORD
# ============================================================

def reset_password(
    token,
    new_password
):

    if not validate_password(
        new_password
    ):

        return False, {
            "error":
                "Password must contain at least 8 characters."
        }


    users = load_users()

    now = datetime.utcnow()


    for user in users:

        if user.get(
            "reset_token"
        ) != token:

            continue


        expires_text = user.get(
            "reset_expires"
        )


        if not expires_text:

            return False, {
                "error":
                    "Reset token is invalid."
            }


        try:

            expires_at = datetime.fromisoformat(
                expires_text
            )

        except ValueError:

            return False, {
                "error":
                    "Reset token is invalid."
            }


        if now > expires_at:

            user.pop(
                "reset_token",
                None
            )

            user.pop(
                "reset_expires",
                None
            )

            save_users(
                users
            )

            return False, {
                "error":
                    "Reset token has expired."
            }


        # ----------------------------------------------------
        # UPDATE PASSWORD
        # ----------------------------------------------------

        user["password_hash"] = (
            generate_password_hash(
                new_password
            )
        )


        # ----------------------------------------------------
        # REMOVE USED RESET TOKEN
        # ----------------------------------------------------

        user.pop(
            "reset_token",
            None
        )

        user.pop(
            "reset_expires",
            None
        )


        save_users(
            users
        )


        return True, {
            "message":
                "Password has been reset successfully."
        }


    return False, {
        "error":
            "Invalid password reset token."
    }