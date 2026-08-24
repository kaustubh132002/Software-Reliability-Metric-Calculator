# Software Reliability Metric Calculator

A modern, responsive web application for **Software Engineering and Quality Assurance (SEQA)** designed to analyze and calculate core software reliability metrics.

---

## 📐 Mathematical Formulations (SEQA Standards)

| Metric | Formula | Definition & Purpose |
| :--- | :--- | :--- |
| **MTBF** *(Mean Time Between Failures)* | $\text{MTBF} = \frac{\text{Total Operating Time}}{\text{Number of Failures}}$ | Average operational uptime between successive software or system failures. |
| **MTTR** *(Mean Time To Repair)* | $\text{MTTR} = \frac{\text{Total Repair Time}}{\text{Number of Failures}}$ | Average downtime required to diagnose, patch, and restore normal service. |
| **Failure Rate** $(\lambda)$ | $\lambda = \frac{\text{Number of Failures}}{\text{Total Operating Time}}$ | Frequency of unexpected failure occurrences per operational hour. |
| **System Availability** $(A)$ | $A = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}} \times 100\%$ | Percentage probability that the system is fully accessible and functional. |
| **Mission Reliability** $R(t)$ | $R(t) = e^{-\lambda t}$ | Probability that the software functions continuously without failure over mission time $t$. |

---

## 🌟 Key Features

1. **User Authentication & Role Management**
   - Secure account registration with email validation and hashed passwords (`werkzeug.security`).
   - Session-based authentication with "Remember Me" capability.
   - Dual-role system: **Admin** (system-wide monitoring and user control) and **Student / QA Engineer**.
   - 1-Click quick login buttons for testing and grading evaluation.

2. **Executive Reliability Dashboard**
   - Live KPI Stat Cards: Total Systems, Cumulative Failures, Portfolio Average MTBF, Average MTTR, System Availability.
   - 4 Interactive **Chart.js** Visualizers:
     - **MTBF Trend** (Spline curve)
     - **MTTR Trend** (Recovery time bar chart)
     - **Availability Comparison** (Target benchmark comparison)
     - **Failure Rate ($\lambda$) Graph** (Area chart)
   - Recent evaluations summary with direct report generation.

3. **Interactive Reliability Calculator**
   - Real-time instant computation as you type (no page reload required).
   - Form inputs for System Name, Category, Operating Hours, Failure Count, Down Time, and Mission Time.
   - Step-by-step mathematical substitution breakdown showing exact formula evaluations.
   - Interactive preset lab scenarios for Telecom switches, FinTech ledgers, E-Commerce platforms, and Avionics units.
   - Dynamic reliability badge indicators (Four 9s High Availability, Production Tier, Moderate, Critical).

4. **History & Record Management Module**
   - Full CRUD support: Create, Read, in-place Edit via modal dialog, and Delete with safety confirmation.
   - Live multi-criteria keyword search and architectural category filtering.
   - Multi-column sorting (by Date, Availability, MTBF, Failure count) and clean pagination.

5. **Professional Reporting & Exports**
   - **Single System Audit PDF Report**: Generates formatted, standalone PDF documents with mathematical steps using ReportLab.
   - **Portfolio Summary PDF Report**: Multi-system audit summary table.
   - **CSV Export**: Clean spreadsheet export with UTC timestamps and raw metrics.

6. **Modern Dark Blue & Crisp White UI Theme**
   - Deep blue `#0b132b`, `#1e40af`, `#0284c7`, `#f8fafc` palette.
   - Full **Dark / Light Mode** switch with `localStorage` persistence.
   - Toast notification system for instant user feedback.
   - 100% responsive for Desktop, Tablet, and Mobile devices.

---

## 📁 Project Directory Structure

```
Software-Reliability-Calculator/
│── app.py                 # Flask Application factory & routing setup
│── requirements.txt       # Python project dependencies
│── database.db            # SQLite database with pre-populated sample records
│── models.py              # Database schema, queries, calculations, and auth helpers
│── routes.py              # Web views, REST APIs, CSV and ReportLab PDF generators
│── seed_data.py           # Sample data seeding script with realistic benchmark systems
│── test_app.py            # Unit and integration test suite
│── static/
│     ├── css/
│     │    └── styles.css  # Dark Blue & White theme, Dark/Light modes, responsive CSS
│     ├── js/
│     │    ├── main.js     # Theme toggle, mobile sidebar, toast alerts, modal handlers
│     │    ├── calculator.js # Real-time mathematical calculation engine & presets
│     │    ├── charts.js   # Chart.js visualizations (MTBF, MTTR, Availability, Failure Rate)
│     │    └── history.js  # Search, filter, pagination, edit modal, delete confirmation
│     └── images/
│          └── logo.svg    # Vector brand icon
│── templates/
│     ├── base.html        # Main layout shell with sidebar, topbar, and notifications
│     ├── login.html       # Authentication login screen with 1-click test fill
│     ├── register.html    # User registration screen
│     ├── dashboard.html   # KPI stat cards, charts, and recent activity
│     ├── calculator.html  # Live calculator with formulas and step-by-step breakdown
│     ├── history.html     # Historical data table with search, filter, edit & delete
│     ├── admin.html       # Admin control center and user management
│     ├── profile.html     # User profile and individual metrics
│     ├── 404.html         # Page not found error screen
│     └── 500.html         # Server error screen
└── README.md              # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Installation
Clone or navigate to the project directory and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the Flask development server:
```bash
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo User Credentials

The database is pre-seeded with sample user accounts for testing:

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Lead Administrator** | `admin@seqa.edu` | `admin123` | Full administrative control, all records, user management |
| **QA Engineer / Student** | `student@seqa.edu` | `student123` | Standard calculations, personal history, CSV & PDF export |

*(Note: 1-click demo login buttons are provided directly on the login screen for rapid access)*

---

## 🧪 Running the Test Suite

To run the automated unit and integration tests:
```bash
python test_app.py
```
All mathematical formulas, database integrity constraints, user authentication flows, and PDF/CSV export routines are verified.

---

## 📊 Pre-Populated Benchmark Systems

The application includes realistic industry test datasets:
- **Telecom Core Signaling Node** (Carrier-grade $99.96\%$ availability, $T=8760\text{h}$)
- **DO-178C Avionics Flight Navigation Module** ($99.99\%$ availability, $T=4380\text{h}$)
- **Hospital Patient Telemetry Monitor** ($99.99\%$ safety-critical compliance, $T=5000\text{h}$)
- **FinTech Transaction Core Hub** ($99.94\%$ financial ledger, $T=3600\text{h}$)
- **Cloud Payment Gateway** ($99.94\%$ availability, $T=2400\text{h}$)
- **Black Friday E-Commerce Checkout API** ($99.33\%$ availability under stress, $T=1200\text{h}$)
- **IoT Telemetry Stream Engine** ($97.82\%$ load-stressed streaming, $T=720\text{h}$)
