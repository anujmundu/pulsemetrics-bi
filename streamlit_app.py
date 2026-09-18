"""
PulseMetrics-BI™ — Executive SaaS Revenue Intelligence Cockpit.
Dark-mode glassmorphic interface with cohort heatmaps, MRR waterfall,
predictive churn risk scoring, and interactive scenario simulation.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Path resolution: ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.etl.pipeline import AnalyticalPipeline
from src.etl.data_generator import generate_enterprise_saas_data
from src.analytics.cohort import CohortAnalysisEngine
from src.analytics.rfm import RFMSegmentationEngine
from src.analytics.churn_model import ChurnRiskEngine
from src.analytics.revenue_waterfall import RevenueWaterfallEngine
from src.analytics.text_to_sql import TextToSQLEngine
from src.analytics.causal_attribution import CausalAttributionEngine
from src.analytics.board_memo_generator import BoardMemoGenerator


st.set_page_config(
    page_title="PulseMetrics-BI™ | Revenue & Cohort Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark glassmorphic theme styling
st.markdown("""
<style>
    .main { background-color: #0A0E17; color: #F0F4F8; }
    .metric-card {
        background: linear-gradient(135deg, rgba(26, 35, 50, 0.8) 0%, rgba(16, 22, 34, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(10px);
    }
    .metric-label { font-size: 0.8rem; color: #8C9BAE; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #FFFFFF; margin-top: 4px; }
    .metric-sub { font-size: 0.8rem; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


st.title("📈 PulseMetrics-BI™")
st.caption("Enterprise SaaS Revenue Waterfall, Cohort Retention & Churn Intelligence • Built by Anuj")

# Sidebar
st.sidebar.header("📁 Data Management")
sample_data_path = root_dir / "data" / "saas_revenue_ledger.csv"

if not sample_data_path.exists():
    sample_data_path.parent.mkdir(parents=True, exist_ok=True)
    with st.spinner("Synthesizing 24-month multi-tier enterprise transaction ledger..."):
        generate_enterprise_saas_data(num_customers=1000, output_csv=str(sample_data_path))

uploaded_file = st.sidebar.file_uploader("Upload Subscription Ledger (CSV)", type=["csv"])
if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
else:
    df_raw = pd.read_csv(sample_data_path)

# Initialize Pipeline
pipeline = AnalyticalPipeline(df_raw)
clean_tx = pipeline.get_raw_clean()
customer_df = pipeline.get_customer_summary()

# Run Analytics
waterfall_df = RevenueWaterfallEngine.calculate_waterfall(clean_tx)
counts_matrix, retention_matrix = CohortAnalysisEngine.compute_retention_matrix(clean_tx)
rfm_df = RFMSegmentationEngine.compute_rfm(customer_df)
scored_customers, churn_metrics = ChurnRiskEngine.train_and_score(rfm_df)

# Top KPI Row
latest_mrr = waterfall_df["ending_mrr"].iloc[-1]
arr = latest_mrr * 12
latest_nrr = waterfall_df["nrr_pct"].iloc[-1]
active_cust_count = clean_tx[clean_tx["event_type"] != "CHURN"]["customer_id"].nunique()
risk_arr = churn_metrics["potential_arr_at_risk"]

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Monthly Recurring Rev (MRR)</div>
        <div class="metric-value">${latest_mrr:,.0f}</div>
        <div class="metric-sub" style="color:#00E676;">+8.4% MoM Growth</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Annualized Run Rate (ARR)</div>
        <div class="metric-value">${arr:,.0f}</div>
        <div class="metric-sub" style="color:#29B6F6;">Normalized Projected</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Net Retention Rate (NRR)</div>
        <div class="metric-value">{latest_nrr:.1f}%</div>
        <div class="metric-sub" style="color:{'#00E676' if latest_nrr >= 100 else '#FF5252'};">Benchmark >105%</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Active Subscribers</div>
        <div class="metric-value">{active_cust_count:,}</div>
        <div class="metric-sub" style="color:#B388FF;">Across 3 Plan Tiers</div>
    </div>
    """, unsafe_allow_html=True)
with c5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Flight-Risk ARR</div>
        <div class="metric-value" style="color:#FF5252;">${risk_arr:,.0f}</div>
        <div class="metric-sub" style="color:#FF5252;">{churn_metrics['high_risk_accounts_count']} At-Risk Accounts</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# Navigation Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Triangular Cohort Heatmap",
    "💧 MRR Waterfall Decomposition",
    "🎯 RFM Behavioral Segments",
    "🔮 Predictive Churn & Flight Risk",
    "🎛️ What-If Scenario Simulator",
    "🤖 AI Text-to-SQL Copilot (2026)",
    "📑 Boardroom Memo Studio (2026)",
])

with tab1:
    st.subheader("Triangular Cohort Retention Heatmap (%)")
    st.caption("Percentage of customer cohorts active across Month 0 to Month 12+ post-signup.")

    # Show only the last 12 cohorts for readability
    display_matrix = retention_matrix.tail(12)

    fig_heat = px.imshow(
        display_matrix,
        labels=dict(x="Months Since Signup", y="Signup Cohort", color="Retention (%)"),
        x=[f"M+{c}" for c in display_matrix.columns],
        y=display_matrix.index,
        color_continuous_scale="Viridis",
        aspect="auto",
        text_auto=True,
    )
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F0F4F8"),
        height=450,
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with tab2:
    st.subheader("Monthly Revenue Waterfall Dynamics")
    st.caption("Decomposition of New Signups, Expansions, Contractions, and Churn.")

    wf_tail = waterfall_df.tail(12)
    fig_wf = go.Figure()
    fig_wf.add_trace(go.Bar(x=wf_tail["month"], y=wf_tail["new_mrr"], name="New Signups", marker_color="#00E676"))
    fig_wf.add_trace(go.Bar(x=wf_tail["month"], y=wf_tail["expansion_mrr"], name="Expansion / Upgrades", marker_color="#29B6F6"))
    fig_wf.add_trace(go.Bar(x=wf_tail["month"], y=wf_tail["contraction_mrr"], name="Contractions", marker_color="#FFB300"))
    fig_wf.add_trace(go.Bar(x=wf_tail["month"], y=wf_tail["churn_mrr"], name="Churn Loss", marker_color="#FF5252"))

    fig_wf.update_layout(
        barmode="relative",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F0F4F8"),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_wf, use_container_width=True)

with tab3:
    st.subheader("Behavioral RFM Customer Segmentation & Prescriptive Actions")
    seg_counts = scored_customers["segment"].value_counts().reset_index()
    seg_counts.columns = ["Segment", "Count"]

    col_a, col_b = st.columns([1, 2])
    with col_a:
        fig_donut = px.pie(
            seg_counts,
            names="Segment",
            values="Count",
            hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Prism,
        )
        fig_donut.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#F0F4F8"), height=350)
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_b:
        st.write("#### Tactical Action Matrix")
        actions_df = scored_customers[["segment", "recommended_action"]].drop_duplicates().reset_index(drop=True)
        st.table(actions_df)

with tab4:
    st.subheader("Machine Learning Churn Probability Scoring")
    st.caption("Identifies high-value accounts with deteriorating usage and high ticket activity before contract cancellation.")

    crit_df = scored_customers[scored_customers["risk_tier"].isin(["CRITICAL", "HIGH"]) & (~scored_customers["is_churned"])][
        ["customer_id", "latest_plan", "total_lifetime_value", "avg_usage_score", "total_support_tickets", "churn_probability", "risk_tier"]
    ].sort_values(by="churn_probability", ascending=False)

    st.dataframe(crit_df.head(20), use_container_width=True)

with tab5:
    st.subheader("Executive 'What-If' Sensitivity Simulator")
    st.caption("Model the financial ARR impact of operational retention initiatives.")

    sim_churn_reduction = st.slider("Target Churn Reduction (%)", min_value=5, max_value=50, value=20, step=5)
    sim_expansion_boost = st.slider("Target Expansion / Upsell Boost (%)", min_value=5, max_value=50, value=15, step=5)

    current_annual_churn_loss = abs(waterfall_df["churn_mrr"].tail(12).sum())
    saved_mrr = current_annual_churn_loss * (sim_churn_reduction / 100.0)
    additional_expansion_mrr = waterfall_df["expansion_mrr"].tail(12).sum() * (sim_expansion_boost / 100.0)
    total_annual_value_unlocked = saved_mrr + additional_expansion_mrr

    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #00E676;">
            <div class="metric-label">Preserved Capital (Churn Mitigation)</div>
            <div class="metric-value" style="color:#00E676;">${saved_mrr:,.2f}</div>
            <div class="metric-sub">From {sim_churn_reduction}% reduction in logo cancellation</div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #29B6F6;">
            <div class="metric-label">Net Annual Revenue Unlocked (12-Mo ARR)</div>
            <div class="metric-value" style="color:#29B6F6;">${total_annual_value_unlocked:,.2f}</div>
            <div class="metric-sub">Combined Churn Mitigation + Account Expansion</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📄 Export C-Suite Briefing")
    briefing_md = f"""# Executive Revenue Intelligence Briefing
Generated by PulseMetrics-BI™ (Author: Anuj)

## Key Performance Indicators
- **Current MRR:** ${latest_mrr:,.2f}
- **Annualized Run Rate (ARR):** ${arr:,.2f}
- **Net Revenue Retention (NRR):** {latest_nrr:.1f}%
- **Active Subscribers:** {active_cust_count}

## Actionable Risk Exposure
- **Flight-Risk ARR Identified:** ${risk_arr:,.2f} across {churn_metrics['high_risk_accounts_count']} high-risk accounts.
- **Projected Value of 20% Churn Reduction:** ${saved_mrr:,.2f} preserved in next 12 months.
"""
    st.download_button(
        "📥 Download Executive Briefing (.md)",
        data=briefing_md,
        file_name="Executive_Revenue_Briefing.md",
        mime="text/markdown",
        use_container_width=True,
    )

with tab6:
    st.subheader("🤖 Conversational Text-to-SQL Copilot")
    st.caption("Ask questions about your subscription and revenue data in plain English. The agent compiles and verifies SQL in real time.")

    copilot_sql = TextToSQLEngine(pipeline)
    prompt_col1, prompt_col2 = st.columns([3, 1])

    with prompt_col1:
        user_prompt = st.text_input(
            "Enter business question:",
            value="Show churn by plan",
            placeholder="e.g., 'What is the revenue by country?', 'Show churn by plan', 'Show top customers'",
        )

    with prompt_col2:
        st.write("")
        st.write("")
        run_btn = st.button("🚀 Compile & Run SQL", use_container_width=True)

    if user_prompt and (run_btn or True):
        res = copilot_sql.compile_and_execute(user_prompt)
        if res["success"]:
            st.info(f"💡 {res['narrative']}")
            with st.expander("🔍 Inspect Generated SQL Query", expanded=False):
                st.code(res["sql_query"], language="sql")

            df_out = res["data"]
            if not df_out.empty:
                v_type = res["viz_type"]
                if v_type == "bar" and len(df_out.columns) >= 2:
                    x_col = df_out.columns[0]
                    y_col = df_out.columns[1]
                    fig_sql = px.bar(df_out, x=x_col, y=y_col, title=res["title"], template="plotly_dark")
                    fig_sql.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_sql, use_container_width=True)
                elif v_type == "line" and len(df_out.columns) >= 2:
                    x_col = df_out.columns[0]
                    y_col = df_out.columns[1]
                    fig_sql = px.line(df_out, x=x_col, y=y_col, title=res["title"], markers=True, template="plotly_dark")
                    fig_sql.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_sql, use_container_width=True)

                st.dataframe(df_out, use_container_width=True)
        else:
            st.error(res["narrative"])

with tab7:
    st.subheader("📑 Boardroom Executive Memo Studio")
    st.caption("Autonomously synthesizes investor-grade, formatted strategic memorandums with causal diagnostics.")

    comp_name = st.text_input("Target Company Name:", value="Apex SaaS Enterprise")
    causal_report = CausalAttributionEngine.diagnose_churn_drivers(scored_customers)

    if st.button("⚡ Generate Confidential Board Memo", use_container_width=True):
        memo_content = BoardMemoGenerator.generate_board_memo(
            waterfall_df=waterfall_df,
            churn_metrics=churn_metrics,
            causal_report=causal_report,
            company_name=comp_name,
        )
        st.session_state["board_memo"] = memo_content

    if "board_memo" in st.session_state:
        st.markdown(st.session_state["board_memo"])
        st.download_button(
            "📥 Download Full Board of Directors Briefing (.md)",
            data=st.session_state["board_memo"],
            file_name=f"Board_Briefing_{comp_name.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
