/* ============================================================
   TRUSTGUARD FRONTEND
   Authentication + Google Login + Analyzer + History + Logout
============================================================ */

"use strict";


/* ============================================================
   GLOBAL STATE
============================================================ */

let currentAnalysis = null;


/* ============================================================
   SAFE JSON FETCH
   Prevents:
   Unexpected token '<', "<!doctype..." is not valid JSON
============================================================ */

async function apiFetch(url, options = {}) {

    const defaultOptions = {
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json"
        }
    };

    const response = await fetch(
        url,
        {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        }
    );

    const contentType =
        response.headers.get("content-type") || "";

    const text = await response.text();

    let data = null;

    if (contentType.includes("application/json")) {

        try {
            data = JSON.parse(text);
        } catch (error) {

            throw new Error(
                "Server returned invalid JSON."
            );
        }

    } else {

        /*
         * This is the important protection against:
         *
         * Unexpected token '<'
         *
         * If Flask returns an HTML error page, we don't
         * try to JSON.parse() it.
         */

        throw new Error(
            `Server returned HTML/non-JSON response (${response.status}).`
        );
    }

    if (!response.ok) {

        throw new Error(
            data?.error ||
            data?.message ||
            `Request failed (${response.status})`
        );
    }

    return data;
}


/* ============================================================
   DOM READY
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    async function () {

        console.log(
            "TrustGuard frontend loaded."
        );

        await checkAuthentication();

        await loadHistory();

        setupNavigation();

        setupProfileMenu();

    }
);


/* ============================================================
   AUTHENTICATION
============================================================ */

async function checkAuthentication() {

    try {

        const data =
            await apiFetch(
                "/api/me",
                {
                    method: "GET",
                    headers: {}
                }
            );


        if (
            !data ||
            data.authenticated !== true
        ) {

            console.warn(
                "User is not authenticated."
            );

            /*
             * If the current page is the dashboard,
             * return to login.
             */

            if (
                window.location.pathname.includes(
                    "index.html"
                )
            ) {

                window.location.href =
                    "/login.html";

                return false;
            }

            return false;
        }


        const user =
            data.user || {};


        updateUserProfile(
            user
        );


        console.log(
            "Authenticated user:",
            user
        );


        return true;

    } catch (error) {

        console.error(
            "Authentication check failed:",
            error
        );

        /*
         * Do not immediately redirect on a temporary
         * frontend/server problem.
         */

        const currentUser =
            document.getElementById(
                "currentUser"
            );

        if (currentUser) {

            currentUser.textContent =
                "User";
        }

        return false;
    }
}


/* ============================================================
   UPDATE PROFILE
============================================================ */

function updateUserProfile(user) {

    const name =
        user.full_name ||
        user.name ||
        "User";

    const email =
        user.email ||
        "";


    const currentUser =
        document.getElementById(
            "currentUser"
        );

    const avatar =
        document.getElementById(
            "userAvatar"
        );


    if (currentUser) {

        currentUser.textContent =
            name;
    }


    if (avatar) {

        const initials =
            name
                .split(/\s+/)
                .filter(Boolean)
                .slice(0, 2)
                .map(
                    word =>
                        word
                            .charAt(0)
                            .toUpperCase()
                )
                .join("");


        avatar.textContent =
            initials || "U";
    }


    /*
     * Save user information for the profile popup.
     */

    window.trustGuardUser = {
        id: user.id || "",
        full_name: name,
        email: email,
        login_method:
            user.login_method || "password"
    };
}


/* ============================================================
   PROFILE MENU
============================================================ */

function setupProfileMenu() {

    const userMenu =
        document.querySelector(
            ".user-menu"
        );

    if (!userMenu) {
        return;
    }


    /*
     * Prevent the logout button from opening
     * the profile popup.
     */

    const logoutButton =
        userMenu.querySelector(
            ".logout-btn"
        );


    userMenu.addEventListener(
        "click",
        function (event) {

            if (
                logoutButton &&
                (
                    event.target === logoutButton ||
                    logoutButton.contains(
                        event.target
                    )
                )
            ) {

                return;
            }


            showProfile();
        }
    );
}


/* ============================================================
   PROFILE DISPLAY
============================================================ */

