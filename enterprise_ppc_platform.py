# ============================================================
# PPC TOOL PRO
# Advanced Amazon PPC Intelligence Engine
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(page_title="PPC Tool Pro", layout="wide")

st.markdown("""
<style>
body {background-color: #0E1117; color: white;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 PPC Tool Pro")

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_div(a, b):
    return a / b if b != 0 else 0

def find_col(df, keys):
    for k in keys:
        for c in df.columns:
            if k in c.lower():
                return c
    return None

# ============================================================
# FILE UPLOAD
# ============================================================

file = st.file_uploader("Upload Search Term Report", type=["csv", "xlsx"])

if file:

    df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
    df.columns = df.columns.str.lower().str.strip()

    # ============================================================
    # COLUMN STANDARDIZATION
    # ============================================================

    mapping = {
        "search_term": ["search term"],
        "campaign": ["campaign"],
        "ad_group": ["ad group"],
        "spend": ["spend"],
        "sales": ["sales"],
        "orders": ["orders"],
        "clicks": ["clicks"],
        "impressions": ["impressions"],
        "sku": ["sku"]
    }

    for std, keys in mapping.items():
        col = find_col(df, keys)
        if col:
            df[std] = df[col]
        else:
            if std == "sku":
                df[std] = "UNKNOWN"
            else:
                df[std] = 0

    df.fillna(0, inplace=True)

    # ============================================================
    # CORE METRICS
    # ============================================================

    df["cpc"] = df.apply(lambda r: safe_div(r["spend"], r["clicks"]), axis=1)
    df["ctr"] = df.apply(lambda r: safe_div(r["clicks"], r["impressions"]) * 100, axis=1)
    df["cvr"] = df.apply(lambda r: safe_div(r["orders"], r["clicks"]) * 100, axis=1)
    df["roas"] = df.apply(lambda r: safe_div(r["sales"], r["spend"]), axis=1)
    df["acos"] = df.apply(lambda r: safe_div(r["spend"], r["sales"]) * 100, axis=1)
    df["hard_waste"] = np.where(df["sales"] == 0, df["spend"], 0)

    avg_cvr = df["cvr"].mean()
    avg_ctr = df["ctr"].mean()
    avg_roas = df["roas"].mean()
    avg_cpc = df["cpc"].mean()

    # ============================================================
    # PROFIT SETTINGS
    # ============================================================

    st.sidebar.header("💰 Profit Settings")
    margin = st.sidebar.slider("Margin %", 10, 80, 40)
    organic_sales = st.sidebar.number_input("Organic Sales (Optional)", value=0)

    break_even_roas = 1 / (margin / 100)

    # ============================================================
    # UNIFIED INTELLIGENCE SCORE
    # ============================================================

    def uis(r):
        roas_factor = (r["roas"] / (break_even_roas + 0.01)) * 30
        cvr_factor = (r["cvr"] / (avg_cvr + 0.01)) * 25
        ctr_factor = (r["ctr"] / (avg_ctr + 0.01)) * 15
        cpc_factor = (avg_cpc / (r["cpc"] + 0.01)) * 15
        score = roas_factor + cvr_factor + ctr_factor + cpc_factor
        return max(0, min(100, score))

    df["uis"] = df.apply(uis, axis=1)

    # ============================================================
    # SMART BID ENGINE
    # ============================================================

    def smart_bid(r):
        if r["uis"] >= 80:
            return r["cpc"] * 1.25
        elif r["uis"] >= 60:
            return r["cpc"] * 1.15
        elif r["uis"] >= 40:
            return r["cpc"]
        elif r["uis"] >= 20:
            return r["cpc"] * 0.9
        else:
            return r["cpc"] * 0.8

    df["smart_bid"] = df.apply(smart_bid, axis=1)

    # ============================================================
    # OVERVIEW
    # ============================================================

    total_spend = df["spend"].sum()
    total_sales = df["sales"].sum()
    total_orders = df["orders"].sum()

    total_roas = safe_div(total_sales, total_spend)
    total_acos = safe_div(total_spend, total_sales) * 100
    total_waste = df["hard_waste"].sum()

    total_sales_all = total_sales + organic_sales
    tacos = safe_div(total_spend, total_sales_all) * 100

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Spend", f"₹ {total_spend:,.2f}")
    c2.metric("Sales", f"₹ {total_sales:,.2f}")
    c3.metric("ROAS", f"{total_roas:.2f}")
    c4.metric("ACOS %", f"{total_acos:.2f}%")
    c5.metric("Hard Waste", f"₹ {total_waste:,.2f}")
    c6.metric("TACOS %", f"{tacos:.2f}%")

    # ============================================================
    # KEYWORD TABLE
    # ============================================================

    st.subheader("📊 Keyword Intelligence")

    st.dataframe(df[[
        "search_term", "campaign", "spend", "sales",
        "roas", "acos", "cvr", "uis", "smart_bid"
    ]].round(2))

    # ============================================================
    # NEGATIVE KEYWORDS
    # ============================================================

    st.subheader("⛔ Negative Candidates")

    negative_df = df[(df["sales"] == 0) & (df["spend"] > avg_cpc * 5)]

    st.dataframe(negative_df[[
        "search_term", "spend", "hard_waste", "campaign"
    ]].round(2))

    negative_bulk = pd.DataFrame({
        "Record Type": "Negative Keyword",
        "Campaign Name": negative_df["campaign"],
        "Ad Group Name": negative_df["ad_group"],
        "Keyword or Product Targeting": negative_df["search_term"],
        "Match Type": "Negative Exact",
        "Status": "enabled"
    })

    st.download_button(
        "Download Negative Bulk File",
        negative_bulk.to_csv(index=False),
        "negative_bulk.csv"
    )

    # ============================================================
    # SMART BID BULK
    # ============================================================

    smart_bulk = pd.DataFrame({
        "Record Type": "Keyword",
        "Campaign Name": df["campaign"],
        "Ad Group Name": df["ad_group"],
        "Keyword or Product Targeting": df["search_term"],
        "Match Type": "Exact",
        "Bid": df["smart_bid"].round(2),
        "Status": "enabled"
    })

    st.download_button(
        "Download Smart Bid Bulk",
        smart_bulk.to_csv(index=False),
        "smart_bid_bulk.csv"
    )

    # ============================================================
    # SKU ANALYSIS
    # ============================================================

    if "sku" in df.columns:

        st.subheader("📦 SKU Intelligence")

        sku_df = df.groupby("sku").agg(
            Spend=("spend", "sum"),
            Sales=("sales", "sum"),
            Avg_UIS=("uis", "mean")
        ).reset_index()

        sku_df["ROAS"] = safe_div(sku_df["Sales"], sku_df["Spend"])

        st.dataframe(sku_df.round(2))

else:
    st.info("Upload a search term report to begin.")
