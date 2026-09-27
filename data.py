"""Synthetic shop inventory + sales data for the demo. No external DB."""
import numpy as np
import pandas as pd

np.random.seed(7)

PRODUCTS = [
    # name, category, price, avg_daily_demand, lead_time_days, current_stock
    ("Biscuits",   "Snacks",      10,  9.0, 2, 18),
    ("Milk",       "Dairy",       28,  12.0, 1, 15),
    ("Coke",       "Beverages",   40,  6.0, 2, 25),
    ("Rice",       "Staples",     60,  3.0, 4, 40),
    ("Atta",       "Staples",     55,  2.5, 4, 35),
    ("Sugar",      "Staples",     45,  2.0, 3, 30),
    ("Soap",       "Personal Care",35,  1.5, 3, 20),
    ("Eggs (dozen)","Dairy",      70,  4.0, 1, 8),
]

def _make_products_df():
    rows = []
    for name, cat, price, demand, lead, stock in PRODUCTS:
        rows.append({
            "product": name,
            "category": cat,
            "price": price,
            "avg_daily_demand": demand,
            "lead_time_days": lead,
            "current_stock": stock,
        })
    return pd.DataFrame(rows)

def _make_sales_history(days=90):
    """Synthetic daily sales per product with weekday + noise."""
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days)
    records = []
    for name, cat, price, demand, lead, stock in PRODUCTS:
        for d in dates:
            weekend_mult = 1.4 if d.weekday() >= 5 else 1.0
            noise = np.random.normal(1.0, 0.25)
            qty = max(0, round(demand * weekend_mult * noise))
            records.append({"date": d, "product": name, "qty_sold": qty})
    return pd.DataFrame(records)

PRODUCTS_DF = _make_products_df()
SALES_DF = _make_sales_history()