function showProfile() {

    const user =
        window.trustGuardUser;


    if (!user) {

        alert(
            "Profile information is still loading."
        );

        return;
    }


    const name =
        user.full_name ||
        "User";

    const email =
        user.email ||
        "Not available";

    const method =
        user.login_method === "google"
            ? "Google"
            : "Password";


    alert(
        "TRUSTGUARD PROFILE\n\n" +
        "Name: " +
        name +
        "\n" +
        "Email: " +
        email +
        "\n" +
        "Login method: " +
        method
    );
}


/* ============================================================
   LOGOUT
============================================================ */

async function logout() {

    try {

        const data =
            await apiFetch(
                "/api/logout",
                {
                    method: "POST",
                    body: JSON.stringify({})
                }
            );


        console.log(
            "Logout:",
            data
        );


        window.trustGuardUser =
            null;


        /*
         * Always return to login after successful logout.
         */

        window.location.href =
            "/login.html";


    } catch (error) {

        console.error(
            "Logout error:",
            error
        );

        alert(
            "Logout failed: " +
            error.message
        );
    }
}


/* ============================================================
   ANALYZE ACTION
============================================================ */

async function analyzeAction() {

    const input =
        document.getElementById(
            "actionInput"
        );

    const button =
        document.getElementById(
            "analyzeBtn"
        );

    const result =
        document.getElementById(
            "result"
        );


    if (!input || !button || !result) {

        console.error(
            "Analyzer elements not found."
        );

        return;
    }


    const action =
        input.value.trim();


    if (!action) {

        alert(
            "Please describe the AI action first."
        );

        input.focus();

        return;
    }


    /*
     * Reset UI.
     */

    result.classList.add(
        "hidden"
    );


    hideApprovalPanels();


    button.disabled = true;

    button.textContent =
        "Analyzing...";


    try {

        console.log(
            "Sending action to backend:",
            action
        );


        const data =
            await apiFetch(
                "/analyze",
                {
                    method: "POST",
                    body: JSON.stringify({
                        action: action
                    })
                }
            );


        console.log(
            "Analysis response:",
            data
        );


        currentAnalysis = data;


        displayAnalysis(
            data
        );


        /*
         * Save every analysis to history.
         * Human decision will be updated separately
         * for medium/high-risk actions.
         */

        await saveAnalysisToHistory(
            data,
            ""
        );


    } catch (error) {

        console.error(
            "Analysis failed:",
            error
        );


        result.classList.remove(
            "hidden"
        );


        const riskLevel =
            document.getElementById(
                "riskLevel"
            );

        const decision =
            document.getElementById(
                "decision"
            );

        const explanationList =
            document.getElementById(
                "explanationList"
            );


        if (riskLevel) {

            riskLevel.textContent =
                "ERROR";
        }


        if (decision) {

            decision.textContent =
                "FAILED";
        }


        if (explanationList) {

            explanationList.innerHTML =
                `<li>${escapeHtml(
                    error.message
                )}</li>`;
        }


        alert(
            "Analysis failed:\n\n" +
            error.message
        );


    } finally {

        /*
         * IMPORTANT:
         * This guarantees the button NEVER remains
         * stuck on "Analyzing..."
         */

        button.disabled = false;

        button.textContent =
            "Analyze Risk";
    }
}


/* ============================================================
   DISPLAY ANALYSIS
============================================================ */

