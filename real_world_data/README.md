# Authentic Real-World Data Directory: PulseMetrics-BI™

This directory contains **authentic, real-world e-commerce orders, SaaS subscription churn benchmarks, and enterprise sales ledgers** downloaded directly from international research repositories, Microsoft Learning, and open benchmarks.

---

### Downloaded Benchmark Datasets & Direct URLs

| # | File Name | File Size / Rows | Dataset Type & Industry | Direct Download URL / Source |
|---|---|---|---|---|
| **1** | `01_uci_online_retail_transactions.csv` | **42.9 MB**<br>*(541,909 real transactions)* | **UCI Machine Learning Repository**: Actual transactions from a UK registered non-store online retail platform. Contains InvoiceNo, StockCode, Quantity, UnitPrice, CustomerID, Country. | [UCI Online Retail Mirror](https://raw.githubusercontent.com/guipsamora/pandas_exercises/master/07_Visualization/Online_Retail/Online_Retail.csv) |
| **2** | `02_ibm_telco_customer_churn_mrr.csv` | **947.7 KB**<br>*(7,043 customer accounts)* | **IBM Telco Customer Churn & MRR Benchmark**: Real subscription churn dataset tracking tenure, MonthlyCharges, TotalCharges, contract types, and active churn status. | [IBM GitHub Repository](https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv) |
| **3** | `03_microsoft_enterprise_ecommerce_orders.csv` | **20.5 KB**<br>*(542 line orders)* | **Microsoft DP Commercial Orders**: Commercial order transactions with SalesOrderID, OrderDate, CustomerID, LineItemTotal, and ProductID. | [Microsoft Learning Official Repo](https://raw.githubusercontent.com/MicrosoftLearning/dp-data/main/orders.csv) |
| **4** | `04_northwind_global_sales_orders.csv` | **129.3 KB**<br>*(830 international orders)* | **Northwind Global Orders Dataset**: Enterprise trading transactions across Europe, Americas, and Asia with orderDate, customerID, freight, and shipCountry. | [GraphQL Northwind Dataset](https://raw.githubusercontent.com/graphql-compose/graphql-compose-examples/master/examples/northwind/data/csv/orders.csv) |
| **5** | `05_world_economic_revenue_benchmark.csv` | **549.6 KB**<br>*(Multi-year global metrics)* | **World Economic Benchmark**: Multi-year GDP and economic revenue aggregates across all sovereign nations. | [DataHub Open Datasets](https://raw.githubusercontent.com/datasets/gdp/master/data/gdp.csv) |

---

### Intelligent Schema Auto-Normalization
PulseMetrics-BI's `AnalyticalPipeline` has been equipped with an intelligent schema adapter that automatically detects and standardizes arbitrary column naming conventions:
- `CustomerID` / `customerID` / `user_id` -> `customer_id`
- `InvoiceNo` / `SalesOrderID` / `orderID` -> `transaction_id`
- `OrderDate` / `InvoiceDate` / `orderDate` -> `date`
- `LineItemTotal` / `MonthlyCharges` / `UnitPrice * Quantity` -> `mrr_amount`
- `Country` / `shipCountry` -> `country`

---

### How to Test in the Browser UI
1. Open the **PulseMetrics BI Dashboard** at `http://localhost:8502`.
2. In the left sidebar, locate the **Upload Subscription Ledger (CSV)** uploader.
3. Browse and upload any of the 5 real datasets (for quick interactive testing, `03_microsoft_enterprise_ecommerce_orders.csv` or `04_northwind_global_sales_orders.csv` or `02_ibm_telco_customer_churn_mrr.csv` load instantly; `01_uci_online_retail_transactions.csv` processes all 541k rows via DuckDB in seconds).
4. Watch the entire BI cockpit immediately recompute:
   - **Triangular Cohort Heatmap**: Dynamic retention matrix across customer cohorts.
   - **MRR Waterfall Decomposition**: Net revenue expansion vs churn.
   - **RFM Segmentation**: Recency, Frequency, Monetary value clustering.
   - **Predictive Churn Model**: Scored flight risk accounts with estimated ARR at risk.
   - **AI Text-to-SQL Copilot**: Query the real dataset in plain English.
