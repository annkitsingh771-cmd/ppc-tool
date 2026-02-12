# ============================================================
# ENTERPRISE AMAZON PPC PLATFORM (FINAL SIMPLIFIED VERSION)
# Unified Intelligence • Profit Driven • Multi Account Ready
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np

# ============================================================
# PAGE CONFIG + DARK STYLE
# ============================================================

st.set_page_config(page_title="Enterprise PPC Platform", layout="wide")

st.markdown("""
<style>
body {background-color: #0E1117; color: white;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 Enterprise Amazon PPC Platform")

# ============================================================
# SESSION MULTI ACCOUNT SYSTEM
# ============================================================

if "accounts" not in st.session_state:
    st.session_state.accounts = {}

if "current_account" not in st.session_state:
    st.session_state.current_account = None

st.sidebar.header("🏢 Account Manager")

acc_name = st.sidebar.text_input("Account Name")
file_upload = st.sidebar.file_uploader("Upload Search Term Report", type=["csv","xlsx"])

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

def safe_div(a,b):
    return a/b if b!=0 else 0

def find_col(df, keys):
    for k in keys:
        for c in df.columns:
            if k in c.lower():
                return c
    return None

# ============================================================
# MAIN ENGINE
# ============================================================

if st.session_state.current_account:

    df = st.session_state.accounts[st.session_state.current_account].copy()
    df.columns = df.columns.str.lower().str.strip()

    # ---------------- COLUMN STANDARDIZATION ----------------

    mapping = {
        "search_term":["search term"],
        "campaign":["campaign"],
        "ad_group":["ad group"],
        "spend":["spend"],
        "sales":["sales"],
        "orders":["orders"],
        "clicks":["clicks"],
        "impressions":["impressions"],
        "sku":["sku"]
    }

    for std,keys in mapping.items():
        col = find_col(df,keys)
        df[std] = df[col] if col else 0

    df.fillna(0,inplace=True)

    # ---------------- CORE METRICS ----------------

    df["cpc"] = df.apply(lambda r: safe_div(r["spend"],r["clicks"]),axis=1)
    df["ctr"] = df.apply(lambda r: safe_div(r["clicks"],r["impressions"])*100,axis=1)
    df["cvr"] = df.apply(lambda r: safe_div(r["orders"],r["clicks"])*100,axis=1)
    df["roas"] = df.apply(lambda r: safe_div(r["sales"],r["spend"]),axis=1)
    df["acos"] = df.apply(lambda r: safe_div(r["spend"],r["sales"])*100,axis=1)

    avg_cvr = df["cvr"].mean()
    avg_ctr = df["ctr"].mean()
    avg_roas = df["roas"].mean()
    avg_cpc = df["cpc"].mean()

    # ---------------- PROFIT SETTINGS ----------------

    st.sidebar.header("💰 Profit Settings")
    margin = st.sidebar.number_input("Margin %", min_value=1, max_value=90, value=40)
    break_even_roas = 1/(margin/100)

    df["profit_status"] = np.where(df["roas"]>=break_even_roas,"Profitable","Loss Risk")

    # ---------------- COMPETITOR PRESSURE ----------------

    def pressure(r):
        score=0
        if r["cpc"]>avg_cpc: score+=30
        if r["roas"]<avg_roas: score+=30
        if r["ctr"]<avg_ctr: score+=20
        if r["orders"]==0 and r["spend"]>avg_cpc*5: score+=20
        return min(score,100)

    df["pressure_score"] = df.apply(pressure,axis=1)

    # ---------------- UNIFIED INTELLIGENCE SCORE ----------------

    def uis(r):
        roas_factor=(r["roas"]/(break_even_roas+0.01))*30
        cvr_factor=(r["cvr"]/(avg_cvr+0.01))*25
        ctr_factor=(r["ctr"]/(avg_ctr+0.01))*15
        cpc_factor=(avg_cpc/(r["cpc"]+0.01))*15
        penalty=(r["pressure_score"]/100)*20
        score=roas_factor+cvr_factor+ctr_factor+cpc_factor-penalty
        return max(0,min(100,score))

    df["uis"]=df.apply(uis,axis=1)

    # ---------------- SMART BID ENGINE ----------------

    def smart_bid(r):
        if r["uis"]>=80: return r["cpc"]*1.25
        elif r["uis"]>=60: return r["cpc"]*1.15
        elif r["uis"]>=40: return r["cpc"]
        elif r["uis"]>=20: return r["cpc"]*0.9
        else: return r["cpc"]*0.8

    df["smart_bid"]=df.apply(smart_bid,axis=1)

    # ---------------- CLUSTER + INTENT ----------------

    df["cluster"]=df["search_term"].astype(str).apply(lambda x:" ".join(x.lower().split()[:2]))
    
    def intent(term):
        t=str(term).lower()
        if any(x in t for x in ["buy","order","price","deal"]): return "Transactional"
        if any(x in t for x in ["best","top","review"]): return "Commercial"
        if any(x in t for x in ["pandora","tanishq","voylla"]): return "Competitor"
        if any(x in t for x in ["how","guide","meaning"]): return "Research"
        return "Generic"

    df["intent"]=df["search_term"].apply(intent)

    # ============================================================
    # TABS
    # ============================================================

    tab1,tab2,tab3,tab4,tab5,tab6=st.tabs([
        "Overview",
        "Keyword Intelligence",
        "Scaling & Optimization",
        "Campaign Builder",
        "Portfolio",
        "Simulation + SKU"
    ])

    # ---------------- OVERVIEW ----------------

    with tab1:
        c1,c2,c3,c4,c5,c6=st.columns(6)
        c1.metric("Spend",round(df["spend"].sum(),2))
        c2.metric("Sales",round(df["sales"].sum(),2))
        c3.metric("ROAS",round(avg_roas,2))
        c4.metric("CVR%",round(avg_cvr,2))
        c5.metric("BreakEven ROAS",round(break_even_roas,2))
        c6.metric("Avg UIS",round(df["uis"].mean(),2))

    # ---------------- KEYWORD INTELLIGENCE ----------------

    with tab2:
        st.dataframe(df[[
            "search_term","campaign","spend","sales","orders",
            "roas","cvr","uis","smart_bid","intent","cluster"
        ]].round(2))
        st.download_button("Download Full Intelligence",df.to_csv(index=False),"full_intelligence.csv")

    # ---------------- SCALING ----------------

    with tab3:
        high=df[df["uis"]>=70]
        low=df[df["uis"]<30]
        st.subheader("High Scale Keywords")
        st.dataframe(high)
        st.subheader("Negative Candidates")
        st.dataframe(low)

        st.download_button(
            "Download Smart Bid File",
            pd.DataFrame({
                "Record Type":"Keyword",
                "Campaign Name":df["campaign"],
                "Ad Group Name":df["ad_group"],
                "Keyword or Product Targeting":df["search_term"],
                "Match Type":"Exact",
                "Bid":df["smart_bid"].round(2),
                "Status":"enabled"
            }).to_csv(index=False),
            "smart_bid_bulk.csv"
        )

    # ---------------- CAMPAIGN BUILDER ----------------

    with tab4:
        isolate=df[df["uis"]>=80]
        st.dataframe(isolate)
        st.download_button(
            "Download Isolation Campaigns",
            pd.DataFrame({
                "Record Type":"Keyword",
                "Campaign Name":isolate["search_term"].str[:40]+"_Exact",
                "Ad Group Name":isolate["search_term"].str[:40],
                "Keyword or Product Targeting":isolate["search_term"],
                "Match Type":"Exact",
                "Bid":isolate["smart_bid"].round(2),
                "Status":"enabled"
            }).to_csv(index=False),
            "isolation_campaign.csv"
        )

    # ---------------- PORTFOLIO ----------------

    with tab5:
        camp=df.groupby("campaign").agg(
            Spend=("spend","sum"),
            Sales=("sales","sum"),
            Avg_UIS=("uis","mean")
        ).reset_index()
        camp["ROAS"]=camp["Sales"]/camp["Spend"].replace(0,1)
        st.dataframe(camp.round(2))
        st.download_button("Download Portfolio",camp.to_csv(index=False),"portfolio.csv")

    # ---------------- SIMULATION + SKU ----------------

    with tab6:
        add_budget=st.number_input("Additional Budget",value=10000)
        if add_budget>0:
            camp_sim=df.groupby("campaign").agg(
                Spend=("spend","sum"),
                Sales=("sales","sum"),
                Avg_UIS=("uis","mean"),
                Avg_CPC=("cpc","mean"),
                Avg_CVR=("cvr","mean")
            ).reset_index()

            weight=camp_sim["Avg_UIS"]/camp_sim["Avg_UIS"].sum()
            camp_sim["Allocated"]=weight*add_budget
            camp_sim["NewSpend"]=camp_sim["Spend"]+camp_sim["Allocated"]
            camp_sim["ProjectedClicks"]=camp_sim["NewSpend"]/camp_sim["Avg_CPC"].replace(0,1)
            camp_sim["ProjectedOrders"]=camp_sim["ProjectedClicks"]*(camp_sim["Avg_CVR"]/100)
            st.dataframe(camp_sim.round(2))

        if "sku" in df.columns:
            sku=df.groupby("sku").agg(
                Spend=("spend","sum"),
                Sales=("sales","sum"),
                Avg_UIS=("uis","mean")
            ).reset_index()
            sku["ROAS"]=sku["Sales"]/sku["Spend"].replace(0,1)
            st.subheader("SKU Intelligence")
            st.dataframe(sku.round(2))

else:
    st.info("Add and select an account to start.")
