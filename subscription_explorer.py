
import streamlit as st
import pandas as pd
import altair as alt

# Load data (assumes CSV in same directory or deployed with Streamlit Cloud)
@st.cache_data
def load_data():
    return pd.read_csv("newboshhhsubscriptioncategory.csv")

df = load_data()
# Clean category names for display
df['boshh_subscription_category'] = df['boshh_subscription_category'].str.replace(r'^Subscription\s*[-–]\s*', '', regex=True)
st.title("📦 Subscription Explorer – Boshhh")
st.markdown("""
Explore subscription transactions detected in open banking data. Filter by category or merchant to analyse volume, spending patterns, and descriptions.
""")

# --- Sidebar filters ---
category_filter = st.sidebar.multiselect(
    "Filter by Subscription Category:", 
    sorted(df['boshh_subscription_category'].dropna().unique()),
    default=None
)

merchant_filter = st.sidebar.multiselect(
    "Filter by Merchant:", 
    sorted(df['enrichment_merchant_name'].dropna().unique()),
    default=None
)

min_amt, max_amt = st.sidebar.slider(
    "Transaction Amount Range:", 
    float(df['transaction_amount'].min()), 
    float(df['transaction_amount'].max()), 
    (float(df['transaction_amount'].min()), float(df['transaction_amount'].max()))
)

# --- Apply filters ---
df_filtered = df.copy()
if category_filter:
    df_filtered = df_filtered[df_filtered['boshh_subscription_category'].isin(category_filter)]
if merchant_filter:
    df_filtered = df_filtered[df_filtered['enrichment_merchant_name'].isin(merchant_filter)]
df_filtered = df_filtered[(df_filtered['transaction_amount'] >= min_amt) & (df_filtered['transaction_amount'] <= max_amt)]

# --- Charts ---
st.subheader("📊 Volume of Subscriptions by Category")
volume_chart = (
    alt.Chart(df_filtered)
    .mark_bar()
    .encode(
        x=alt.X("boshh_subscription_category:N", title="Subscription Category", sort="-y"),
        y=alt.Y("count():Q", title="Number of Transactions"),
        tooltip=["boshh_subscription_category", "count():Q"]
    )
    .properties(width=700)
)
st.altair_chart(volume_chart, use_container_width=True)

st.subheader("💷 Average Spend by Category")
avg_chart = (
    alt.Chart(df_filtered)
    .mark_line(point=True)
    .encode(
        x=alt.X("boshh_subscription_category:N", sort="-y", title="Subscription Category"),
        y=alt.Y("mean(transaction_amount):Q", title="Avg. Transaction Amount (GBP)"),
        tooltip=["boshh_subscription_category", "mean(transaction_amount):Q"]
    )
    .properties(width=700)
)
st.altair_chart(avg_chart, use_container_width=True)

# --- Table of transactions ---
st.subheader("📋 Filtered Transactions")
st.dataframe(df_filtered.sort_values("date", ascending=False).reset_index(drop=True))

# --- Per-user breakdown ---
st.subheader("🔍 Explore Individual User Subscriptions")
user_sub_counts = df_filtered.groupby('user_id')['boshh_subscription_category'].nunique().reset_index()
user_sub_counts = user_sub_counts[user_sub_counts['boshh_subscription_category'] > 3]
eligible_users = user_sub_counts['user_id'].tolist()

if eligible_users:
    selected_user = st.selectbox("Select a user with more than 3 subscriptions:", eligible_users)

    user_df = df_filtered[df_filtered['user_id'] == selected_user]
    pie_df = user_df['boshh_subscription_category'].value_counts().reset_index()
    pie_df.columns = ['Subscription Category', 'Count']

    st.markdown(f"### 📈 Subscription Breakdown for User: `{selected_user}`")

    pie_chart = alt.Chart(pie_df).mark_arc(innerRadius=40).encode(
        theta="Count:Q",
        color="Subscription Category:N",
        tooltip=["Subscription Category", "Count"]
    ).properties(width=400, height=400)

    st.altair_chart(pie_chart, use_container_width=False)

    st.markdown("#### 📋 Subscriptions List")
    st.dataframe(user_df[['date', 'transaction_amount', 'enrichment_merchant_name', 'boshh_subscription_category', 'description']].sort_values("date", ascending=False))
else:
    st.warning("No users found with more than 3 subscription categories.")
