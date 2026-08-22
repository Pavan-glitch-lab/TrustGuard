# TrustGuard Hybrid Decision Engine
# Combines rule-based analysis with AI/ML prediction.

def calculate_hybrid_decision(rule_result, ml_prediction):

    # =========================================================
    # RISK LEVELS
    # =========================================================

    risk_values = {
        "Low": 1,
        "Medium": 2,
        "High": 3
    }

    # =========================================================
    # GET RULE ENGINE RESULT
    # =========================================================

    rule_risk = rule_result.get("risk_level", "Low")

    # ---------------------------------------------------------
    # IMPORTANT:
    # Use total_score as the authoritative rule-based result.
    #
    # 0-2  = Low
    # 3-8  = Medium
    # 9+   = High
    # ---------------------------------------------------------

    total_score = rule_result.get("total_score")

    if total_score is not None:

        if total_score <= 2:
            rule_risk = "Low"

        elif total_score <= 8:
            rule_risk = "Medium"

        else:
            rule_risk = "High"

    # =========================================================
    # NORMALIZE ML PREDICTION
    # =========================================================

    if ml_prediction:
        ml_prediction = str(ml_prediction).strip().capitalize()
    else:
        ml_prediction = "Low"

    # Make sure unexpected ML values do not break the system
    if ml_prediction not in risk_values:
        ml_prediction = "Low"

    # =========================================================
    # CONVERT TO NUMBERS
    # =========================================================

    rule_value = risk_values.get(rule_risk, 1)
    ml_value = risk_values.get(ml_prediction, 1)

    # =========================================================
    # HYBRID DECISION
    # =========================================================
    #
    # Always select the HIGHER risk.
    #
    # Example:
    #
    # Rule = Medium
    # ML   = Low
    #
    # Final = Medium
    #
    # =========================================================

    final_value = max(rule_value, ml_value)

    if final_value == 3:

        final_risk = "High"
        final_decision = "Human Approval"

    elif final_value == 2:

        final_risk = "Medium"
        final_decision = "User Confirmation"

    else:

        final_risk = "Low"
        final_decision = "Autonomous Execution"

    # =========================================================
    # EXPLANATION
    # =========================================================

    if rule_risk == ml_prediction:

        agreement = (
            f"Rule engine and ML model agree: {rule_risk}."
        )

    else:

        agreement = (
            f"Rule engine predicted {rule_risk}, "
            f"while ML predicted {ml_prediction}. "
            f"TrustGuard selected the higher risk level for safety."
        )

    # =========================================================
    # FINAL RESULT
    # =========================================================

    return {
        "final_risk_level": final_risk,
        "final_decision": final_decision,
        "rule_risk": rule_risk,
        "ml_prediction": ml_prediction,
        "agreement": agreement
    }