function displayAnalysis(data) {

    const result =
        document.getElementById(
            "result"
        );

    const riskLevel =
        document.getElementById(
            "riskLevel"
        );

    const decision =
        document.getElementById(
            "decision"
        );

    const mlPrediction =
        document.getElementById(
            "mlPrediction"
        );

    const riskScore =
        document.getElementById(
            "riskScore"
        );

    const explanationList =
        document.getElementById(
            "explanationList"
        );

    const hybridAgreement =
        document.getElementById(
            "hybridAgreement"
        );


    if (result) {

        result.classList.remove(
            "hidden"
        );
    }


    const finalRisk =
        data.risk_level ||
        data.final_risk_level ||
        "UNKNOWN";


    const finalDecision =
        data.decision ||
        data.final_decision ||
        "UNKNOWN";


    const ml =
        data.ml_prediction ??
        "N/A";


    const score =
        data.total_score ??
        data.risk_score ??
        0;


    if (riskLevel) {

        riskLevel.textContent =
            String(
                finalRisk
            ).toUpperCase();
    }


    if (decision) {

        decision.textContent =
            formatDecision(
                finalDecision
            );
    }


    if (mlPrediction) {

        if (
            typeof ml === "object"
        ) {

            mlPrediction.textContent =
                ml.risk_level ||
                ml.prediction ||
                ml.label ||
                "N/A";

        } else {

            mlPrediction.textContent =
                String(ml);
        }
    }


    if (riskScore) {

        riskScore.textContent =
            String(score);
    }


    /*
     * Explanation
     */

    if (explanationList) {

        explanationList.innerHTML =
            "";


        let explanations =
            data.explanation ||
            data.risk_factors ||
            [];


        if (!Array.isArray(
            explanations
        )) {

            explanations =
                [String(
                    explanations
                )];
        }


        if (
            explanations.length === 0
        ) {

            explanations = [
                "TrustGuard completed the risk evaluation."
            ];
        }


        explanations.forEach(
            item => {

                const li =
                    document.createElement(
                        "li"
                    );

                li.textContent =
                    typeof item === "string"
                        ? item
                        : JSON.stringify(item);

                explanationList.appendChild(
                    li
                );
            }
        );
    }


    /*
     * Hybrid analysis
     */

    if (hybridAgreement) {

        const hybrid =
            data.hybrid_analysis ||
            {};


        hybridAgreement.textContent =
            hybrid.agreement ||
            hybrid.message ||
            hybrid.final_decision ||
            "Hybrid engine completed the safety evaluation.";
    }


    /*
     * Show correct interaction panel.
     */

    showRiskInteraction(
        finalRisk,
        finalDecision
    );


    /*
     * Scroll result into view.
     */

    if (result) {

        setTimeout(
            () => {

                result.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest"
                });

            },
            100
        );
    }
}


/* ============================================================
   RISK INTERACTION
============================================================ */

function showRiskInteraction(
    risk,
    decision
) {

    hideApprovalPanels();


    const normalizedRisk =
        String(
            risk || ""
        ).toLowerCase();


    const normalizedDecision =
        String(
            decision || ""
        ).toLowerCase();


    /*
     * HIGH RISK
     */

    if (
        normalizedRisk.includes(
            "high"
        ) ||
        normalizedDecision.includes(
            "approval"
        ) ||
        normalizedDecision.includes(
            "block"
        )
    ) {

        const panel =
            document.getElementById(
                "approvalPanel"
            );

        if (panel) {

            panel.classList.remove(
                "hidden"
            );
        }


        return;
    }


    /*
     * MEDIUM RISK
     */

    if (
        normalizedRisk.includes(
            "medium"
        ) ||
        normalizedDecision.includes(
            "confirm"
        )
    ) {

        const panel =
            document.getElementById(
                "confirmationPanel"
            );

        if (panel) {

            panel.classList.remove(
                "hidden"
            );
        }


        return;
    }


    /*
     * LOW RISK
     */

    console.log(
        "Low-risk action can proceed automatically."
    );
}


/* ============================================================
   HIDE APPROVAL PANELS
============================================================ */

function hideApprovalPanels() {

    const approval =
        document.getElementById(
            "approvalPanel"
        );

    const confirmation =
        document.getElementById(
            "confirmationPanel"
        );


    if (approval) {

        approval.classList.add(
            "hidden"
        );
    }


    if (confirmation) {

        confirmation.classList.add(
            "hidden"
        );
    }


    const approvalStatus =
        document.getElementById(
            "approvalStatus"
        );

    const confirmationStatus =
        document.getElementById(
            "confirmationStatus"
        );


    if (approvalStatus) {

        approvalStatus.textContent =
            "";
    }


    if (confirmationStatus) {

        confirmationStatus.textContent =
            "";
    }
}


/* ============================================================
   HIGH-RISK APPROVAL
============================================================ */

