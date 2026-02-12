# ============================================================
# PPC TOOL LAR – ENTERPRISE AGENCY VERSION
# Sponsored Products | INR | Monthly Comparison | Client Mode
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="PPC TOOL LAR", layout="wide")
st.title("🚀 PPC TOOL LAR – Enterprise Agency Dashboard")

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_div(a, b):
    if isinstance(a, pd.Series):
        return np.where(b != 0, a / b, 0)
    return a / b if b != 0 else 0

def change_indicator(current, previous):
    if previous == 0:
        return "—"
    change = (current - previous) / previous * 100
    if change > 0:
        return f"🟢 {change:.2f}%"
    elif change < 0:
        return f"🔴 {change:.2f}%"
    else:
        return "0%"

# ============================================================
# FILE UPLOAD
# ============================================================

st.sidebar.header("Upload Reports")

current_file = st.sidebar.file_uploader(
    "Upload Current Month Search Term Report",
    type=["csv","xlsx"]
)

previous_file = st.sidebar.file_uploader(
    "Upload Previous Month Search Term Report",
    type=["csv","xlsx"]
)

# ============================================================
# MAIN ENGINE
# ============================================================

if current_file:

    df = pd.read_excel(current_file) if current_file.name.endswith("xlsx") else pd.read_csv(current_file)

    # Exact mapping (based on your real report)
    df["search_term"] = df["Customer Search Term"]
    df["campaign"] = df["Campaign Name"]
    df["ad_group"] = df["Ad Group Name"]
    df["spend"] = df["Spend"]
    df["sales"] = df["7 Day Total Sales (₹)"]
    df["orders"] = df["7 Day Total Orders (#)"]
    df["clicks"] = df["Clicks"]
    df["impressions"] = df["Impressions"]

    df.fillna(0, inplace=True)

    # ================= METRICS =================

    df["cpc"] = safe_div(df["spend"], df["clicks"])
    df["ctr"] = safe_div(df["clicks"], df["impressions"]) * 100
    df["cvr"] = safe_div(df["orders"], df["clicks"]) * 100
    df["roas"] = safe_div(df["sales"], df["spend"])
    df["acos"] = safe_div(df["spend"], df["sales"]) * 100

    df["hard_waste"] = np.where(
        (df["orders"] == 0) & (df["spend"] > df["cpc"].mean() * 5),
        df["spend"],
        0
    )

    # ================= PROFIT SETTINGS =================

    st.sidebar.header("Profit Settings")
    margin = st.sidebar.slider("Margin %", 10, 80, 40)
    total_revenue = st.sidebar.number_input(
        "Total Revenue (For TACOS)",
        value=float(df["sales"].sum())
    )

    break_even_roas = 1 / (margin / 100)
    tacos = safe_div(df["spend"].sum(), total_revenue) * 100

    # ================= UIS =================

    avg_roas = df["roas"].mean()
    avg_cvr = df["cvr"].mean()

    df["uis"] = (
        (safe_div(df["roas"], break_even_roas) * 40) +
        (safe_div(df["cvr"], avg_cvr) * 30)
    ).clip(0,100)

    df["smart_bid"] = np.where(df["uis"] > 80, df["cpc"] * 1.25,
                        np.where(df["uis"] > 60, df["cpc"] * 1.15,
                        np.where(df["uis"] > 40, df["cpc"],
                        df["cpc"] * 0.85)))

    # ============================================================
    # TABS (STRUCTURE SAME)
    # ============================================================

    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8 = st.tabs([
        "Overview",
        "Keyword Intelligence",
        "Negative Engine",
        "Campaign Builder",
        "Portfolio",
        "Product Intelligence",
        "Client Report",
        "Monthly Comparison"
    ])

    # ============================================================
    # OVERVIEW (UPGRADED)
    # ============================================================

    with tab1:

        total_spend = float(df["spend"].sum())
        total_sales = float(df["sales"].sum())
        total_orders = int(df["orders"].sum())
        total_roas = safe_div(total_sales, total_spend)
        total_acos = safe_div(total_spend, total_sales) * 100
        total_waste = float(df["hard_waste"].sum())
        waste_percent = safe_div(total_waste, total_spend) * 100

        col1,col2,col3,col4 = st.columns(4)

        col1.metric("Spend ₹", f"₹ {total_spend:,.2f}")
        col2.metric("Sales ₹", f"₹ {total_sales:,.2f}")
        col3.metric("ROAS", f"{total_roas:.2f}")
        col4.metric("Waste %", f"{waste_percent:.2f}%")

        st.progress(min(total_roas / break_even_roas, 1.0))

    # ============================================================
    # KEYWORD INTELLIGENCE
    # ============================================================

    with tab2:
        st.dataframe(df.round(2))
        st.download_button("Download Keywords", df.to_csv(index=False), "keywords.csv")

    # ============================================================
    # NEGATIVE ENGINE
    # ============================================================

    with tab3:
        negatives = df[df["hard_waste"] > 0]
        st.dataframe(negatives)
        negative_bulk = pd.DataFrame({
            "Record Type":"Negative Keyword",
            "Campaign Name":negatives["campaign"],
            "Ad Group Name":negatives["ad_group"],
            "Keyword Text":negatives["search_term"],
            "Match Type":"Negative Exact",
            "Status":"enabled"
        })
        st.download_button("Download Negatives", negative_bulk.to_csv(index=False), "negatives.csv")

    # ============================================================
    # CAMPAIGN BUILDER
    # ============================================================

    with tab4:
        high = df[df["uis"] > 85]
        st.dataframe(high)
        isolation_bulk = pd.DataFrame({
            "Record Type":"Keyword",
            "Campaign Name":high["search_term"].str[:40]+"_Exact",
            "Campaign Daily Budget":500,
            "Campaign Start Date":pd.Timestamp.today().strftime("%Y%m%d"),
            "Ad Group Name":high["search_term"].str[:40],
            "Keyword Text":high["search_term"],
            "Match Type":"Exact",
            "Bid":high["smart_bid"].round(2),
            "Status":"enabled"
        })
        st.download_button("Download Isolation Campaign", isolation_bulk.to_csv(index=False), "isolation.csv")

    # ============================================================
    # PORTFOLIO
    # ============================================================

    with tab5:
        camp = df.groupby("campaign").agg(
            Spend=("spend","sum"),
            Sales=("sales","sum")
        ).reset_index()
        camp["ROAS"] = safe_div(camp["Sales"], camp["Spend"])
        st.dataframe(camp.round(2))

    # ============================================================
    # PRODUCT INTELLIGENCE
    # ============================================================

    with tab6:
        product_df = df.groupby("campaign").agg(
            Spend=("spend","sum"),
            Sales=("sales","sum"),
            Waste=("hard_waste","sum")
        ).reset_index()
        product_df["ROAS"] = safe_div(product_df["Sales"], product_df["Spend"])
        product_df["Waste %"] = safe_div(product_df["Waste"], product_df["Spend"]) * 100
        st.dataframe(product_df.round(2))

    # ============================================================
    # CLIENT REPORT
    # ============================================================

    with tab7:
        st.subheader("Client Performance Snapshot")
        st.metric("Total ROAS", f"{total_roas:.2f}")
        st.metric("TACOS %", f"{tacos:.2f}%")

    # ============================================================
    # MONTHLY COMPARISON
    # ============================================================

    with tab8:

        if previous_file:

            prev = pd.read_excel(previous_file) if previous_file.name.endswith("xlsx") else pd.read_csv(previous_file)
            prev_spend = prev["Spend"].sum()
            prev_sales = prev["7 Day Total Sales (₹)"].sum()
            prev_roas = safe_div(prev_sales, prev_spend)

            curr_spend = total_spend
            curr_sales = total_sales
            curr_roas = total_roas

            comparison = pd.DataFrame({
                "Metric":["Spend","Sales","ROAS"],
                "Previous":[prev_spend,prev_sales,prev_roas],
                "Current":[curr_spend,curr_sales,curr_roas],
                "Change":[
                    change_indicator(curr_spend,prev_spend),
                    change_indicator(curr_sales,prev_sales),
                    change_indicator(curr_roas,prev_roas)
                ]
            })

            st.dataframe(comparison)

            st.bar_chart(pd.DataFrame({
                "Spend":[prev_spend,curr_spend],
                "Sales":[prev_sales,curr_sales]
            }, index=["Previous","Current"]))

        else:
            st.info("Upload Previous Month Report for Comparison")

else:
    st.info("Upload Current Month Report to Start")
