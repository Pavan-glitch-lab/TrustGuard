# TrustGuard Risk Engine
# Five-factor risk assessment based on the TrustGuard research paper.

import re


def calculate_risk(action):
    text = action.lower().strip()

    # =========================================================
    # 1. PRIVACY RISK
    # =========================================================

    privacy_keywords = [
        "password",
        "aadhaar",
        "aadhar",
        "pan card",
        "personal information",
        "personal data",
        "private information",
        "confidential",
        "identity",
        "medical record",
        "medical data",
        "credentials",
        "otp",
        "phone number",
        "email address",
    ]

    privacy_matches = [
        keyword for keyword in privacy_keywords
        if keyword in text
    ]

    privacy_score = min(len(privacy_matches), 5)

    # =========================================================
    # 2. FINANCIAL RISK
    # =========================================================

    financial_keywords = [
        "transfer",
        "payment",
        "pay",
        "purchase",
        "buy",
        "bank",
        "money",
        "rupee",
        "credit card",
        "debit card",
        "upi",
        "transaction",
    ]

    financial_matches = [
        keyword for keyword in financial_keywords
        if keyword in text
    ]

    financial_score = min(len(financial_matches), 5)

    # Detect monetary amounts
    amount_detected = bool(
        re.search(
            r"(₹|\brs\.?\b|\brupees?\b|\bdollars?\b|\$)\s*[\d,]+",
            text,
        )
    )

    if amount_detected:
        financial_score = min(financial_score + 1, 5)

    # Significant transaction amount
    large_amount = bool(
        re.search(
            r"(₹|\brs\.?\b|\brupees?\b|\$|\bdollars?\b)\s*"
            r"(?:[1-9]\d{4,}|[\d,]{6,})",
            text,
        )
    )

    if large_amount:
        financial_score = 5

    # =========================================================
    # 3. DATA MODIFICATION RISK
    # =========================================================

    data_keywords = [
        "delete",
        "remove",
        "modify",
        "change",
        "edit",
        "overwrite",
        "update",
        "rename",
        "format",
        "database",
        "file",
        "folder",
        "configuration",
        "settings",
    ]

    data_matches = [
        keyword for keyword in data_keywords
        if keyword in text
    ]

    data_score = min(len(data_matches), 5)

    if "delete permanently" in text or "factory reset" in text:
        data_score = 5

    # =========================================================
    # 4. IRREVERSIBILITY RISK
    # =========================================================

    irreversible_keywords = [
        "delete permanently",
        "permanently",
        "transfer",
        "send",
        "publish",
        "post",
        "submit",
        "terminate",
        "close account",
        "remove permanently",
        "factory reset",
    ]

    irreversible_matches = [
        keyword for keyword in irreversible_keywords
        if keyword in text
    ]

    irreversible_score = min(len(irreversible_matches), 5)

    if "transfer" in text:
        irreversible_score = max(irreversible_score, 4)

    # =========================================================
    # 5. EXTERNAL IMPACT
    # =========================================================

    external_keywords = [
        "send",
        "email",
        "upload",
        "publish",
        "post",
        "portal",
        "website",
        "external",
        "another person",
        "bank",
        "online",
        "social media",
        "college",
    ]

    external_matches = [
        keyword for keyword in external_keywords
        if keyword in text
    ]

    external_score = min(len(external_matches), 5)

    if "upload" in text and (
        "portal" in text or "website" in text
    ):
        external_score = max(external_score, 5)

    if "transfer" in text and "bank" in text:
        external_score = max(external_score, 5)

    # =========================================================
    # SPECIAL CONTEXTUAL RULES
    # =========================================================

    # College portal upload
    if "upload" in text and "college portal" in text:
        privacy_score = max(privacy_score, 1)
        external_score = 5

    # Bank transfer to newly added account
    if (
        "transfer" in text
        and "newly added bank account" in text
    ):
        financial_score = 5
        irreversible_score = 5
        external_score = 5

    # =========================================================
    # TOTAL SCORE
    # =========================================================

    total_score = (
        privacy_score
        + financial_score
        + data_score
        + irreversible_score
        + external_score
    )

    # =========================================================
    # RISK CLASSIFICATION
    # =========================================================
    #
    # 0 - 2  = LOW
    # 3 - 8  = MEDIUM
    # 9+     = HIGH
    #
    # =========================================================

    if total_score <= 2:
        risk_level = "Low"
        decision = "Autonomous Execution"

    elif total_score <= 8:
        risk_level = "Medium"
        decision = "User Confirmation"

    else:
        risk_level = "High"
        decision = "Human Approval"

    # =========================================================
    # EXPLANATION
    # =========================================================

    explanation = []

    if privacy_score > 0:
        explanation.append(
            f"Privacy-related information detected ({privacy_score}/5)."
        )

    if financial_score > 0:
        explanation.append(
            f"Financial activity detected ({financial_score}/5)."
        )

    if data_score > 0:
        explanation.append(
            f"Data modification risk detected ({data_score}/5)."
        )

    if irreversible_score > 0:
        explanation.append(
            f"Potentially irreversible action detected "
            f"({irreversible_score}/5)."
        )

    if external_score > 0:
        explanation.append(
            f"External impact detected ({external_score}/5)."
        )

    if not explanation:
        explanation.append(
            "No significant risk indicators were detected."
        )

    # =========================================================
    # FINAL RESULT
    # =========================================================

    return {
        "action": action,

        "risk_factors": {
            "privacy_risk": privacy_score,
            "financial_risk": financial_score,
            "data_modification_risk": data_score,
            "irreversibility_risk": irreversible_score,
            "external_impact": external_score,
        },

        "total_score": total_score,
        "risk_level": risk_level,
        "decision": decision,
        "explanation": explanation,
    }