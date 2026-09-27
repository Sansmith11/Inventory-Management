"""Deterministic inventory math. The LLM NEVER computes these numbers itself —
it only calls these functions and explains the results in natural language.
"""
import math
from data import PRODUCTS_DF, SALES_DF

SAFETY_FACTOR = 1.5  # simple safety-stock multiplier on daily demand std dev


def _row(product: str):
    matches = PRODUCTS_DF[PRODUCTS_DF["product"].str.lower() == product.lower()]
    if matches.empty:
        return None
    return matches.iloc[0]


def _forecast_7day(product: str, demand_increase_pct: float = 0.0) -> float:
    """7-day demand forecast = recent 14-day avg daily sales * 7, with weekday
    seasonality already baked into the historical average. Adjustable for
    what-if scenarios via demand_increase_pct."""
    hist = SALES_DF[SALES_DF["product"].str.lower() == product.lower()]
    recent = hist.sort_values("date").tail(14)
    avg_daily = float(recent["qty_sold"].mean())
    forecast = avg_daily * 7 * (1 + demand_increase_pct / 100.0)
    return round(forecast, 1)


def _safety_stock(product: str) -> float:
    hist = SALES_DF[SALES_DF["product"].str.lower() == product.lower()]
    std_daily = float(hist["qty_sold"].std())
    row = _row(product)
    lead_time = float(row["lead_time_days"])
    return round(SAFETY_FACTOR * std_daily * math.sqrt(lead_time), 1)


def get_low_stock() -> list[dict]:
    """Products whose current stock is at or below their reorder point."""
    out = []
    for _, row in PRODUCTS_DF.iterrows():
        rop = calculate_reorder(row["product"])
        if row["current_stock"] <= rop["reorder_point"]:
            out.append({
                "product": row["product"],
                "current_stock": int(row["current_stock"]),
                "reorder_point": rop["reorder_point"],
                "recommended_order": rop["recommended_order"],
            })
    return out


def get_product_status(product: str) -> dict:
    row = _row(product)
    if row is None:
        return {"error": f"Unknown product '{product}'"}
    rop = calculate_reorder(product)
    return {
        "product": row["product"],
        "current_stock": int(row["current_stock"]),
        "price": float(row["price"]),
        "reorder_point": rop["reorder_point"],
        "forecast_7day": rop["forecast_7day"],
        "recommended_order": rop["recommended_order"],
        "status": "LOW" if row["current_stock"] <= rop["reorder_point"] else "HEALTHY",
    }


def calculate_reorder(product: str, demand_increase_pct: float = 0.0) -> dict:
    """ROP = demand during lead time + safety stock.
    Recommended order = 7-day forecast - current stock (never below 0).
    """
    row = _row(product)
    if row is None:
        return {"error": f"Unknown product '{product}'"}
    forecast_7day = _forecast_7day(product, demand_increase_pct)
    safety_stock = _safety_stock(product)
    demand_during_lead_time = float(row["avg_daily_demand"]) * float(row["lead_time_days"]) * (1 + demand_increase_pct / 100.0)
    reorder_point = round(demand_during_lead_time + safety_stock, 1)
    recommended_order = max(0, round(forecast_7day - float(row["current_stock"])))
    return {
        "product": row["product"],
        "forecast_7day": forecast_7day,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "recommended_order": recommended_order,
    }


def inventory_value() -> dict:
    total = (PRODUCTS_DF["current_stock"] * PRODUCTS_DF["price"]).sum()
    return {"total_inventory_value": round(float(total), 2)}


def top_value_products(n: int = 5) -> list[dict]:
    df = PRODUCTS_DF.copy()
    df["value"] = df["current_stock"] * df["price"]
    df = df.sort_values("value", ascending=False).head(n)
    return [
        {"product": r["product"], "value": round(float(r["value"]), 2)}
        for _, r in df.iterrows()
    ]


def what_if(product: str, demand_increase_pct: float) -> dict:
    baseline = calculate_reorder(product, 0.0)
    scenario = calculate_reorder(product, demand_increase_pct)
    return {
        "product": product,
        "baseline_recommended_order": baseline.get("recommended_order"),
        "scenario_recommended_order": scenario.get("recommended_order"),
        "demand_increase_pct": demand_increase_pct,
    }


TOOLS = {
    "get_low_stock": get_low_stock,
    "get_product_status": get_product_status,
    "calculate_reorder": calculate_reorder,
    "inventory_value": inventory_value,
    "top_value_products": top_value_products,
    "what_if": what_if,
}

TOOL_SCHEMAS = [
    {
        "name": "get_low_stock",
        "description": "List all products currently at or below their reorder point.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_product_status",
        "description": "Get current stock, reorder point, forecast and recommended order for one product.",
        "parameters": {
            "type": "object",
            "properties": {"product": {"type": "string"}},
            "required": ["product"],
        },
    },
    {
        "name": "calculate_reorder",
        "description": "Calculate reorder point and recommended order quantity for a product, optionally with a demand increase percentage for scenario analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
                "demand_increase_pct": {"type": "number", "default": 0},
            },
            "required": ["product"],
        },
    },
    {
        "name": "inventory_value",
        "description": "Total value (stock * price) of the entire shop inventory.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "top_value_products",
        "description": "Products holding the most money in inventory (stock * price), highest first.",
        "parameters": {
            "type": "object",
            "properties": {"n": {"type": "integer", "default": 5}},
        },
    },
    {
        "name": "what_if",
        "description": "Scenario analysis: compare current recommended order vs a demand-increase scenario for one product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
                "demand_increase_pct": {"type": "number"},
            },
            "required": ["product", "demand_increase_pct"],
        },
    },
]
