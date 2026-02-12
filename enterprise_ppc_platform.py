# ============================================================
# PPC TOOL LAR – ENTERPRISE MODE (STABLE VERSION)
# SP Search Term + Purchased Product Report
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="PPC TOOL LAR", layout="wide")
st.title("🚀 PPC TOOL LAR – Enterprise Mode")

# ============================================================
# HELPER
# ============================================================

def safe_div(a, b):
    if isinstance(a, pd.Series):
        return np.where(b != 0, a / b, 0)
    return a / b if b != 0 else 0

# ============================================================
# FILE UPLOADS
# ============================================================

st.sidebar.header("Upload Reports")

search_file = st.sidebar.file_uploader(
    "Upload Search Term Report",
    type=["csv","xlsx"]
)

purchased_file = st.sidebar.file_uploader(
    "Upload Purchased Product Report (For SKU)",
    type=["csv","xlsx"]
)

if search_file:

    # ============================================================
    # LOAD SEARCH TERM REPORT
    # ============================================================

    df = pd.read_excel(search_file) if search_file.name.endswith("xlsx") else pd.read_csv(search_file)

    # Exact mapping based on your real file
    df["search_term"] = df["Customer Search Term"]
    df["campaign"] = df["Campaign Name"]
    df["ad_group"] = df["Ad Group Name"]
    df["spend"] = df["Spend"]
    df["sales"] = df["7 Day Total Sales (₹)"]
    df["orders"] = df["7 Day Total Orders (#)"]
    df["clicks"] = df["Clicks"]
    df["impressions"] = df["Impressions"]

    df.fillna(0, inplace=True)

    # ============================================================
    # METRICS
    # ============================================================

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

    # ============================================================
    # PROFIT SETTINGS
    # ============================================================

    st.sidebar.header("Profit Settings")
    margin = st.sidebar.slider("Margin %", 10, 80, 40)
    total_revenue = st.sidebar.number_input(
        "Total Revenue (For TACOS)",
        value=float(df["sales"].sum())
    )

    break_even_roas = 1 / (margin / 100)
    tacos = safe_div(df["spend"].sum(), total_revenue) * 100

    # ============================================================
    # UIS SCORE
    # ============================================================

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

    df["cluster"] = df["search_term"].astype(str).apply(lambda x: " ".join(x.split()[:2]))

    # ============================================================
    # TABS
    # ============================================================

    tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
        "Overview",
        "Keyword Intelligence",
        "Negative Engine",
        "Campaign Builder",
        "Portfolio",
        "SKU Intelligence"
    ])

    # ============================================================
    # OVERVIEW
    # ============================================================

    with tab1:

        total_spend = float(df["spend"].sum())
        total_sales = float(df["sales"].sum())
        total_orders = int(df["orders"].sum())
        total_roas = safe_div(total_sales, total_spend)
        total_acos = safe_div(total_spend, total_sales) * 100
        total_waste = float(df["hard_waste"].sum())

        overview = pd.DataFrame({
            "Metric":[
                "Spend ₹","Sales ₹","Orders",
                "ROAS","ACOS %","Hard Waste ₹","TACOS %"
            ],
            "Value":[
                f"₹ {total_spend:,.2f}",
                f"₹ {total_sales:,.2f}",
                total_orders,
                f"{total_roas:.2f}",
                f"{total_acos:.2f}%",
                f"₹ {total_waste:,.2f}",
                f"{tacos:.2f}%"
            ]
        })

        st.table(overview)

    # ============================================================
    # KEYWORD INTELLIGENCE
    # ============================================================

    with tab2:

        st.dataframe(
            df[[
                "search_term","campaign","ad_group","spend",
                "sales","orders","roas","acos",
                "cvr","uis","smart_bid","cluster"
            ]].round(2)
        )

        st.download_button(
            "Download Keyword Intelligence",
            df.to_csv(index=False),
            "keyword_intelligence.csv"
        )

    # ============================================================
    # NEGATIVE ENGINE
    # ============================================================

    with tab3:

        negatives = df[df["hard_waste"] > 0]

        st.dataframe(
            negatives[[
                "search_term","campaign","ad_group","spend"
            ]]
        )

        negative_bulk = pd.DataFrame({
            "Record Type":"Negative Keyword",
            "Campaign Name":negatives["campaign"],
            "Ad Group Name":negatives["ad_group"],
            "Keyword Text":negatives["search_term"],
            "Match Type":"Negative Exact",
            "Status":"enabled"
        })

        st.download_button(
            "Download Negative Bulk File",
            negative_bulk.to_csv(index=False),
            "negative_bulk.csv"
        )

    # ============================================================
    # CAMPAIGN BUILDER
    # ============================================================

    with tab4:

        high = df[df["uis"] > 85]

        st.dataframe(high[["search_term","roas","uis"]])

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

        st.download_button(
            "Download Isolation Campaign Bulk",
            isolation_bulk.to_csv(index=False),
            "isolation_campaign_bulk.csv"
        )

    # ============================================================
    # PORTFOLIO
    # ============================================================

    with tab5:

        camp = df.groupby("campaign").agg(
            Spend=("spend","sum"),
            Sales=("sales","sum"),
            Orders=("orders","sum")
        ).reset_index()

        camp["ROAS"] = safe_div(camp["Sales"], camp["Spend"])

        st.dataframe(camp.round(2))

    # ============================================================
    # SKU INTELLIGENCE (Requires Purchased Product Report)
    # ============================================================

    with tab6:

        if purchased_file:

            sku_df = pd.read_excel(purchased_file) if purchased_file.name.endswith("xlsx") else pd.read_csv(purchased_file)

            sku_df["sku"] = sku_df["Advertised SKU"]
            sku_df["sales"] = sku_df["7 Day Advertised SKU Sales (₹)"]
            sku_df["units"] = sku_df["7 Day Advertised SKU Units (#)"]

            sku_summary = sku_df.groupby("sku").agg(
                Sales=("sales","sum"),
                Units=("units","sum")
            ).reset_index()

            st.dataframe(sku_summary.round(2))

        else:
            st.info("Upload Purchased Product Report to see SKU Intelligence.")

else:
    st.info("Upload Search Term Report to begin.")
