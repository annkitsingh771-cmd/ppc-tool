# ============================================================
# PPC TOOL LAR – ENTERPRISE MODE (STABLE POLISHED VERSION)
# Sponsored Products | INR | Multi Account | Full Tabs
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="PPC TOOL LAR", layout="wide")
st.title("🚀 PPC TOOL LAR – Enterprise Mode")

# ============================================================
# SESSION: MULTI ACCOUNT SYSTEM
# ============================================================

if "accounts" not in st.session_state:
    st.session_state.accounts = {}

if "current_account" not in st.session_state:
    st.session_state.current_account = None

st.sidebar.header("🏢 Multi-Account Manager")

acc_name = st.sidebar.text_input("Account Name")
file_upload = st.sidebar.file_uploader("Upload SP Search Term Report", type=["csv","xlsx"])

if st.sidebar.button("Add Account"):
    if acc_name and file_upload:
        df_new = pd.read_excel(file_upload) if file_upload.name.endswith("xlsx") else pd.read_csv(file_upload)
        st.session_state.accounts[acc_name] = df_new
        st.session_state.current_account = acc_name
        st.sidebar.success("Account Added")

if st.session_state.accounts:
    selected = st.sidebar.selectbox("Select Account", list(st.session_state.accounts.keys()))
    st.session_state.current_account = selected

# ============================================================
# HELPER FUNCTIONS
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
# MAIN ENGINE
# ============================================================

if st.session_state.current_account:

    df = st.session_state.accounts[st.session_state.current_account].copy()
    df.columns = df.columns.str.lower().str.strip()

    # ---------------- SMART SP COLUMN MAPPING ----------------

    mapping = {
        "search_term": find_column(df, ["customer search term","search term"]),
        "campaign": find_column(df, ["campaign name"]),
        "ad_group": find_column(df, ["ad group name"]),
        "spend": find_column(df, ["spend"]),
        "sales": find_column(df, ["7 day total sales"]),
        "orders": find_column(df, ["7 day total orders"]),
        "clicks": find_column(df, ["click"]),
        "impressions": find_column(df, ["impression"]),
    }

    for k,v in mapping.items():
        if v:
            df[k] = df[v]
        else:
            df[k] = 0

    # SKU FIX
    sku_col = find_column(df, ["advertised sku","advertised asin","sku"])
    if sku_col:
        df["sku"] = df[sku_col].astype(str)
    else:
        df["sku"] = "Unknown"

    df.fillna(0, inplace=True)

    # ---------------- CORE METRICS ----------------

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

    # ---------------- PROFIT SETTINGS ----------------

    st.sidebar.header("💰 Profit Settings")
    margin = st.sidebar.slider("Margin %", 10, 80, 40)
    total_revenue = st.sidebar.number_input(
        "Total Revenue (For TACOS)",
        value=float(df["sales"].sum())
    )

    break_even_roas = 1 / (margin / 100)
    tacos = safe_div(df["spend"].sum(), total_revenue) * 100

    # ---------------- UIS SCORE ----------------

    avg_roas = df["roas"].mean()
    avg_cvr = df["cvr"].mean()

    df["uis"] = (
        (safe_div(df["roas"], break_even_roas) * 40) +
        (safe_div(df["cvr"], avg_cvr) * 30)
    ).clip(0,100)

    # ---------------- SMART BID ----------------

    df["smart_bid"] = np.where(df["uis"] > 80, df["cpc"] * 1.25,
                        np.where(df["uis"] > 60, df["cpc"] * 1.15,
                        np.where(df["uis"] > 40, df["cpc"],
                        df["cpc"] * 0.85)))

    # ---------------- CLUSTER ----------------

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
        "Simulation + SKU"
    ])

    # ---------------- OVERVIEW ----------------

    with tab1:

        total_spend = float(df["spend"].sum())
        total_sales = float(df["sales"].sum())
        total_orders = int(df["orders"].sum())

        total_roas = safe_div(total_sales, total_spend)
        total_acos = safe_div(total_spend, total_sales) * 100
        total_waste = float(df["hard_waste"].sum())

        c1,c2,c3,c4,c5,c6 = st.columns(6)

        c1.metric("Spend ₹", f"₹ {total_spend:,.2f}")
        c2.metric("Sales ₹", f"₹ {total_sales:,.2f}")
        c3.metric("Orders", total_orders)
        c4.metric("ROAS", f"{total_roas:.2f}")
        c5.metric("ACOS %", f"{total_acos:.2f}%")
        c6.metric("Hard Waste ₹", f"₹ {total_waste:,.2f}")

        st.metric("TACOS %", f"{tacos:.2f}%")

    # ---------------- KEYWORD INTELLIGENCE ----------------

    with tab2:

        st.dataframe(
            df[[
                "search_term","campaign","ad_group","spend",
                "sales","orders","roas","acos","cvr",
                "uis","smart_bid","cluster"
            ]].round(2)
        )

        st.download_button(
            "Download Full Keyword Intelligence",
            df.to_csv(index=False),
            "keyword_intelligence.csv"
        )

    # ---------------- NEGATIVE ENGINE ----------------

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

    # ---------------- CAMPAIGN BUILDER ----------------

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

    # ---------------- PORTFOLIO ----------------

    with tab5:

        camp = df.groupby("campaign").agg(
            Spend=("spend","sum"),
            Sales=("sales","sum"),
            Orders=("orders","sum")
        ).reset_index()

        camp["ROAS"] = safe_div(camp["Sales"], camp["Spend"])

        st.dataframe(camp.round(2))

    # ---------------- SIMULATION + SKU ----------------

    with tab6:

        add_budget = st.number_input("Add Extra Budget ₹", value=10000)

        if add_budget > 0:
            camp_sim = df.groupby("campaign").agg(
                Spend=("spend","sum"),
                UIS=("uis","mean")
            ).reset_index()

            weight = camp_sim["UIS"] / camp_sim["UIS"].sum()
            camp_sim["Allocated Budget"] = weight * add_budget

            st.dataframe(camp_sim.round(2))

        st.subheader("SKU Intelligence")

        sku_df = df.groupby("sku").agg(
            Spend=("spend","sum"),
            Sales=("sales","sum"),
            Orders=("orders","sum")
        ).reset_index()

        sku_df["ROAS"] = safe_div(sku_df["Sales"], sku_df["Spend"])

        st.dataframe(sku_df.round(2))

else:
    st.info("Add and select an account to start.")
