import streamlit as st
import pandas as pd
import plotly.express as px
import anthropic
from fpdf import FPDF
import io

from dotenv import load_dotenv
load_dotenv()


# Initialise chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""



st.set_page_config(page_title="Car Sales Dashboard", layout="wide")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
else:
    df = pd.read_excel("car_sales_full_year_realistic_10000.xlsx")
# Scenario selector
st.sidebar.title("Filters")

markets = st.sidebar.multiselect(
    "Select Market",
    options=sorted(df["market"].dropna().unique()),
    default=sorted(df["market"].dropna().unique())
)

channels = st.sidebar.multiselect(
    "Select Sales Channel",
    options=sorted(df["sales_channel"].dropna().unique()),
    default=sorted(df["sales_channel"].dropna().unique())
)

scenario = st.sidebar.selectbox(
    "Scenario",
    ["Normal (0%)", "Optimistic (+20%)", "Pessimistic (-20%)"]
)

# Filter data
df_filtered = df[
    (df["market"].isin(markets)) &
    (df["sales_channel"].isin(channels))
].copy()

# Scenario logic
multiplier = 1.0
if scenario == "Optimistic (+20%)":
    multiplier = 1.2
elif scenario == "Pessimistic (-20%)":
    multiplier = 0.8

# Next-year scenario assumptions:
# - sales and variable costs move with volume
# - fixed overhead stays constant
df_filtered["scenario_sales_eur"] = df_filtered["net_sales_eur"] * multiplier
df_filtered["scenario_variable_cost_eur"] = df_filtered["total_variable_cost_eur"] * multiplier
df_filtered["scenario_gross_profit_eur"] = (
    df_filtered["scenario_sales_eur"] - df_filtered["scenario_variable_cost_eur"]
)
df_filtered["scenario_operating_profit_eur"] = (
    df_filtered["scenario_gross_profit_eur"] - df_filtered["allocated_fixed_overhead_eur"]
)

# KPI calculations
total_sales = df_filtered["scenario_sales_eur"].sum()
total_units = df_filtered["units_sold"].sum() * multiplier
gross_profit = df_filtered["scenario_gross_profit_eur"].sum()
operating_profit = df_filtered["scenario_operating_profit_eur"].sum()
gross_margin = gross_profit / total_sales if total_sales != 0 else 0
operating_margin = operating_profit / total_sales if total_sales != 0 else 0

# Title
st.title("🚗 Car Sales Dashboard")
st.markdown(f"### Scenario: {scenario}")

# KPI cards
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Sales (€)", f"{total_sales:,.0f}")
col2.metric("Units", f"{total_units:,.0f}")
col3.metric("Gross Profit (€)", f"{gross_profit:,.0f}")
col4.metric("Operating Profit (€)", f"{operating_profit:,.0f}")
col5.metric("Operating Margin", f"{operating_margin:.2%}")

# Monthly trends
month_order = list(range(1, 13))
monthly = (
    df_filtered.groupby("month")[["scenario_sales_eur", "scenario_operating_profit_eur"]]
    .sum()
    .reindex(month_order, fill_value=0)
    .reset_index()
)

left, right = st.columns(2)

with left:
    fig_sales = px.line(
        monthly,
        x="month",
        y="scenario_sales_eur",
        title="Monthly Sales Trend"
    )
    st.plotly_chart(fig_sales, use_container_width=True)

with right:
    fig_profit = px.line(
        monthly,
        x="month",
        y="scenario_operating_profit_eur",
        title="Monthly Operating Profit Trend"
    )
    st.plotly_chart(fig_profit, use_container_width=True)

# Market analysis
market_sales = (
    df_filtered.groupby("market")["scenario_sales_eur"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

channel_sales = (
    df_filtered.groupby("sales_channel")["scenario_sales_eur"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

left2, right2 = st.columns(2)

with left2:
    fig_market = px.bar(
        market_sales,
        x="market",
        y="scenario_sales_eur",
        title="Sales by Market"
    )
    st.plotly_chart(fig_market, use_container_width=True)

with right2:
    fig_channel = px.bar(
        channel_sales,
        x="sales_channel",
        y="scenario_sales_eur",
        title="Sales by Sales Channel"
    )
    st.plotly_chart(fig_channel, use_container_width=True)

# Top models
top_models = (
    df_filtered.groupby("model_name")["scenario_sales_eur"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig_models = px.bar(
    top_models,
    x="model_name",
    y="scenario_sales_eur",
    title="Top 10 Models by Sales"
)
st.plotly_chart(fig_models, use_container_width=True)

# Data preview
st.subheader("AI Finance Assistant")

style = st.selectbox(
    "Commentary Style",
    ["Executive (3 sentences)", "Detailed Analysis", "Action-focused"]
)

# Build system prompt based on style
if style == "Executive (3 sentences)":
    system_prompt = """You are a CFO presenting to a board.
Write exactly 3 sentences. Be direct. Lead with the bottom line.
You have access to the current dashboard data provided by the user."""

elif style == "Detailed Analysis":
    system_prompt = """You are a senior FP&A analyst writing for a management team.
Write 5-6 sentences covering revenue, costs, margin, and root cause analysis.
You have access to the current dashboard data provided by the user."""

else:
    system_prompt = """You are a management consultant presenting findings.
Keep responses under 60 words.
Structure: one sentence on what happened, then 2-3 bullet point actions.
You have access to the current dashboard data provided by the user."""

# Data context to inject into first message
data_context = f"""
<data>
Scenario: {scenario}
Total Sales: €{total_sales:,.0f}
Total Units: {total_units:,.0f}
Gross Profit: €{gross_profit:,.0f}
Operating Profit: €{operating_profit:,.0f}
Operating Margin: {operating_margin:.2%}
</data>
"""

# Reset chat if style changes
if system_prompt != st.session_state.system_prompt:
    st.session_state.messages = []
    st.session_state.system_prompt = system_prompt

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
user_input = st.chat_input("Ask about the financial data...")

if user_input:
    # Add data context to first message only
    if len(st.session_state.messages) == 0:
        full_input = f"{data_context}\n\n{user_input}"
    else:
        full_input = user_input

    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": full_input
    })

    # Display user message
    with st.chat_message("user"):
        st.write(user_input)

    # Call Claude with full history
    client = anthropic.Anthropic()

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                temperature=0,
                system=system_prompt,
                messages=st.session_state.messages
            )
        response = message.content[0].text
        st.write(response)

    # Add assistant response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

# Clear chat button
if len(st.session_state.messages) > 0:
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()