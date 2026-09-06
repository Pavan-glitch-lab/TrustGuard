# 🛡️ TrustGuard AI

### AI Agent Security & Risk Management Platform

TrustGuard AI is an AI-agent risk oversight platform that analyzes agent actions, evaluates security and operational risk, and determines whether an action should execute autonomously, require user confirmation, or require human approval.

**Live Demo:** https://trustguard-production-2dba.up.railway.app/

---

## 🚀 What TrustGuard AI Does

As AI agents become capable of taking real-world actions, not every action should be executed automatically.

TrustGuard AI provides a safety layer between an AI agent and high-impact actions.

It evaluates actions across multiple risk dimensions and produces an appropriate execution decision:

| Risk Level | Score | Decision             |
| ---------- | ----: | -------------------- |
| 🟢 Low     |   0–8 | Autonomous Execution |
| 🟡 Medium  |  9–16 | User Confirmation    |
| 🔴 High    | 17–25 | Human Approval       |

---

## 🔐 Risk Assessment

TrustGuard evaluates five major risk factors:

* **Privacy Risk**
* **Financial Risk**
* **Data Modification Risk**
* **Irreversibility Risk**
* **External Impact Risk**

The resulting score ranges from **0 to 25**.

---

## 🧠 Hybrid Risk Intelligence

TrustGuard combines:

### Rule-Based Risk Engine

A deterministic five-factor risk engine evaluates the characteristics of an AI-agent action.

### Machine Learning Prediction

A trained machine-learning model provides an additional risk prediction.

### Hybrid Decision Engine

The final system selects the higher risk level between the rule-based assessment and ML prediction, providing a safety-oriented decision.

This creates three possible execution paths:

```text
AI Agent Action
       │
       ▼
┌─────────────────────┐
│ Rule-Based Analysis │
└──────────┬──────────┘
           │
           ├──────────────┐
           ▼              ▼
   ┌─────────────┐  ┌─────────────┐
   │ ML Analysis │  │ Risk Factors│
   └──────┬──────┘  └──────┬──────┘
          └────────┬────────┘
                   ▼
          ┌─────────────────┐
          │ Hybrid Decision │
          └────────┬────────┘
                   ▼
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   Autonomous   Confirmation  Approval
```

---

## ✨ Features

* AI-agent action risk analysis
* Five-factor risk scoring
* Machine-learning risk prediction
* Hybrid risk decision engine
* Low / Medium / High risk classification
* Autonomous execution decision
* User confirmation workflow
* Human approval workflow
* Approval history
* Secure authentication
* Google authentication
* Password reset
* Protected dashboard
* Security operations dashboard
* Responsive mobile interface
* Animated risk visualization
* Production deployment on Railway

---

## 🏗️ Architecture

```text
Frontend
HTML + CSS + JavaScript
        │
        │ HTTPS API
        ▼
Flask Backend
        │
        ├── Authentication
        ├── Risk Engine
        ├── ML Predictor
        ├── Hybrid Decision Engine
        └── Approval / History
        │
        ▼
Machine Learning Model
        │
        ▼
Risk Decision
```

---

## 🛠️ Technology Stack

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* Flask
* Flask-CORS
* Gunicorn

### Machine Learning

* scikit-learn
* pandas
* NumPy
* joblib

### Authentication & Security

* Flask sessions
* Secure password hashing
* Google OAuth
* Password reset workflow
* HTTPS
* Secure / HttpOnly session cookies

### Deployment

* Railway
* GitHub

---

## 📁 Project Structure

```text
TrustGuard/
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── hybrid_engine.py
│   ├── risk_engine.py
│   ├── ml_model.py
│   ├── ml_predictor.py
│   ├── models/
│   ├── requirements.txt
│   └── .gitignore
│
├── dataset/
│   └── development.csv
│
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── reset-password.html
│   ├── script.js
│   ├── style.css
│   ├── robots.txt
│   └── sitemap.xml
│
└── README.md
```

---

## 🧪 Example Risk Decisions

### Low Risk

> AI agent creates a reminder for the user to attend a meeting tomorrow.

**Result:** Low Risk
**Score:** 0
**Decision:** Autonomous Execution

### Medium Risk

> AI agent uploads a project abstract to the college portal.

**Result:** Medium Risk
**Score:** 6
**Decision:** User Confirmation

### High Risk

> AI agent transfers ₹50,000 to a newly added bank account.

**Result:** High Risk
**Score:** 15
**Decision:** Human Approval

---

## 🎯 Project Goal

TrustGuard AI explores how AI agents can operate safely in environments where actions may affect:

* sensitive information
* financial resources
* user data
* external systems
* irreversible operations

The goal is to provide a practical risk-control layer that helps keep autonomous AI actions **observable, explainable, and appropriately governed**.

---

## 🌐 Live Application

**TrustGuard AI:**
https://trustguard-production-2dba.up.railway.app/

---

## 📌 Project Status

**Production deployed and operational.**

The project currently includes authentication, AI-agent risk analysis, hybrid ML/rule-based decision making, approval workflows, dashboard monitoring, responsive UI, and production deployment.
