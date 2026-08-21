import streamlit as st
import re
import csv
import io


# ==================================================
# PAGE SETTINGS
# ==================================================

st.set_page_config(
    page_title="TrustGuard",
    page_icon="🛡️",
    layout="wide"
)


# ==================================================
# SESSION STATE
# ==================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def normalize(text):
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def contains(text, *words):
    return any(word in text for word in words)


def extract_amount(text):
    match = re.search(r"₹\s*([\d,]+)", text)

    if match:
        return int(match.group(1).replace(",", ""))

    return None


def raise_scores(scores, order, target):
    scores = list(scores)

    while sum(scores) < target:

        changed = False

        for index in order:

            if scores[index] < 5:
                scores[index] += 1
                changed = True

                if sum(scores) >= target:
                    break

        if not changed:
            break

    return scores


# ==================================================
# AUTOMATIC RISK ANALYZER
# ==================================================

def analyze_action(action):

    text = normalize(action)

    privacy = 0
    financial = 0
    data = 0
    irreversible = 0
    external = 0

    reasons = []

    # ------------------------------------------------
    # CONTEXT DETECTION
    # ------------------------------------------------

    safe_draft = (
        "draft" in text
        and contains(
            text,
            "without sending",
            "without posting",
            "without saving"
        )
    )

    nonimportant = contains(
        text,
        "non-important",
        "non important"
    )

    public_or_unknown = contains(
        text,
        "publicly",
        "public website",
        "public platform",
        "unknown",
        "external application",
        "third-party",
        "another person",
        "unknown recipient",
        "unknown email",
        "unknown merchant"
    )

    sensitive = contains(
        text,
        "otp",
        "aadhaar",
        "cvv",
        "credit card",
        "login credentials",
        "password",
        "medical",
        "tax documents",
        "identity",
        "confidential",
        "private",
        "banking data",
        "payment-card",
        "payment card",
        "academic records",
        "organizational records",
        "company files",
        "research data"
    )

    security_change = contains(
        text,
        "disable two-factor",
        "administrator access",
        "administrator permission",
        "security restrictions",
        "security permissions",
        "recovery settings",
        "recovery email",
        "phone number linked to",
        "full cloud storage access"
    )

    destructive = contains(
        text,
        "delete",
        "erase",
        "remove"
    )

    consequential_target = (
        not nonimportant
        and contains(
            text,
            "important",
            "entire",
            "all files",
            "shared cloud",
            "shared team",
            "database records",
            "backup",
            "email account",
            "user account"
        )
    )

    amount = extract_amount(text)

    high_money = (
        (amount is not None and amount >= 10000)
        or contains(
            text,
            "high-value",
            "high value",
            "large payment"
        )
    )

    bank_context = contains(
        text,
        "bank",
        "banking",
        "payment-card",
        "credit card",
        "payment details"
    )

    money_action = contains(
        text,
        "transfer",
        "purchase",
        "payment"
    )


    # ==================================================
    # PRIVACY RISK
    # ==================================================

    if sensitive:
        privacy = 5
        reasons.append("Sensitive or private information detected.")

    elif contains(
        text,
        "resume",
        "phone",
        "contact",
        "profile photo",
        "personal"
    ):
        privacy = 2

    elif "email" in text:
        privacy = 1

    if safe_draft:
        privacy = min(privacy, 1)
        reasons.append(
            "Draft-only action detected; no external execution occurs."
        )


    # ==================================================
    # FINANCIAL RISK
    # ==================================================

    if (
        (bank_context and money_action)
        or high_money
        or contains(
            text,
            "bank details",
            "banking otp",
            "banking data"
        )
    ):
        financial = 5
        reasons.append("High financial or banking impact detected.")

    elif contains(
        text,
        "purchase",
        "buy",
        "payment",
        "recharge",
        "subscribe",
        "ticket",
        "order"
    ):
        financial = 3
        reasons.append("Financial transaction detected.")


    # ==================================================
    # DATA MODIFICATION RISK
    # ==================================================

    if destructive:

        if consequential_target or "permanently" in text:
            data = 5
            reasons.append(
                "Destructive modification of important data detected."
            )

        else:
            data = 3

    elif security_change:
        data = 5
        reasons.append("Security configuration change detected.")

    elif contains(
        text,
        "change password",
        "change the password"
    ):
        data = 5

    elif contains(
        text,
        "edit",
        "change",
        "update",
        "upload",
        "submit",
        "install",
        "archive",
        "reschedule",
        "cancel",
        "add a new",
        "invite"
    ):
        data = 3

    elif contains(
        text,
        "create",
        "add a note",
        "set a personal alarm"
    ):
        data = 1


    # ==================================================
    # IRREVERSIBILITY RISK
    # ==================================================

    if (
        contains(
            text,
            "permanently",
            "transfer",
            "publish"
        )
        or (destructive and consequential_target)
    ):
        irreversible = 5
        reasons.append(
            "Action may be difficult or impossible to reverse."
        )

    elif contains(
        text,
        "send",
        "share",
        "submit",
        "post",
        "approve",
        "purchase",
        "buy",
        "book",
        "subscribe",
        "recharge"
    ):
        irreversible = 4

    elif contains(
        text,
        "upload",
        "change",
        "edit",
        "update",
        "reschedule",
        "cancel",
        "archive",
        "invite",
        "add a new",
        "install",
        "disable"
    ):
        irreversible = 2

    if safe_draft:
        irreversible = 0


    # ==================================================
    # EXTERNAL IMPACT
    # ==================================================

    if public_or_unknown:
        external = 5
        reasons.append(
            "Action affects an unknown, external, or public target."
        )

    elif contains(
        text,
        "send",
        "share",
        "post",
        "upload",
        "submit",
        "professor",
        "teacher",
        "classmate",
        "shared",
        "portal",
        "social media",
        "website",
        "meeting invitation",
        "class group",
        "calendar event",
        "delivery",
        "online service",
        "online purchase",
        "movie ticket",
        "mobile recharge"
    ):
        external = 4

    elif contains(
        text,
        "account",
        "application",
        "order"
    ):
        external = 2

    if safe_draft:
        external = 0


    # ==================================================
    # HIGH-RISK GUARDRAIL
    # ==================================================

    high_condition = (

        (
            sensitive
            and (
                public_or_unknown
                or contains(
                    text,
                    "send",
                    "share",
                    "submit",
                    "publish"
                )
            )
        )

        or (
            bank_context
            and (
                money_action
                or security_change
                or contains(
                    text,
                    "password",
                    "otp",
                    "phone number",
                    "access"
                )
            )
        )

        or high_money

        or (
            destructive
            and (
                consequential_target
                or "permanently" in text
            )
        )

        or security_change

        or (
            "unknown application" in text
            and contains(
                text,
                "install",
                "access",
                "administrator"
            )
        )
    )


    if high_condition:

        reasons.append(
            "TrustGuard high-risk safety guardrail activated."
        )

        if sensitive:
            privacy = max(privacy, 5)

        if bank_context or high_money:
            financial = max(financial, 5)

        if (
            destructive
            or security_change
            or contains(
                text,
                "change",
                "install",
                "access"
            )
        ):
            data = max(data, 4)

        if contains(
            text,
            "send",
            "share",
            "submit",
            "publish",
            "transfer",
            "delete",
            "erase",
            "remove",
            "disable",
            "change",
            "install",
            "approve",
            "purchase",
            "payment"
        ):
            irreversible = max(
                irreversible,
                4
            )

        if public_or_unknown:
            external = max(external, 5)

        else:
            external = max(external, 3)

        scores = raise_scores(
            [
                privacy,
                financial,
                data,
                irreversible,
                external
            ],
            [0, 2, 3, 4, 1],
            17
        )

        (
            privacy,
            financial,
            data,
            irreversible,
            external
        ) = scores


    # ==================================================
    # MEDIUM-RISK GUARDRAIL
    # ==================================================

    medium_condition = (
        not safe_draft
        and (
            contains(
                text,
                "send",
                "share",
                "post",
                "upload",
                "submit",
                "invite",
                "reschedule",
                "cancel"
            )

            or contains(
                text,
                "shared",
                "professor",
                "teacher",
                "classmate",
                "portal",
                "social media",
                "public website"
            )

            or contains(
                text,
                "low-cost",
                "recharge",
                "movie ticket",
                "subscribe"
            )

            or (
                contains(
                    text,
                    "purchase",
                    "buy"
                )
                and not high_money
            )

            or (
                destructive
                and nonimportant
            )

            or contains(
                text,
                "edit",
                "change",
                "update",
                "archive",
                "add a new contact",
                "profile photo",
                "display name",
                "username",
                "notification settings",
                "delivery preference",
                "delivery instruction",
                "delivery address"
            )
        )
    )


    if medium_condition and not high_condition:

        reasons.append(
            "TrustGuard medium-risk oversight rule activated."
        )

        if contains(
            text,
            "send",
            "share",
            "post",
            "upload",
            "submit",
            "invite",
            "shared",
            "portal",
            "social media",
            "public website"
        ):
            external = max(external, 4)
            irreversible = max(irreversible, 3)

        if contains(
            text,
            "edit",
            "change",
            "update",
            "archive",
            "reschedule",
            "cancel",
            "add a new",
            "profile photo",
            "display name",
            "username",
            "notification",
            "delete"
        ):
            data = max(data, 3)
            irreversible = max(irreversible, 2)

        if contains(
            text,
            "purchase",
            "buy",
            "recharge",
            "ticket",
            "subscribe",
            "order"
        ):
            financial = max(financial, 3)
            irreversible = max(irreversible, 3)
            external = max(external, 3)

        scores = raise_scores(
            [
                privacy,
                financial,
                data,
                irreversible,
                external
            ],
            [4, 3, 2, 0, 1],
            9
        )

        (
            privacy,
            financial,
            data,
            irreversible,
            external
        ) = scores


    # ==================================================
    # FINAL SCORE
    # ==================================================

    total = (
        privacy
        + financial
        + data
        + irreversible
        + external
    )

    if total <= 8:
        level = "Low"
        decision = "Autonomous Execution"
        status = "Automatically Approved"

    elif total <= 16:
        level = "Medium"
        decision = "User Confirmation Required"
        status = "Waiting for User Confirmation"

    else:
        level = "High"
        decision = "Human Approval Required"
        status = "Waiting for Human Approval"

    return {
        "Privacy Risk": privacy,
        "Financial Risk": financial,
        "Data Modification Risk": data,
        "Irreversibility Risk": irreversible,
        "External Impact": external,
        "Total Score": total,
        "Risk Level": level,
        "Decision": decision,
        "Status": status,
        "Reasons": reasons
    }


