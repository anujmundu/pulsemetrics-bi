"""
SaaS MRR / ARR Waterfall Engine.
Decomposes revenue changes into New, Expansion, Contraction, and Churn components.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


class RevenueWaterfallEngine:
    """Computes MRR waterfall dynamics and Net Revenue Retention (NRR)."""

    @classmethod
    def calculate_waterfall(cls, clean_tx_df: pd.DataFrame) -> pd.DataFrame:
        df = clean_tx_df.copy()
        df["tx_date"] = pd.to_datetime(df["tx_date"])
        df["month"] = df["tx_date"].dt.to_period("M").astype(str)

        months = sorted(df["month"].unique())
        waterfall_records = []

        prev_mrr = 0.0

        for m in months:
            m_df = df[df["month"] == m]

            new_mrr = m_df[m_df["event_type"] == "NEW_SIGNUP"]["mrr"].sum()
            expansion_mrr = m_df[m_df["event_type"] == "UPGRADE"]["mrr"].sum()
            contraction_mrr = m_df[m_df["event_type"] == "DOWNGRADE"]["mrr"].sum()
            churn_mrr = m_df[m_df["event_type"] == "CHURN"]["mrr"].sum()

            total_billed_mrr = m_df[m_df["event_type"] != "CHURN"]["mrr"].sum()

            # Net Revenue Retention (NRR) = (Beginning + Expansion - Contraction - Churn) / Beginning
            if prev_mrr > 0:
                nrr = ((prev_mrr + expansion_mrr - contraction_mrr - churn_mrr) / prev_mrr) * 100.0
            else:
                nrr = 100.0

            waterfall_records.append({
                "month": m,
                "starting_mrr": round(prev_mrr, 2),
                "new_mrr": round(new_mrr, 2),
                "expansion_mrr": round(expansion_mrr, 2),
                "contraction_mrr": round(-abs(contraction_mrr), 2),
                "churn_mrr": round(-abs(churn_mrr), 2),
                "ending_mrr": round(total_billed_mrr, 2),
                "nrr_pct": round(nrr, 1),
            })
            prev_mrr = total_billed_mrr

        return pd.DataFrame(waterfall_records)
