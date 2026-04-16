import streamlit as st
import requests
import pandas as pd

import os
import time
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")
REQUEST_TIMEOUT = 90
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.0

st.set_page_config(page_title="Credit Risk Platform", page_icon="💳", layout="wide")

st.markdown(
    """
    <style>
    /* Sticky title bar */
    .sticky-title-wrap {
        position: sticky;
        top: 0;
        z-index: 10000;
        background: white;
        padding: 10px 0 8px 0;
        border-bottom: 1px solid #dbe7ff;
        margin-bottom: 8px;
    }

    .main-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(
            90deg,
            #ff0000,
            #ff7f00,
            #ffff00,
            #00ff00,
            #0000ff,
            #4b0082,
            #8b00ff
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
    }

    /* Sticky tabs bar under title */
    div[data-testid="stTabs"] > div[role="tablist"] {
        position: sticky;
        top: 68px;   /* adjust to 72 if overlap */
        z-index: 9999;
        background: white;
        padding-top: 6px;
        padding-bottom: 6px;
        border-bottom: 1px solid #dbe7ff;
    }

    /* Prevent tab content from sitting under sticky tabs */
    div[data-testid="stTabs"] > div[role="tabpanel"] {
        padding-top: 0.75rem;
    }

    .sub-title {
        color: #4f5d75;
        margin-bottom: 1.2rem;
    }
    .section-card {
        background: linear-gradient(135deg, #f8fbff 0%, #eef4ff 100%);
        border: 1px solid #dbe7ff;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin: 0.6rem 0 0.9rem 0;
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #173b72;
        margin-bottom: 0.2rem;
    }
    .section-sub {
        color: #5c6780;
        font-size: 0.88rem;
    }
    .pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .pill-approve { background: #dcfce7; color: #166534; }
    .pill-conditional { background: #fef9c3; color: #854d0e; }
    .pill-decline { background: #fee2e2; color: #991b1b; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sticky-title-wrap"><div class="main-title">Loan Credit Risk Assessment Platform</div></div>',
    unsafe_allow_html=True,
)


def _request_with_retry(method: str, path: str, payload=None):
    url = f"{BACKEND_URL}{path}"
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            if method == "GET":
                resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            else:
                resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 200:
                return resp.json(), None

            # Retry only on rate limit errors (429)
            if resp.status_code == 429 and attempt < MAX_RETRIES - 1:
                retry_after_header = resp.headers.get("Retry-After")
                sleep_for = RETRY_BACKOFF_SECONDS * (2 ** attempt)

                if retry_after_header:
                    try:
                        sleep_for = max(float(retry_after_header), sleep_for)
                    except ValueError:
                        pass

                time.sleep(sleep_for)
                continue

            return None, f"{resp.status_code} - {resp.text}"

        except Exception as err:
            last_error = str(err)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_SECONDS * (2 ** attempt))
                continue
            return None, last_error

    return None, last_error or "Unknown request error"


def safe_get(path: str):
    return _request_with_retry("GET", path)


def safe_post(path: str, payload=None):
    return _request_with_retry("POST", path, payload)


def decision_pill(decision: str) -> str:
    if decision == "Approve":
        return '<span class="pill pill-approve">Approve</span>'
    if decision == "Conditional Approve":
        return '<span class="pill pill-conditional">Conditional Approve</span>'
    return '<span class="pill pill-decline">Decline</span>'


def prettify_factor(raw_name: str) -> str:
    name = raw_name.replace("num__", "").replace("cat__", "")
    if name.startswith("employment_type_"):
        return f"Employment Type: {name.replace('employment_type_', '').replace('_', ' ').title()}"
    if name.startswith("residence_type_"):
        return f"Residence Type: {name.replace('residence_type_', '').replace('_', ' ').title()}"
    return name.replace("_", " ").title()


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "📝 Loan Intake",
        "📋 Underwriter Dashboard",
        "🔎 Application Detail",
        "📊 Portfolio Dashboard",
        "📈 Model Performance",
        "⚖️ Fairness Report",
    ]
)

with tab1:
    st.subheader("Loan Application Intake")
    c1, c2, c3 = st.columns(3)
    with c1:
        age = st.number_input("Age", min_value=18, max_value=75, value=30)
        monthly_income = st.number_input("Monthly Income", min_value=1.0, value=40000.0, step=1000.0)
        employment_years = st.number_input("Employment Years", min_value=0.0, value=3.0, step=0.5)
        employment_type = st.selectbox("Employment Type", ["salaried", "self_employed", "unemployed"])
    with c2:
        existing_loan_amount = st.number_input("Existing Loan Amount", min_value=0.0, value=50000.0, step=1000.0)
        loan_amount_requested = st.number_input("Requested Loan Amount", min_value=1.0, value=150000.0, step=1000.0)
        loan_tenure_months = st.number_input("Loan Tenure (Months)", min_value=6, max_value=360, value=36)
        residence_type = st.selectbox("Residence Type", ["owned", "rented", "family"])
    with c3:
        credit_card_utilization = st.slider("Credit Card Utilization (%)", 0, 100, 50)
        missed_payments_last_12m = st.number_input("Missed Payments (Last 12 Months)", min_value=0, max_value=24, value=1)
        utility_payment_score = st.slider("Utility Payment Score", 0, 100, 75)
        mobile_recharge_consistency = st.slider("Mobile Recharge Consistency", 0, 100, 70)

    m1, m2 = st.columns(2)
    with m1:
        gender = st.selectbox("Gender", ["male", "female", "other"])
    with m2:
        consent_for_alt_data = st.checkbox("Consent for alternative data enrichment", value=True)

    if st.button("Get Risk Decision"):
        payload = {
            "age": age,
            "monthly_income": monthly_income,
            "employment_years": employment_years,
            "existing_loan_amount": existing_loan_amount,
            "loan_amount_requested": loan_amount_requested,
            "loan_tenure_months": loan_tenure_months,
            "credit_card_utilization": credit_card_utilization,
            "missed_payments_last_12m": missed_payments_last_12m,
            "utility_payment_score": utility_payment_score,
            "mobile_recharge_consistency": mobile_recharge_consistency,
            "employment_type": employment_type,
            "residence_type": residence_type,
            "gender": gender,
            "consent_for_alt_data": consent_for_alt_data,
        }
        result, err = safe_post("/predict", payload)
        if err:
            st.error(f"Prediction failed: {err}")
        else:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Application ID", result.get("application_id"))
            k2.metric("Risk Score", result.get("risk_score"))
            k3.metric("Risk Tier", result.get("risk_tier"))
            k4.metric("Confidence", result.get("confidence"))

            st.markdown("### Recommended Decision")
            st.markdown(decision_pill(result.get("recommended_decision", "Decline")), unsafe_allow_html=True)

            st.info(result.get("applicant_message", ""))
            st.write("**Underwriter Summary:**", result.get("underwriter_summary", ""))

            factors = result.get("top_factors", [])
            if factors:
                rows = []
                for factor in factors:
                    rows.append(
                        {
                            "Factor": prettify_factor(factor.get("factor", "Unknown")),
                            "Impact": factor.get("impact", ""),
                            "Explanation": factor.get("plain_language_reason", ""),
                        }
                    )
                st.markdown("### Explainability (Top 5 Factors)")
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            enrich = result.get("enriched_data", {})
            if enrich:
                st.markdown("### Alternative Data Enrichment Output")
                enrich_df = pd.DataFrame([{"Field": k, "Value": v} for k, v in enrich.items()])
                st.dataframe(enrich_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Underwriter Dashboard")
    if st.button("Refresh Queue"):
        apps, err = safe_get("/applications")
        if err:
            st.error(err)
        elif not apps:
            st.info("No applications available.")
        else:
            queue_df = pd.DataFrame(apps)
            st.dataframe(queue_df, use_container_width=True, hide_index=True)
            q1, q2, q3 = st.columns(3)
            q1.metric("Total Applications", len(queue_df))
            q2.metric("Average Risk Score", round(queue_df["risk_score"].mean(), 2))
            q3.metric(
                "High + Very High",
                int((queue_df["risk_tier"].isin(["High", "Very High"])).sum()),
            )

with tab3:
    st.subheader("Application Detail View")
    app_id = st.number_input("Enter Application ID", min_value=1, value=1)
    if st.button("Fetch Details"):
        detail, err = safe_get(f"/applications/{app_id}")
        if err:
            st.error(err)
        else:
            input_data = detail.get("input_data", {})
            output_data = detail.get("output_data", {})

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Application ID", detail.get("application_id"))
            d2.metric("Risk Score", output_data.get("risk_score", 0))
            d3.metric("Risk Tier", output_data.get("risk_tier", "Unknown"))
            d4.metric("Confidence", output_data.get("confidence", 0))

            st.markdown(decision_pill(output_data.get("recommended_decision", "Decline")), unsafe_allow_html=True)
            st.write("**Applicant Message:**", output_data.get("applicant_message", ""))
            st.write("**Underwriter Summary:**", output_data.get("underwriter_summary", ""))

            left, right = st.columns(2)
            with left:
                st.markdown("### Applicant Input Summary")
                input_df = pd.DataFrame([{"Field": k.replace("_", " ").title(), "Value": v} for k, v in input_data.items()])
                st.dataframe(input_df, use_container_width=True, hide_index=True)
            with right:
                st.markdown("### Explainability")
                factor_rows = []
                for factor in output_data.get("top_factors", []):
                    factor_rows.append(
                        {
                            "Factor": prettify_factor(factor.get("factor", "")),
                            "Impact": factor.get("impact", ""),
                            "Reason": factor.get("plain_language_reason", ""),
                        }
                    )
                if factor_rows:
                    st.dataframe(pd.DataFrame(factor_rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No factor explanations found.")

with tab4:
    st.subheader("Portfolio Risk Dashboard")
    st.markdown(
        '<div class="section-card"><div class="section-title">Portfolio Snapshot</div>'
        '<div class="section-sub">Track risk distribution across the active loan book.</div></div>',
        unsafe_allow_html=True,
    )
    summary, err = safe_get("/portfolio-summary")
    if err:
        st.error(f"Unable to load portfolio data: {err}")
    elif not summary:
        st.info("No portfolio data yet. Submit applications first.")
    else:
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Applications", summary.get("total_applications", 0))
        k2.metric("Average Risk Score", summary.get("average_risk_score", 0))
        high_risk = summary.get("risk_tier_distribution", {}).get("High", 0) + summary.get("risk_tier_distribution", {}).get("Very High", 0)
        k3.metric("High / Very High Cases", high_risk)

        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Risk Tier Distribution")
            risk_dist = summary.get("risk_tier_distribution", {})
            if risk_dist:
                risk_df = pd.DataFrame(
                    {"Risk Tier": list(risk_dist.keys()), "Count": list(risk_dist.values())}
                ).set_index("Risk Tier")
                st.bar_chart(risk_df)
            else:
                st.info("Risk tier distribution unavailable.")
        with c2:
            st.markdown("#### Decision Distribution")
            dec_dist = summary.get("decision_distribution", {})
            if dec_dist:
                dec_df = pd.DataFrame(
                    {"Decision": list(dec_dist.keys()), "Count": list(dec_dist.values())}
                ).set_index("Decision")
                st.bar_chart(dec_df)
            else:
                st.info("Decision distribution unavailable.")

with tab5:
    st.subheader("Model Performance")
    st.markdown(
        '<div class="section-card"><div class="section-title">Performance Monitoring</div>'
        '<div class="section-sub">Review decision rates and score trend over time.</div></div>',
        unsafe_allow_html=True,
    )
    metrics, err_m = safe_get("/model-metrics")
    trend, err_t = safe_get("/score-trend")

    if err_m:
        st.error(f"Unable to load model metrics: {err_m}")
    elif not metrics:
        st.info("No model metrics yet.")
    else:
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Approval Rate (%)", metrics.get("approval_rate", 0))
        m2.metric("Conditional Rate (%)", metrics.get("conditional_approval_rate", 0))
        m3.metric("Decline Rate (%)", metrics.get("decline_rate", 0))
        m4.metric("Avg Risk Score", metrics.get("average_risk_score", 0))
        m5.metric("Expected Default Rate (%)", metrics.get("expected_default_rate", 0))

        st.markdown("---")
        st.markdown("#### Decision Mix")
        rate_df = pd.DataFrame(
            {
                "Metric": ["Approval", "Conditional", "Decline"],
                "Rate": [
                    metrics.get("approval_rate", 0),
                    metrics.get("conditional_approval_rate", 0),
                    metrics.get("decline_rate", 0),
                ],
            }
        ).set_index("Metric")
        st.bar_chart(rate_df)

    if err_t:
        st.error(f"Unable to load score trend: {err_t}")
    elif trend:
        st.markdown("#### Risk Score Trend Over Time")
        trend_df = pd.DataFrame(trend).sort_values("date")
        st.line_chart(trend_df.set_index("date")[["average_risk_score"]])

        st.markdown("#### Application Volume Trend")
        st.bar_chart(trend_df.set_index("date")[["application_count"]])
    else:
        st.info("Trend data not available yet.")

with tab6:
    st.subheader("Fairness Report (Demographic Monitoring)")
    st.markdown(
        '<div class="section-card"><div class="section-title">Bias Monitoring Overview</div>'
        '<div class="section-sub">Compare outcome rates across demographic segments.</div></div>',
        unsafe_allow_html=True,
    )
    fairness, err = safe_get("/fairness-report")
    if err:
        st.error(f"Unable to load fairness report: {err}")
    elif not fairness:
        st.info("No fairness data yet. Submit applications with gender field.")
    else:
        fair_df = pd.DataFrame(fairness)

        f1, f2 = st.columns(2)
        f1.metric("Demographic Segments", fair_df["segment"].nunique())
        f2.metric("Total Records in Fairness View", int(fair_df["total_applications"].sum()))

        st.markdown("---")
        st.markdown("#### Segment-wise Decision Rates")
        display_cols = [
            "segment",
            "total_applications",
            "approval_rate",
            "conditional_approval_rate",
            "decline_rate",
        ]
        st.dataframe(fair_df[display_cols], use_container_width=True, hide_index=True)

        st.markdown("#### Visual Comparison (Approval vs Decline)")
        chart_df = fair_df[["segment", "approval_rate", "decline_rate"]].set_index("segment")
        st.bar_chart(chart_df)

        st.caption(
            "This is a basic fairness monitoring view for assignment scope. "
            "Production fairness requires deeper statistical checks."
        )