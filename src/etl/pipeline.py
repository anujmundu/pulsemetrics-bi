"""
Fast Analytical ELT Pipeline utilizing DuckDB (with automated SQLite3 fallback).
Handles data hygiene, schema validation, and window aggregation.
"""

from pathlib import Path
from typing import Union
import sqlite3
import pandas as pd

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False


class AnalyticalPipeline:
    """Enterprise ELT pipeline with dual DuckDB / SQLite3 engine support."""

    def __init__(self, data_source: Union[str, Path, pd.DataFrame]):
        if isinstance(data_source, (str, Path)):
            try:
                df = pd.read_csv(data_source, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(data_source, encoding="latin1")
        else:
            df = data_source.copy()

        # Intelligent schema auto-normalization for real-world datasets (UCI, Microsoft, IBM, Northwind, etc.)
        df_cols_lower = {str(c).lower().strip(): c for c in df.columns}
        
        # 1. customer_id mapping
        cust_candidates = ["customer_id", "customerid", "customer_no", "client_id", "user_id", "account_id"]
        for c in cust_candidates:
            if c in df_cols_lower:
                df["customer_id"] = df[df_cols_lower[c]].astype(str)
                break
        if "customer_id" not in df.columns:
            df["customer_id"] = [f"CUST-{i%200+1:04d}" for i in range(len(df))]

        # 2. transaction_id mapping
        tx_candidates = ["transaction_id", "invoiceno", "salesorderid", "orderid", "order_id", "id", "trans_id"]
        for c in tx_candidates:
            if c in df_cols_lower:
                df["transaction_id"] = df[df_cols_lower[c]].astype(str)
                break
        if "transaction_id" not in df.columns:
            df["transaction_id"] = [f"TX-{i+1:06d}" for i in range(len(df))]

        # 3. date mapping
        date_candidates = ["date", "invoicedate", "orderdate", "created_at", "tx_date", "timestamp"]
        for c in date_candidates:
            if c in df_cols_lower:
                df["date"] = pd.to_datetime(df[df_cols_lower[c]], errors="coerce").dt.strftime("%Y-%m-%d")
                break
        if "date" not in df.columns or df["date"].isna().all():
            df["date"] = pd.date_range(start="2025-01-01", periods=len(df), freq="h").strftime("%Y-%m-%d")
        else:
            df["date"] = df["date"].fillna("2025-01-01")

        # 4. mrr_amount / revenue mapping
        rev_candidates = ["mrr_amount", "lineitemtotal", "monthlycharges", "totalcharges", "mrr", "amount", "total", "price", "revenue", "value"]
        found_rev = False
        for c in rev_candidates:
            if c in df_cols_lower:
                df["mrr_amount"] = pd.to_numeric(df[df_cols_lower[c]], errors="coerce").fillna(50.0).abs()
                found_rev = True
                break
        if not found_rev:
            if "unitprice" in df_cols_lower and "quantity" in df_cols_lower:
                df["mrr_amount"] = (pd.to_numeric(df[df_cols_lower["unitprice"]], errors="coerce").fillna(10.0) * 
                                    pd.to_numeric(df[df_cols_lower["quantity"]], errors="coerce").fillna(1.0)).abs()
            else:
                df["mrr_amount"] = 99.0

        # 5. plan / tier mapping
        plan_candidates = ["plan", "internetservice", "contract", "productid", "category", "stockcode"]
        for c in plan_candidates:
            if c in df_cols_lower:
                df["plan"] = df[df_cols_lower[c]].astype(str)
                break
        if "plan" not in df.columns:
            df["plan"] = "Growth"

        # 6. event_type
        if "event_type" not in df.columns:
            df["event_type"] = "RENEWAL"
            try:
                first_idx = df.groupby("customer_id")["date"].idxmin(skipna=True)
                df.loc[first_idx, "event_type"] = "NEW"
            except Exception:
                pass

        # 7. usage_score & support_tickets
        if "usage_score" not in df.columns:
            df["usage_score"] = 75.0
        if "support_tickets" not in df.columns:
            df["support_tickets"] = 1

        # 8. country
        country_candidates = ["country", "shipcountry", "country name"]
        for c in country_candidates:
            if c in df_cols_lower:
                df["country"] = df[df_cols_lower[c]].astype(str)
                break
        if "country" not in df.columns:
            df["country"] = "US"

        self.df_raw = df
        self.use_duckdb = DUCKDB_AVAILABLE

        if self.use_duckdb:
            self.con = duckdb.connect(database=":memory:")
            self.con.register("df_source", self.df_raw)
            self._build_duckdb_layers()
        else:
            self.con = sqlite3.connect(":memory:")
            self.df_raw.to_sql("raw_transactions", self.con, if_exists="replace", index=False)
            self._build_sqlite_layers()

    def _build_duckdb_layers(self):
        self.con.execute("""
            CREATE OR REPLACE TABLE clean_transactions AS
            SELECT 
                transaction_id,
                customer_id,
                CAST(date AS DATE) as tx_date,
                strftime(CAST(date AS DATE), '%Y-%m') as tx_month,
                event_type,
                plan,
                CAST(mrr_amount AS DOUBLE) as mrr,
                CAST(usage_score AS DOUBLE) as usage_score,
                CAST(support_tickets AS INTEGER) as support_tickets,
                country
            FROM df_source
            WHERE transaction_id IS NOT NULL AND customer_id IS NOT NULL
        """)

        self.con.execute("""
            CREATE OR REPLACE TABLE customer_cohorts AS
            SELECT 
                customer_id,
                MIN(tx_date) as first_signup_date,
                strftime(MIN(tx_date), '%Y-%m') as cohort_month,
                MAX(tx_date) as last_activity_date,
                SUM(mrr) as total_lifetime_value,
                COUNT(DISTINCT tx_month) as active_months_count,
                AVG(usage_score) as avg_usage_score,
                SUM(support_tickets) as total_support_tickets,
                MAX(plan) as latest_plan,
                BOOL_OR(event_type = 'CHURN') as is_churned
            FROM clean_transactions
            GROUP BY customer_id
        """)

    def _build_sqlite_layers(self):
        cursor = self.con.cursor()
        cursor.execute("""
            CREATE TABLE clean_transactions AS
            SELECT 
                transaction_id,
                customer_id,
                date as tx_date,
                substr(date, 1, 7) as tx_month,
                event_type,
                plan,
                CAST(mrr_amount AS REAL) as mrr,
                CAST(usage_score AS REAL) as usage_score,
                CAST(support_tickets AS INTEGER) as support_tickets,
                country
            FROM raw_transactions
            WHERE transaction_id IS NOT NULL AND customer_id IS NOT NULL
        """)

        cursor.execute("""
            CREATE TABLE customer_cohorts AS
            SELECT 
                customer_id,
                MIN(tx_date) as first_signup_date,
                substr(MIN(tx_date), 1, 7) as cohort_month,
                MAX(tx_date) as last_activity_date,
                SUM(mrr) as total_lifetime_value,
                COUNT(DISTINCT tx_month) as active_months_count,
                AVG(usage_score) as avg_usage_score,
                SUM(support_tickets) as total_support_tickets,
                MAX(plan) as latest_plan,
                MAX(CASE WHEN event_type = 'CHURN' THEN 1 ELSE 0 END) as is_churned
            FROM clean_transactions
            GROUP BY customer_id
        """)
        self.con.commit()

    def get_monthly_mrr_trends(self) -> pd.DataFrame:
        query = """
            SELECT 
                tx_month,
                SUM(mrr) as total_mrr,
                COUNT(DISTINCT customer_id) as active_subscribers,
                AVG(mrr) as arpu,
                SUM(CASE WHEN event_type = 'NEW_SIGNUP' THEN mrr ELSE 0 END) as new_mrr,
                SUM(CASE WHEN event_type = 'UPGRADE' THEN mrr ELSE 0 END) as expansion_mrr
            FROM clean_transactions
            WHERE event_type != 'CHURN'
            GROUP BY tx_month
            ORDER BY tx_month ASC
        """
        if self.use_duckdb:
            return self.con.execute(query).df()
        return pd.read_sql_query(query, self.con)

    def get_customer_summary(self) -> pd.DataFrame:
        query = "SELECT * FROM customer_cohorts"
        if self.use_duckdb:
            df = self.con.execute(query).df()
        else:
            df = pd.read_sql_query(query, self.con)
        df["is_churned"] = df["is_churned"].astype(bool)
        return df

    def get_raw_clean(self) -> pd.DataFrame:
        query = "SELECT * FROM clean_transactions ORDER BY tx_date ASC"
        if self.use_duckdb:
            return self.con.execute(query).df()
        return pd.read_sql_query(query, self.con)
