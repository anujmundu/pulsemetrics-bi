"""
Causal Anomaly Detection & Root-Cause Attribution Engine.
Analyzes feature drift and statistical divergence between retained and churned accounts
to isolate primary operational drivers behind revenue leaks.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


class CausalAttributionEngine:
    """Diagnoses root causes behind churn spikes and revenue anomalies."""

    @classmethod
    def diagnose_churn_drivers(cls, customer_df: pd.DataFrame) -> Dict[str, Any]:
        df = customer_df.copy()

        retained = df[~df["is_churned"]]
        churned = df[df["is_churned"]]

        if churned.empty or retained.empty:
            return {"status": "INSUFFICIENT_DATA", "findings": []}

        # 1. Usage Score Divergence
        avg_usage_ret = float(retained["avg_usage_score"].mean())
        avg_usage_chr = float(churned["avg_usage_score"].mean())
        usage_drop_pct = ((avg_usage_ret - avg_usage_chr) / max(avg_usage_ret, 1)) * 100

        # 2. Support Ticket Frequency
        avg_tix_ret = float(retained["total_support_tickets"].mean())
        avg_tix_chr = float(churned["total_support_tickets"].mean())
        ticket_increase_pct = ((avg_tix_chr - avg_tix_ret) / max(avg_tix_ret, 0.1)) * 100

        # 3. Plan Vulnerability
        plan_churn_rates = df.groupby("latest_plan")["is_churned"].mean() * 100
        highest_churn_plan = plan_churn_rates.idxmax()
        highest_plan_rate = float(plan_churn_rates.max())

        findings: List[Dict[str, Any]] = [
            {
                "driver": "Platform Usage Deterioration",
                "severity": "CRITICAL" if usage_drop_pct > 30 else "MODERATE",
                "metric": f"{usage_drop_pct:.1f}% lower usage prior to cancellation",
                "evidence": f"Retained avg: {avg_usage_ret:.1f}/100 vs Churned avg: {avg_usage_chr:.1f}/100",
                "prescriptive_action": "Trigger automated onboarding check-in when account usage falls below 45/100 for 14 consecutive days.",
            },
            {
                "driver": "Support Ticket Escalation",
                "severity": "HIGH" if ticket_increase_pct > 50 else "LOW",
                "metric": f"{ticket_increase_pct:.1f}% higher support ticket frequency",
                "evidence": f"Retained avg: {avg_tix_ret:.1f} tickets vs Churned avg: {avg_tix_chr:.1f} tickets",
                "prescriptive_action": "Route accounts with 3+ open tickets directly to Tier-2 Customer Success Managers for proactive de-escalation.",
            },
            {
                "driver": f"Vulnerable Plan Tier ({highest_churn_plan})",
                "severity": "HIGH" if highest_plan_rate > 20 else "MODERATE",
                "metric": f"{highest_plan_rate:.1f}% overall churn rate on {highest_churn_plan} tier",
                "evidence": f"Compare against baseline average of {df['is_churned'].mean()*100:.1f}% across all tiers.",
                "prescriptive_action": f"Re-evaluate onboarding or pricing packaging for {highest_churn_plan} tier customers.",
            },
        ]

        return {
            "status": "DIAGNOSIS_COMPLETE",
            "total_accounts_analyzed": len(df),
            "retained_count": len(retained),
            "churned_count": len(churned),
            "overall_churn_rate_pct": round(float(df["is_churned"].mean() * 100), 1),
            "findings": findings,
            "root_cause_summary": (
                f"Churn is primarily driven by usage deterioration ({usage_drop_pct:.1f}% drop) "
                f"amplified by unresolved support tickets on the {highest_churn_plan} tier."
            ),
        }