# ==================================================
# CATEGORY DETECTION
# ==================================================

def detect_category(text):

    text = normalize(text)

    if contains(
        text,
        "bank",
        "payment",
        "transfer",
        "purchase",
        "money",
        "₹"
    ):
        return "Financial / Banking"

    if contains(
        text,
        "password",
        "otp",
        "security",
        "administrator",
        "two-factor"
    ):
        return "Security"

    if contains(
        text,
        "private",
        "medical",
        "confidential",
        "aadhaar",
        "identity"
    ):
        return "Privacy / Sensitive Data"

    if contains(
        text,
        "send",
        "share",
        "email",
        "post",
        "publish"
    ):
        return "Communication"

    if contains(
        text,
        "delete",
        "edit",
        "upload",
        "file",
        "folder"
    ):
        return "Data / File Management"

    return "General"


# ==================================================
# HEADER
# ==================================================

st.title("🛡️ TrustGuard")

st.subheader(
    "Risk-Aware Human Oversight Framework for AI Agent Actions"
)

st.write(
    "TrustGuard automatically analyzes a proposed AI-agent action "
    "using five risk factors and determines the appropriate level "
    "of human oversight."
)

st.info(
    "Each risk factor is scored automatically from 0 to 5. "
    "Maximum total risk score = 25."
)

