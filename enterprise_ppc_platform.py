# ============================================================
# PPC TOOL LAR – ENTERPRISE MODE (SP | INR)
# Full Restore + True TACOS + Waste Engine + SKU Fix
# Nothing Removed • Fully Stable • Bulk Ready
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="PPC TOOL LAR", layout="wide")
st.title("🚀 PPC TOOL LAR – Enterprise Mode")

# ============================================================
# SAFE FUNCTIONS
# ============================================================

def safe_div(a, b):
    if isinstance(a, pd.Series):
        return np.where(b != 0, a / b, 0)
    return a / b if b != 0 else 0

def find_column(df, keywords):
    for col in df.columns:
        for key in keywords:
            if key in col.lower():
                return col
    return None

# ============================================================
# FILE UPLOAD
# ============================================================

uploaded = st.file_uploader("Upload Sponsored Products Search Term Report", type=["csv", "xlsx"])

if uploaded:

    df = pd.read_excel(uploaded) if uploaded.name.endswith("xlsx") else pd.read_csv(uploaded)
    df.columns = df.columns.str.lower().str.strip()

    # ============================================================
    # AUTO COLUMN MAP
    # ============================================================

    col_map = {
        "search_term": find_column(df, ["search term"]),
        "campaign": find_column(df, ["campaign"]),
        "ad_group": find_column(df, ["ad group"]),
        "spend": find_column(df, ["spend"]),
        "sales": find_column(df, ["sales"]),
        "orders": find_column(df, ["order"]),
        "clicks": find_column(df, ["click"]),
        "impressions": find_column(df, ["impression"]),
        "sku": find_column(df, ["sku"]),
    }

    for k, v in col_map.items():
        df[k] = df[v] if v else 0

    df.fillna(0, inplace=True)

    # ============================================================
    # CORE METRICS
    # ============================================================

    df["cpc"] = safe_div(df["spend"], df["clicks"])
    df["ctr"] = safe_div(df["clicks"], df["impressions"]) * 100
    df["cvr"] = safe_div(df["orders"], df["clicks"]) * 100
    df["roas"] = safe_div(df["sales"], df["spend"])
    df["acos"] = safe_div(df["spend"], df["sales"]) * 100

    total_spend = df["spend"].sum()
    total_sales = df["sales"].sum()

    # ============================================================
    # PROFIT SETTINGS
    # ============================================================

    st.sidebar.header("💰 Profit Settings")
    margin = st.sidebar.slider("Margin %", 10, 80, 40)
    total_revenue = st.sidebar.number_input("Total Store Revenue (For TACOS)", value=float(total_sales))

    break_even_roas = 1 / (margin / 100)
    tacos = safe_div(total_spend, total_revenue) * 100

    # ============================================================
    # WASTE ENGINE
    # ============================================================

    df["hard_waste"] = np.where((df["orders"] == 0) & (df["spend"] > 100), df["spend"], 0)
    df["soft_waste"] = np.where(df["acos"] > 60, df["spend"], 0)
    df["profit_risk"] = np.where(df["roas"] < break_even_roas, 1, 0)

    total_hard_waste = df["hard_waste"].sum()

    # ============================================================
    # INTELLIGENCE SCORE (UIS)
    # ============================================================

    avg_roas = df["roas"].mean()
    avg_cvr = df["cvr"].mean()

    df["uis"] = (
        (safe_div(df["roas"], break_even_roas) * 40) +
        (safe_div(df["cvr"], avg_cvr) * 30) -
        (df["profit_risk"] * 20)
    ).clip(0, 100)

    # ============================================================
    # SMART BID ENGINE
    # ============================================================

    df["smart_bid"] = np.where(df["uis"] > 80, df["cpc"] * 1.25,
                        np.where(df["uis"] > 60, df["cpc"] * 1.15,
                        np.where(df["uis"] > 40, df["cpc"],
                        df["cpc"] * 0.85)))

    # ============================================================
    # CLUSTER ENGINE
    # ============================================================

    df["cluster"] = df["search_term"].astype(str).apply(lambda x: " ".join(x.split()[:2]))

    # ============================================================
    # DASHBOARD METRICS
    # ============================================================

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("Spend (₹)", f"₹ {total_spend:,.2f}")
    c2.metric("Sales (₹)", f"₹ {total_sales:,.2f}")
    c3.metric("ROAS", round(safe_div(total_sales, total_spend), 2))
    c4.metric("ACOS %", round(safe_div(total_spend, total_sales) * 100, 2))
    c5.metric("Hard Waste (₹)", f"₹ {total_hard_waste:,.2f}")
    c6.metric("TACOS %", round(tacos, 2))

    # ============================================================
    # KEYWORD INTELLIGENCE TABLE
    # ============================================================

    st.subheader("📊 Keyword Intelligence")

    st.dataframe(
        df[[
            "search_term", "campaign", "spend", "sales", "roas",
            "acos", "cvr", "uis", "smart_bid", "cluster"
        ]].round(2)
    )

    # ============================================================
    # NEGATIVE CANDIDATES (Keyword View)
    # ============================================================

    st.subheader("🚫 Negative Keyword Candidates (Keyword View)")

    negatives = df[df["hard_waste"] > 0]
    st.dataframe(negatives[["search_term", "campaign", "spend", "orders"]])

    # Amazon Bulk Format (Campaign Wise)
    negative_bulk = pd.DataFrame({
        "Record Type": "Negative Keyword",
        "Campaign Name": negatives["campaign"],
        "Ad Group Name": negatives["ad_group"],
        "Keyword or Product Targeting": negatives["search_term"],
        "Match Type": "Negative Exact",
        "Status": "enabled"
    })

    st.download_button(
        "Download Negative Bulk File",
        negative_bulk.to_csv(index=False),
        "negative_bulk.csv"
    )

    # ============================================================
    # ISOLATION CAMPAIGN CREATOR
    # ============================================================

    st.subheader("🚀 High Performing Isolation Campaigns")

    high_perf = df[df["uis"] > 85]

    isolation_bulk = pd.DataFrame({
        "Record Type": "Keyword",
        "Campaign Name": high_perf["search_term"].str[:40] + "_Exact",
        "Ad Group Name": high_perf["search_term"].str[:40],
        "Keyword or Product Targeting": high_perf["search_term"],
        "Match Type": "Exact",
        "Bid": high_perf["smart_bid"].round(2),
        "Status": "enabled"
    })

    st.dataframe(high_perf[["search_term", "roas", "uis"]])

    st.download_button(
        "Download Isolation Campaign Bulk",
        isolation_bulk.to_csv(index=False),
        "isolation_campaign_bulk.csv"
    )

    # ============================================================
    # SKU INTELLIGENCE (FIXED ERROR)
    # ============================================================

    if col_map["sku"]:
        st.subheader("📦 SKU Intelligence")

        sku_df = df.groupby("sku").agg(
            Spend=("spend", "sum"),
            Sales=("sales", "sum"),
        ).reset_index()

        sku_df["ROAS"] = np.where(sku_df["Spend"] != 0,
                                  sku_df["Sales"] / sku_df["Spend"], 0)

        st.dataframe(sku_df.round(2))

else:
    st.info("Upload Sponsored Products Search Term Report to start.")
