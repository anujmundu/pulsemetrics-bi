"""
Synthetic Enterprise SaaS Transaction & Subscription Data Generator.
Simulates realistic customer lifecycles, upgrades, downgrades, and churn events
across multiple cohorts over 24 months.
"""

from pathlib import Path
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


def generate_enterprise_saas_data(
    num_customers: int = 1200,
    start_date: str = "2024-01-01",
    months: int = 24,
    output_csv: str = "data/saas_revenue_ledger.csv",
) -> pd.DataFrame:
    random.seed(42)
    np.random.seed(42)

    plans = {
        "Starter": {"base_mrr": 49.0, "weight": 0.45},
        "Professional": {"base_mrr": 199.0, "weight": 0.38},
        "Enterprise": {"base_mrr": 899.0, "weight": 0.17},
    }

    plan_names = list(plans.keys())
    plan_weights = [plans[p]["weight"] for p in plan_names]

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    transactions = []

    for cust_idx in range(1, num_customers + 1):
        customer_id = f"CUST-{cust_idx:05d}"
        signup_month_offset = random.randint(0, months - 6)
        signup_date = start_dt + timedelta(days=signup_month_offset * 30 + random.randint(1, 28))

        current_plan = random.choices(plan_names, weights=plan_weights)[0]
        current_mrr = plans[current_plan]["base_mrr"]
        tenure_months = random.randint(3, months - signup_month_offset)

        # Baseline churn probability per month
        monthly_churn_prob = 0.045 if current_plan == "Starter" else (0.025 if current_plan == "Professional" else 0.012)
        has_churned = False

        for m in range(tenure_months):
            tx_date = signup_date + timedelta(days=m * 30 + random.randint(-1, 2))
            if tx_date > (start_dt + timedelta(days=months * 30)):
                break

            # Upgrade or downgrade event
            event_type = "RENEWAL"
            if m == 0:
                event_type = "NEW_SIGNUP"
            elif not has_churned and random.random() < 0.06:
                # Upgrade
                if current_plan == "Starter":
                    current_plan = "Professional"
                    current_mrr = plans["Professional"]["base_mrr"]
                    event_type = "UPGRADE"
                elif current_plan == "Professional":
                    current_plan = "Enterprise"
                    current_mrr = plans["Enterprise"]["base_mrr"]
                    event_type = "UPGRADE"
            elif not has_churned and random.random() < 0.03:
                # Downgrade
                if current_plan == "Enterprise":
                    current_plan = "Professional"
                    current_mrr = plans["Professional"]["base_mrr"]
                    event_type = "DOWNGRADE"

            # Check churn
            if m > 1 and not has_churned and random.random() < monthly_churn_prob:
                has_churned = True
                transactions.append({
                    "transaction_id": f"TX-{customer_id}-{m:02d}-CHURN",
                    "customer_id": customer_id,
                    "date": tx_date.strftime("%Y-%m-%d"),
                    "event_type": "CHURN",
                    "plan": current_plan,
                    "mrr_amount": 0.0,
                    "usage_score": round(random.uniform(5.0, 30.0), 1),  # Low usage precedes churn
                    "support_tickets": random.randint(3, 8),
                    "country": random.choice(["USA", "UK", "Germany", "Canada", "Australia", "India"]),
                })
                break

            # Active transaction
            usage_score = round(random.uniform(45.0, 99.0), 1)
            support_tickets = random.randint(0, 2)

            transactions.append({
                "transaction_id": f"TX-{customer_id}-{m:02d}",
                "customer_id": customer_id,
                "date": tx_date.strftime("%Y-%m-%d"),
                "event_type": event_type,
                "plan": current_plan,
                "mrr_amount": float(current_mrr),
                "usage_score": usage_score,
                "support_tickets": support_tickets,
                "country": random.choice(["USA", "UK", "Germany", "Canada", "Australia", "India"]),
            })

    df = pd.DataFrame(transactions)
    df = df.sort_values(by="date").reset_index(drop=True)

    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    df = generate_enterprise_saas_data()
    print(f"Generated {len(df)} transactions across {df['customer_id'].nunique()} customers.")
