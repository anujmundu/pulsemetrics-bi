"""
Automated unit test suite for PulseMetrics-BI analytics pipeline.
"""

import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.etl.pipeline import AnalyticalPipeline
from src.etl.data_generator import generate_enterprise_saas_data
from src.analytics.cohort import CohortAnalysisEngine
from src.analytics.rfm import RFMSegmentationEngine
from src.analytics.churn_model import ChurnRiskEngine
from src.analytics.revenue_waterfall import RevenueWaterfallEngine


@pytest.fixture
def sample_df():
    return generate_enterprise_saas_data(num_customers=50, months=6)


def test_analytical_pipeline_duckdb(sample_df):
    pipeline = AnalyticalPipeline(sample_df)
    clean_tx = pipeline.get_raw_clean()
    customer_df = pipeline.get_customer_summary()

    assert len(clean_tx) > 0
    assert len(customer_df) > 0
    assert "mrr" in clean_tx.columns
    assert "cohort_month" in customer_df.columns


def test_cohort_retention_matrix(sample_df):
    pipeline = AnalyticalPipeline(sample_df)
    clean_tx = pipeline.get_raw_clean()
    counts, retention = CohortAnalysisEngine.compute_retention_matrix(clean_tx)

    assert not retention.empty
    # Month 0 retention must be 100%
    assert (retention.iloc[:, 0] == 100.0).all()


def test_rfm_segmentation(sample_df):
    pipeline = AnalyticalPipeline(sample_df)
    cust_df = pipeline.get_customer_summary()
    rfm_df = RFMSegmentationEngine.compute_rfm(cust_df)

    assert "segment" in rfm_df.columns
    assert "recommended_action" in rfm_df.columns
    assert rfm_df["segment"].nunique() >= 1


def test_churn_model_scoring(sample_df):
    pipeline = AnalyticalPipeline(sample_df)
    cust_df = pipeline.get_customer_summary()
    rfm_df = RFMSegmentationEngine.compute_rfm(cust_df)
    scored_df, metrics = ChurnRiskEngine.train_and_score(rfm_df)

    assert "churn_probability" in scored_df.columns
    assert "risk_tier" in scored_df.columns
    assert (scored_df["churn_probability"] >= 0.0).all() and (scored_df["churn_probability"] <= 1.0).all()


def test_revenue_waterfall(sample_df):
    pipeline = AnalyticalPipeline(sample_df)
    clean_tx = pipeline.get_raw_clean()
    wf = RevenueWaterfallEngine.calculate_waterfall(clean_tx)

    assert "starting_mrr" in wf.columns
    assert "ending_mrr" in wf.columns
    assert "nrr_pct" in wf.columns