async function approveAction() {
    console.log("Approve button clicked.");

    if (!currentAnalysis) {
        alert("Please analyze an action first.");
        return;
    }

    const status = document.getElementById("approvalStatus");
    const button = document.getElementById("approveBtn");

    console.log("Current analysis:", currentAnalysis);

    if (button) {
        button.disabled = true;
        button.textContent = "Approving...";
    }

    try {
        const data = await saveApprovalDecision("APPROVED");

        console.log("Approval saved successfully:", data);

        if (status) {
            status.textContent = "✓ Action approved by human reviewer.";
            status.style.color = "#059669";
        }

        disableApprovalButtons();

    } catch (error) {
        console.error("APPROVAL ERROR:", error);

        if (status) {
            status.textContent =
                "Approval failed: " + error.message;
            status.style.color = "#dc2626";
        }

        alert(
            "Approval failed.\n\n" +
            error.message
        );

    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = "✓ Approve Action";
        }
    }
}


/* ============================================================
   HIGH-RISK REJECTION
============================================================ */

async function rejectAction(event) {

    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    console.log("Reject button clicked.");

    if (!currentAnalysis) {
        alert("Please analyze an action first.");
        return;
    }

    const status = document.getElementById("approvalStatus");
    const button = document.getElementById("rejectBtn");

    console.log("Current analysis:", currentAnalysis);

    if (button) {
        button.disabled = true;
        button.textContent = "Rejecting...";
    }

    try {

        const data = await saveApprovalDecision("REJECTED");

        console.log("Rejection saved successfully:", data);

        if (status) {
            status.textContent =
                "✕ Action rejected by human reviewer.";
            status.style.color = "#dc2626";
        }

        disableApprovalButtons();

        /*
         * Reload history so the REJECTED decision
         * immediately appears in Approval History.
         */
        await loadHistory();

    } catch (error) {

        console.error("REJECTION ERROR:", error);

        if (status) {
            status.textContent =
                "Rejection failed: " + error.message;

            status.style.color = "#dc2626";
        }

        alert(
            "Rejection failed.\n\n" +
            error.message
        );

    } finally {

        if (button) {
            button.disabled = false;
            button.textContent = "✕ Reject Action";
        }
    }
}


/* ============================================================
   MEDIUM-RISK CONFIRM
============================================================ */

async function confirmAction() {

    if (!currentAnalysis) {

        alert(
            "Please analyze an action first."
        );

        return;
    }


    const status =
        document.getElementById(
            "confirmationStatus"
        );


    const button =
        document.getElementById(
            "confirmBtn"
        );


    if (button) {

        button.disabled = true;
    }


    try {

        await saveApprovalDecision(
            "APPROVED"
        );


        if (status) {

            status.textContent =
                "✓ Action confirmed.";

            status.style.color =
                "#059669";
        }


        disableConfirmationButtons();


    } catch (error) {

        console.error(
            error
        );


        if (status) {

            status.textContent =
                "Confirmation failed: " +
                error.message;

            status.style.color =
                "#dc2626";
        }

    } finally {

        if (button) {

            button.disabled = false;
        }
    }
}


/* ============================================================
   MEDIUM-RISK CANCEL
============================================================ */

async function cancelAction() {

    if (!currentAnalysis) {

        alert(
            "Please analyze an action first."
        );

        return;
    }


    const status =
        document.getElementById(
            "confirmationStatus"
        );


    const button =
        document.getElementById(
            "cancelBtn"
        );


    if (button) {

        button.disabled = true;
    }


    try {

        await saveApprovalDecision(
            "CANCELLED"
        );


        if (status) {

            status.textContent =
                "✕ Action cancelled.";

            status.style.color =
                "#dc2626";
        }


        disableConfirmationButtons();


    } catch (error) {

        console.error(
            error
        );


        if (status) {

            status.textContent =
                "Cancellation failed: " +
                error.message;

            status.style.color =
                "#dc2626";
        }

    } finally {

        if (button) {

            button.disabled = false;
        }
    }
}


/* ============================================================
   SAVE HUMAN DECISION
============================================================ */

async function saveApprovalDecision(
    humanDecision
) {

    const data =
        await apiFetch(
            "/approval-history",
            {
                method: "POST",

                body: JSON.stringify({

                    action:
                        currentAnalysis.action,

                    risk:
                        currentAnalysis.risk_level,

                    decision:
                        currentAnalysis.decision,

                    ml_prediction:
                        getMLPredictionText(
                            currentAnalysis.ml_prediction
                        ),

                    human_decision:
                        humanDecision
                })
            }
        );


    await loadHistory();


    return data;
}


