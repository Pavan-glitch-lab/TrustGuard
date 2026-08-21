# TrustGuard Hybrid Decision Engine
# Combines rule-based analysis with AI/ML prediction.

def calculate_hybrid_decision(rule_result, ml_prediction):

    rule_risk = rule_result["risk_level"]

    # Convert risk levels to numerical values
    risk_values = {
        "Low": 1,
        "Medium": 2,
        "High": 3
    }

    rule_value = risk_values.get(rule_risk, 1)
    ml_value = risk_values.get(ml_prediction, 1)

    # Conservative hybrid approach:
    # If ML detects a higher risk than the rule engine,
    # TrustGuard uses the higher risk level.
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

    # Explain disagreement between systems
    if rule_risk == ml_prediction:
        agreement = "Rule engine and ML model agree."

    else:
        agreement = (
            f"Rule engine predicted {rule_risk}, "
            f"while ML predicted {ml_prediction}. "
            "TrustGuard selected the higher risk level for safety."
        )

    return {
        "final_risk_level": final_risk,
        "final_decision": final_decision,
        "rule_risk": rule_risk,
        "ml_prediction": ml_prediction,
        "agreement": agreement
    }