st.divider()


# ==================================================
# ACTION INPUT
# ==================================================

st.header("🤖 AI Agent Action")

action = st.text_area(
    "Enter the action proposed by the AI agent:",
    placeholder="Example: Transfer ₹15,000 to a new bank account",
    height=100
)

if st.button(
    "🛡️ Analyze Action",
    type="primary",
    use_container_width=True
):

    if not action.strip():

        st.warning(
            "Please enter an AI Agent Action."
        )

    else:

        result = analyze_action(action)

        result["Action"] = action
        result["Category"] = detect_category(action)

        st.session_state.last_result = result

        log_result = {
            "Action": action,
            "Category": result["Category"],
            "Privacy": result["Privacy Risk"],
            "Financial": result["Financial Risk"],
            "Data Modification":
                result["Data Modification Risk"],
            "Irreversibility":
                result["Irreversibility Risk"],
            "External Impact":
                result["External Impact"],
            "Total Score":
                result["Total Score"],
            "Risk Level":
                result["Risk Level"],
            "Decision":
                result["Decision"],
            "Status":
                result["Status"]
        }

        st.session_state.history.append(
            log_result
        )


# ==================================================
# CURRENT RESULT
# ==================================================

if st.session_state.last_result:

    result = st.session_state.last_result

    st.divider()

    st.header(
        "🔍 Automatic Risk Assessment"
    )

    st.write(
        "**Detected Category:**",
        result["Category"]
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "Privacy Risk",
            f'{result["Privacy Risk"]} / 5'
        )

    with c2:
        st.metric(
            "Financial Risk",
            f'{result["Financial Risk"]} / 5'
        )

    with c3:
        st.metric(
            "Data Modification",
            f'{result["Data Modification Risk"]} / 5'
        )

    with c4:
        st.metric(
            "Irreversibility",
            f'{result["Irreversibility Risk"]} / 5'
        )

    with c5:
        st.metric(
            "External Impact",
            f'{result["External Impact"]} / 5'
        )


    # ==================================================
    # DECISION
    # ==================================================

    st.divider()

    st.header("🛡️ TrustGuard Decision")

    d1, d2, d3 = st.columns(3)

    with d1:
        st.metric(
            "Total Risk Score",
            f'{result["Total Score"]} / 25'
        )

    with d2:
        st.metric(
            "Risk Level",
            result["Risk Level"]
        )

    with d3:
        st.write("**Decision**")
        st.write(result["Decision"])


    if result["Risk Level"] == "Low":

        st.success(
            "✅ LOW RISK — Autonomous execution is permitted."
        )

    elif result["Risk Level"] == "Medium":

        st.warning(
            "⚠️ MEDIUM RISK — User confirmation is required."
        )

    else:

        st.error(
            "🚨 HIGH RISK — Human approval is required."
        )


    # ==================================================
    # HUMAN OVERSIGHT
    # ==================================================

    if result["Risk Level"] in [
        "Medium",
        "High"
    ]:

        st.subheader("👤 Human Oversight")

        approve_col, reject_col = st.columns(2)

        with approve_col:

            if st.button(
                "✅ Approve Action",
                use_container_width=True
            ):

                result["Status"] = "Approved"

                if st.session_state.history:
                    st.session_state.history[-1][
                        "Status"
                    ] = "Approved"

                st.success(
                    "Action approved."
                )

        with reject_col:

            if st.button(
                "❌ Reject Action",
                use_container_width=True
            ):

                result["Status"] = "Rejected"

                if st.session_state.history:
                    st.session_state.history[-1][
                        "Status"
                    ] = "Rejected"

                st.error(
                    "Action rejected."
                )


    # ==================================================
    # EXPLAINABILITY
    # ==================================================

    with st.expander(
        "🔎 Why did TrustGuard make this decision?"
    ):

        if result["Reasons"]:

            for reason in result["Reasons"]:
                st.write("•", reason)

        else:
            st.write(
                "No significant risk indicators were detected."
            )

        st.write(
            "**Final score:**",
            result["Total Score"],
            "/ 25"
        )