/* ============================================================
   SAVE INITIAL ANALYSIS
============================================================ */

async function saveAnalysisToHistory(
    data,
    humanDecision
) {

    try {

        await apiFetch(
            "/approval-history",
            {
                method: "POST",

                body: JSON.stringify({

                    action:
                        data.action,

                    risk:
                        data.risk_level,

                    decision:
                        data.decision,

                    ml_prediction:
                        getMLPredictionText(
                            data.ml_prediction
                        ),

                    human_decision:
                        humanDecision
                })
            }
        );


        await loadHistory();

    } catch (error) {

        console.warn(
            "Could not save analysis history:",
            error
        );
    }
}


/* ============================================================
   ML TEXT
============================================================ */

function getMLPredictionText(
    prediction
) {

    if (
        prediction === null ||
        prediction === undefined
    ) {

        return "";
    }


    if (
        typeof prediction === "string"
    ) {

        return prediction;
    }


    if (
        typeof prediction === "number"
    ) {

        return String(
            prediction
        );
    }


    return (
        prediction.risk_level ||
        prediction.prediction ||
        prediction.label ||
        prediction.class ||
        JSON.stringify(
            prediction
        )
    );
}


/* ============================================================
   HISTORY
============================================================ */

async function loadHistory() {

    const container =
        document.getElementById(
            "historyContainer"
        );


    if (!container) {

        return;
    }


    try {

        const data =
            await apiFetch(
                "/approval-history",
                {
                    method: "GET",
                    headers: {}
                }
            );


        const history =
            Array.isArray(
                data.history
            )
                ? data.history
                : [];


        renderHistory(
            history
        );


        updateStatistics(
            history
        );


    } catch (error) {

        console.error(
            "History loading failed:",
            error
        );


        container.innerHTML =
            `<div class="empty-history">
                Unable to load history.
                <br>
                ${escapeHtml(
                    error.message
                )}
            </div>`;
    }
}


/* ============================================================
   RENDER HISTORY
============================================================ */

function renderHistory(
    history
) {

    const container =
        document.getElementById(
            "historyContainer"
        );


    if (!container) {

        return;
    }


    if (
        history.length === 0
    ) {

        container.innerHTML =
            `<div class="empty-history">
                No decisions recorded yet.
            </div>`;

        return;
    }


    /*
     * Newest first.
     */

    const sorted =
        [...history].reverse();


    container.innerHTML =
        "";


    sorted.forEach(
        item => {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "history-item";


            const risk =
                String(
                    item.risk ||
                    "UNKNOWN"
                ).toUpperCase();


            const decision =
                formatDecision(
                    item.decision ||
                    "-"
                );


            const humanDecision =
                item.human_decision ||
                "ANALYZED";


            div.innerHTML =
                `
                <h3>
                    ${escapeHtml(
                        risk
                    )}
                </h3>

                <p>
                    <strong>Action:</strong>
                    ${escapeHtml(
                        item.action ||
                        "-"
                    )}
                </p>

                <p>
                    <strong>Decision:</strong>
                    ${escapeHtml(
                        decision
                    )}
                </p>

                <p>
                    <strong>Human Decision:</strong>
                    ${escapeHtml(
                        humanDecision
                    )}
                </p>

                <small>
                    ${escapeHtml(
                        item.timestamp ||
                        ""
                    )}
                </small>
                `;


            container.appendChild(
                div
            );
        }
    );
}


/* ============================================================
   STATISTICS
============================================================ */

