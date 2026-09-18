"""
Automated unit test suite for PulseMetrics-Copilot 2026 upgrades.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.etl.pipeline import AnalyticalPipeline
from src.etl.data_generator import generate_enterprise_saas_data
from src.analytics.text_to_sql import TextToSQLEngine
from src.analytics.causal_attribution import CausalAttributionEngine
from src.analytics.board_memo_generator import BoardMemoGenerator
from src.analytics.revenue_waterfall import RevenueWaterfallEngine


@pytest.fixture
def sample_pipeline():
    df = generate_enterprise_saas_data(num_customers=80, months=6)
    return AnalyticalPipeline(df)


def test_text_to_sql_execution(sample_pipeline):
    engine = TextToSQLEngine(sample_pipeline)

    # Test churn by plan
    res1 = engine.compile_and_execute("Show me churn by plan")
    assert res1["success"] is True
    assert not res1["data"].empty
    assert "plan" in res1["data"].columns or "latest_plan" in res1["data"].columns

    # Test revenue by country
    res2 = engine.compile_and_execute("What is the revenue by country?")
    assert res2["success"] is True
    assert not res2["data"].empty
    assert "country" in res2["data"].columns


def test_causal_attribution(sample_pipeline):
    cust_df = sample_pipeline.get_customer_summary()
    report = CausalAttributionEngine.diagnose_churn_drivers(cust_df)

    assert report["status"] == "DIAGNOSIS_COMPLETE"
    assert len(report["findings"]) >= 2
    assert "Platform Usage Deterioration" in [f["driver"] for f in report["findings"]]


def test_board_memo_generation(sample_pipeline):
    clean_tx = sample_pipeline.get_raw_clean()
    cust_df = sample_pipeline.get_customer_summary()

    wf = RevenueWaterfallEngine.calculate_waterfall(clean_tx)
    causal = CausalAttributionEngine.diagnose_churn_drivers(cust_df)
    churn_metrics = {"potential_arr_at_risk": 50000.0, "high_risk_accounts_count": 5}

    memo = BoardMemoGenerator.generate_board_memo(wf, churn_metrics, causal, company_name="Acme SaaS")
    assert "CONFIDENTIAL: Board of Directors Strategic Briefing" in memo
    assert "Acme SaaS" in memo
    assert "Net Revenue Retention" in memo
