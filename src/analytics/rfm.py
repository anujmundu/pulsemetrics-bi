"""
Behavioral RFM (Recency, Frequency, Monetary) Segmentation Engine.
Partitions customers into actionable tiers with automated business recommendations.
"""

from datetime import datetime
import pandas as pd
import numpy as np


class RFMSegmentationEngine:
    """Calculates quintile-based RFM scores and business labels."""

    SEGMENT_ACTIONS = {
        "Champions": "Reward loyalty, offer beta feature access, request video testimonials & case studies.",
        "Loyal Customers": "Upsell to annual or Enterprise contracts, offer premium add-ons.",
        "Potential Loyalists": "Offer onboarding optimization, training webinars, and usage incentives.",
        "At Risk": "Immediate customer success intervention, automated discount offer on annual renew.",
        "Hibernating / Lost": "Automated re-engagement email sequence with major new feature announcements.",
    }

    @classmethod
    def compute_rfm(cls, customer_summary_df: pd.DataFrame, reference_date: str = None) -> pd.DataFrame:
        df = customer_summary_df.copy()
        df["last_activity_date"] = pd.to_datetime(df["last_activity_date"])

        if reference_date:
            ref_dt = pd.to_datetime(reference_date)
        else:
            ref_dt = df["last_activity_date"].max()

        df["recency_days"] = (ref_dt - df["last_activity_date"]).dt.days
        df["frequency"] = df["active_months_count"]
        df["monetary"] = df["total_lifetime_value"]

        # 1-5 rank scoring using quantiles
        df["r_score"] = pd.qcut(df["recency_days"], q=5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
        df["f_score"] = pd.qcut(df["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
        df["m_score"] = pd.qcut(df["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)

        df["rfm_composite"] = df["r_score"].astype(str) + df["f_score"].astype(str) + df["m_score"].astype(str)

        def assign_segment(row):
            r, f, m = row["r_score"], row["f_score"], row["m_score"]
            if r >= 4 and f >= 4:
                return "Champions"
            elif r >= 3 and f >= 3:
                return "Loyal Customers"
            elif r >= 3 and f < 3:
                return "Potential Loyalists"
            elif r < 3 and f >= 2:
                return "At Risk"
            else:
                return "Hibernating / Lost"

        df["segment"] = df.apply(assign_segment, axis=1)
        df["recommended_action"] = df["segment"].map(cls.SEGMENT_ACTIONS)

        return df