function updateStatistics(
    history
) {

    const total =
        document.getElementById(
            "totalActions"
        );

    const low =
        document.getElementById(
            "lowRiskCount"
        );

    const medium =
        document.getElementById(
            "mediumRiskCount"
        );

    const high =
        document.getElementById(
            "highRiskCount"
        );


    let lowCount = 0;
    let mediumCount = 0;
    let highCount = 0;


    history.forEach(
        item => {

            const risk =
                String(
                    item.risk ||
                    ""
                ).toLowerCase();


            if (
                risk.includes(
                    "low"
                )
            ) {

                lowCount++;

            } else if (
                risk.includes(
                    "medium"
                )
            ) {

                mediumCount++;

            } else if (
                risk.includes(
                    "high"
                )
            ) {

                highCount++;
            }
        }
    );


    if (total) {

        total.textContent =
            history.length;
    }


    if (low) {

        low.textContent =
            lowCount;
    }


    if (medium) {

        medium.textContent =
            mediumCount;
    }


    if (high) {

        high.textContent =
            highCount;
    }
}


/* ============================================================
   CLEAR HISTORY
============================================================ */

async function clearHistory() {
    const confirmed = window.confirm(
        "Are you sure you want to clear your approval history?\n\n" +
        "This will permanently delete all of your recorded decisions."
    );

    if (!confirmed) {
        return;
    }

    const button = document.querySelector(
        ".clear-history-btn"
    );

    if (button) {
        button.disabled = true;
        button.textContent = "Clearing...";
    }

    try {
        console.log(
            "Clearing approval history..."
        );

        const data = await apiFetch(
            "/approval-history",
            {
                method: "DELETE"
            }
        );

        console.log(
            "Approval history cleared:",
            data
        );

        /*
         * Reload history from the backend.
         *
         * Because the backend now returns an empty
         * history for this user, this also resets:
         *
         * Total Actions = 0
         * Low Risk = 0
         * Medium Risk = 0
         * High Risk = 0
         */
        await loadHistory();

        alert(
            "History cleared successfully.\n\n" +
            "Deleted records: " +
            (data.deleted_count ?? 0)
        );

    } catch (error) {
        console.error(
            "Clear history failed:",
            error
        );

        alert(
            "Could not clear history.\n\n" +
            error.message
        );

    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = "🗑 Clear History";
        }
    }
}


/* ============================================================
   DISABLE APPROVAL BUTTONS
============================================================ */

function disableApprovalButtons() {

    const approve =
        document.getElementById(
            "approveBtn"
        );

    const reject =
        document.getElementById(
            "rejectBtn"
        );


    if (approve) {

        approve.disabled = true;
    }


    if (reject) {

        reject.disabled = true;
    }
}


function disableConfirmationButtons() {

    const confirm =
        document.getElementById(
            "confirmBtn"
        );

    const cancel =
        document.getElementById(
            "cancelBtn"
        );


    if (confirm) {

        confirm.disabled = true;
    }


    if (cancel) {

        cancel.disabled = true;
    }
}


/* ============================================================
   NAVIGATION
============================================================ */

function setupNavigation() {

    const links =
        document.querySelectorAll(
            ".nav-item"
        );


    links.forEach(
        link => {

            link.addEventListener(
                "click",
                function () {

                    links.forEach(
                        item =>
                            item.classList.remove(
                                "active"
                            )
                    );


                    this.classList.add(
                        "active"
                    );
                }
            );
        }
    );
}


/* ============================================================
   DECISION FORMATTER
============================================================ */

function formatDecision(
    decision
) {

    if (
        decision === null ||
        decision === undefined ||
        decision === ""
    ) {

        return "-";
    }


    const text =
        String(
            decision
        );


    return text
        .replace(
            /_/g,
            " "
        )
        .replace(
            /\b\w/g,
            char =>
                char.toUpperCase()
        );
}


/* ============================================================
   HTML ESCAPE
============================================================ */

function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


/* ============================================================
   GOOGLE LOGIN HELPER
============================================================ */

function loginWithGoogle() {

    window.location.href =
        "/auth/google";
}


/* ============================================================
   MAKE FUNCTIONS AVAILABLE TO HTML onclick=""
============================================================ */

window.checkAuthentication =
    checkAuthentication;

window.analyzeAction =
    analyzeAction;

window.approveAction =
    approveAction;

window.rejectAction =
    rejectAction;

window.confirmAction =
    confirmAction;

window.cancelAction =
    cancelAction;

window.logout =
    logout;

window.loadHistory =
    loadHistory;

window.clearHistory =
    clearHistory;

window.loginWithGoogle =
    loginWithGoogle;

window.showProfile =
    showProfile;
