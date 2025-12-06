
# 🌟 LuminaBI  
### A Django-Powered Automated Data Analytics & Business Intelligence Platform

LuminaBI is a modern, lightweight alternative to Power BI and Tableau — built with **Django**, **Pandas**, **Chart.js**, and **Django REST Framework**.  
It automatically transforms raw datasets into **clean data**, **visual dashboards**, and **actionable insights**, with no technical skills required.

---

## 🚀 Features

### 🔐 Authentication
- User registration & login  
- Password reset  
- Profile management  
- Secure session-based authentication  

### 📤 Dataset Upload
- Upload CSV, Excel, JSON, and PDF files 
- Automatic file validation and preview
- Metadata extraction (size, columns, rows, file type)  
- Real-time upload progress with WebSocket
- Raw & cleaned versions stored securely  

### 🧼 Automated Data Cleaning
- Intelligent duplicate detection and removal
- Handle missing values(Smart missing value handling (mean, median, mode, interpolation))  
- Column name normalization (snake_case, CamelCase, etc.)
- Convert datatype inconsistencies  
- Date/time parsing with multiple format detection
- Generate summary statistics  

### 📊 Auto-Generated Visualizations
- Bar, Line, Pie charts  
- Correlation heatmaps  
- Auto-chart suggestions based on data types
- Histograms  
- Scatter plots  
- Real-time chart updates with WebSocket
- Smart chart suggestions based on column types  
- Visualizations rendered with **Chart.js / Plotly.js**  

### 🧠 Insights Engine
- Trend detection and analysis  
- Category rankings  
- Outlier identification with statistical methods
- Correlation analysis and heatmaps 
- Time-series summaries  
- AI-powered insights  

### 📉 Dashboard Builder
    Drag-and-drop interface with HTML5 Drag API

    Grid-based layout system

    Real-time collaboration with WebSocket

    Multiple saved dashboards per user

    Interactive filters (date ranges, categories, sliders)

    Public shareable dashboard links

### 📄 Exporting & Reporting
- PDF report generation  
- Export cleaned dataset  
- Export charts as PNG  
- Public shareable dashboard links  
- email report delivery
- scheduled automated delivery


🚀 Luminabi — Pricing & Subscription Module

This document describes the Pricing & Subscription System added to the Luminabi project.
It introduces subscription tiers, trial rules, billing cycles, and recommended enhancements to keep the system scalable, secure, and user–friendly.
📌 Overview

The Luminabi Pricing Module provides a structured and flexible subscription workflow for users at various usage levels.
The system includes:

    Multiple subscription tiers

    Monthly and yearly billing cycles (up to 2 years)

    Free-trial limits

    Integration in the main navigation bar

    Support for both individual users and organizations

This module ensures that access to Luminabi’s advanced analytics, automation, and data features aligns with user needs and business value.
🌟 Subscription Tiers
1. Individual (Personal)

    Designed for single users.

    Access to core Luminabi features.

    Affordable monthly/yearly pricing.

    Free Trial: Up to 5 trial sessions per day.

2. Team (Group ≤ 5 Members)

    For small teams, startups, or student groups.

    Shared workspace.

    Team activity tracking.

    Role-based permissions.

    Free Trial: Up to 5 trial sessions per day (team-wide).

3. Business

    For small-to-medium organizations.

    Enhanced collaboration and project management.

    API access and advanced analytics.

    Higher usage limits.

    Priority support.

    Free Trial: Up to 5 trial sessions per day.

4. Enterprise

    For large-scale organizations.

    Custom integrations, dedicated environments.

    Premium SLA, onboarding support.

    Unlimited team members.

    Custom pricing via sales.

    Free Trial: Up to 5 trial sessions per day.

🗓️ Billing Cycles

    Monthly Plans

    Yearly Plans (12 months)

    Extended Plans (maximum 24 months)

Each plan includes transparent billing, reminders, renewal notifications, and usage monitoring.
🆓 Free Trial Rules

    All tiers support 5 free trial uses per day.

    Trial limits refresh automatically every 24 hours.

    Trials allow partial access to features depending on tier.

    Unlimited signups do not bypass trial checks.

🧩 Key Features of the Pricing Module
✔ Subscription Management

    Upgrade / downgrade handling

    Automatic proration (optional)

    Plan switching with confirmation

    Subscription cancellation flow

✔ Billing & Payments

    Integrates with Stripe, Paystack, or Flutterwave

    Secure encrypted payment handling

    Refund logic (optional)

✔ Access Control

    Middleware-based feature locking

    Tier-based permission system

    Usage tracking

    Daily trial counters

✔ UI/UX Integration

    “Pricing” page added to navigation bar

    Responsive pricing tables

    Plan comparison view

    Clear CTA buttons (Subscribe, Upgrade, Continue Trial, etc.)

🛠 Implementation Notes (Recommended Approach)
1. Django Model Structure

Create models for:

    SubscriptionPlan

    Subscription

    TrialUsage

    Team (optional)

    FeatureFlag (optional)

2. Use Django Signals

For:

    Assigning trial counts on signup

    Resetting trial limits

    Triggering emails on plan changes

3. Middleware or Decorators

To restrict access:

    If trial exceeded → redirect to pricing

    If subscription expired → lock premium features

4. Caching Layer

For trial counters and plan lookups (Redis recommended).
🚀 Enhancements & Future Improvements
✨ 1. Add Usage-Based Billing

Instead of only tier-based pricing, allow:

    Per-seat pricing

    Per-API-call pricing

    Data-processing volume pricing

✨ 2. Discounts and Coupons

Useful for:

    Student plans

    Festival promos

    Referral-based discounts

✨ 3. Loyalty System

Reward long-term subscribers with:

    Extra trial runs

    Discount coupons

    Premium templates

✨ 4. AI Recommendation Engine

Based on user behavior:

    Suggest the ideal subscription plan

    Predict plan upgrades

✨ 5. Admin Analytics Dashboard

Let admins see:

    Daily subscription growth

    Revenue trends

    Trial-to-paid conversion rate

    Churn rate

✨ 6. Grace Period Support

When a subscription expires:

    Allow a 48-hour window before locking features

✨ 7. Email & Notification Automation

    Renewal reminders

    Trial limit warnings

    Payment success/failure notifications

✨ 8. Team Management Tools

    Invite members

    Assign roles

    Remove inactive users


### 🧩 REST API (Optional)
- Upload dataset  
- Fetch clean dataset  
- Retrieve analytics JSON  
- Chart config endpoints  
- Token-based authentication  

---

# 🏗️ Tech Stack

### **Backend**
- Django  
- Django REST Framework  
- Pandas / NumPy  
- Scikit-learn (optional insights)  
- PostgreSQL  

### **Frontend**
- HTML5 / TailwindCSS  
- Chart.js or Plotly  
- HTMX / Alpine.js  
- AJAX for dynamic updates  

### **DevOps**
- Docker (optional)  
- Gunicorn + Nginx (deployment)  

---