# ==================================================
# DASHBOARD
# ==================================================

st.divider()

st.header("📊 TrustGuard Dashboard")

total_actions = len(
    st.session_state.history
)

low_count = sum(
    1 for x in st.session_state.history
    if x["Risk Level"] == "Low"
)

medium_count = sum(
    1 for x in st.session_state.history
    if x["Risk Level"] == "Medium"
)

high_count = sum(
    1 for x in st.session_state.history
    if x["Risk Level"] == "High"
)

a, b, c, d = st.columns(4)

with a:
    st.metric(
        "Total Actions",
        total_actions
    )

with b:
    st.metric(
        "Low Risk",
        low_count
    )

with c:
    st.metric(
        "Medium Risk",
        medium_count
    )

with d:
    st.metric(
        "High Risk",
        high_count
    )


# ==================================================
# ACTION LOG
# ==================================================

st.divider()

st.header("📜 Action Log")

if st.session_state.history:

    st.dataframe(
        st.session_state.history,
        use_container_width=True
    )

    output = io.StringIO()

    fields = [
        "Action",
        "Category",
        "Privacy",
        "Financial",
        "Data Modification",
        "Irreversibility",
        "External Impact",
        "Total Score",
        "Risk Level",
        "Decision",
        "Status"
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fields
    )

    writer.writeheader()

    for row in st.session_state.history:
        writer.writerow(row)

    st.download_button(
        "⬇️ Download Action Log",
        data=output.getvalue(),
        file_name="TrustGuard_Action_Log.csv",
        mime="text/csv"
    )

    if st.button(
        "🗑️ Clear Action Log"
    ):

        st.session_state.history = []
        st.session_state.last_result = None
        st.rerun()

else:

    st.info(
        "No actions have been analyzed yet."
    )


# ==================================================
# SCORING INFORMATION
# ==================================================

st.divider()

with st.expander(
    "ℹ️ TrustGuard Risk Scoring"
):

    st.write("""
**Each factor: 0–5**

- **0** = No Risk
- **1** = Very Low Risk
- **2** = Low Risk
- **3** = Medium Risk
- **4** = High Risk
- **5** = Very High Risk

**Final Risk Score:**

- **0–8 → Low Risk**
- **9–16 → Medium Risk**
- **17–25 → High Risk**
""")


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "TrustGuard Prototype — Automatic Five-Factor "
    "Risk-Based Human Oversight Framework"
)