"""
Triangular Cohort Retention Analysis Engine.
Computes retention rates (percentage of users active in month 0, 1, 2... N)
and visualizes the customer decay curve.
"""

from typing import Tuple
import pandas as pd
import numpy as np


class CohortAnalysisEngine:
    """Computes dynamic triangular retention matrices."""

    @classmethod
    def compute_retention_matrix(cls, clean_tx_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Takes cleaned transactions with customer_id, tx_date.
        Returns:
            - absolute_counts_matrix: raw count of active customers per cohort and period
            - retention_pct_matrix: percentage retained relative to Month 0
        """
        df = clean_tx_df[clean_tx_df["event_type"] != "CHURN"].copy()
        df["tx_date"] = pd.to_datetime(df["tx_date"])
        df["order_month"] = df["tx_date"].dt.to_period("M")

        # Determine cohort month (first purchase month)
        df["cohort_month"] = df.groupby("customer_id")["order_month"].transform("min")

        # Calculate period offset (months since signup)
        df["cohort_index"] = (df["order_month"].dt.year - df["cohort_month"].dt.year) * 12 + (
            df["order_month"].dt.month - df["cohort_month"].dt.month
        )

        # Pivot to triangular matrix
        cohort_data = df.groupby(["cohort_month", "cohort_index"])["customer_id"].nunique().reset_index()
        counts_matrix = cohort_data.pivot(index="cohort_month", columns="cohort_index", values="customer_id")
        counts_matrix.index = counts_matrix.index.astype(str)

        # Compute percentage retention
        cohort_sizes = counts_matrix.iloc[:, 0]
        retention_matrix = counts_matrix.divide(cohort_sizes, axis=0) * 100.0

        return counts_matrix, retention_matrix.round(1)
