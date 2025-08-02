import streamlit as st
import os
import pandas as pd
import calendar
import altair as alt
import time
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from openai import OpenAI
import json
import ast

from src.utils.data_processing import (
    process_credit_transactions,
    process_checking_transactions,
    process_venmo_transactions
)
from src.utils.categorization.credit import categorize_transactions
from src.utils.categorization.checking import (
    checking_to_credit,
    process_income_data,
    process_schwab_data
)
from src.utils.categorization.venmo import (
    add_venmo_info,
    categorize_venmos
)
from src.components.visualizations import (
    display_financial_metrics,
    display_spending_by_category,
    display_monthly_trends,
    display_transaction_table,
    display_category_breakdown
)
from src.components.sidebar import create_sidebar, process_uploaded_files

# Initialize session state variables
if 'processed_credit_df' not in st.session_state:
    st.session_state.processed_credit_df = None
if 'processed_checking_df' not in st.session_state:
    st.session_state.processed_checking_df = None
if 'processed_venmo_df' not in st.session_state:
    st.session_state.processed_venmo_df = None
if 'total_checking_df' not in st.session_state:
    st.session_state.total_checking_df = None
if 'column_info' not in st.session_state:
    st.session_state.column_info = None

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create sidebar and get uploaded files
uploaded_credit, uploaded_checking, uploaded_venmos = create_sidebar()

# Process uploaded files
process_uploaded_files(uploaded_credit, uploaded_checking, uploaded_venmos, client)

# Main content
st.title("Financial Dashboard")

# Create filters
col1, col2 = st.columns(2)
with col1:
    years = ["All Years"] + sorted(st.session_state.processed_credit_df["Year"].unique().tolist() if st.session_state.processed_credit_df is not None else [])
    selected_year = st.selectbox("Select Year", years)
with col2:
    months = ["All Months"] + list(range(1, 13))
    selected_month = st.selectbox("Select Month", months)

# Combine data from different sources
if st.session_state.processed_credit_df is not None:
    # Process credit data
    st.session_state.processed_credit_df = categorize_transactions(st.session_state.processed_credit_df)
    
    # Combine checking and credit data
    if st.session_state.processed_checking_df is not None:
        st.session_state.processed_data = checking_to_credit(
            st.session_state.processed_checking_df,
            st.session_state.processed_credit_df
        )
    else:
        st.session_state.processed_data = st.session_state.processed_credit_df
    
    # Add Venmo data if available
    if st.session_state.processed_venmo_df is not None:
        st.session_state.processed_data = pd.concat(
            [st.session_state.processed_data, st.session_state.processed_venmo_df],
            ignore_index=True
        )
    
    # Process income and Schwab data
    if st.session_state.total_checking_df is not None:
        income_df = process_income_data(st.session_state.total_checking_df)
        schwab_df = process_schwab_data(st.session_state.total_checking_df)
        
        if income_df is not None:
            st.session_state.processed_data = pd.concat(
                [st.session_state.processed_data, income_df],
                ignore_index=True
            )
        
        if schwab_df is not None:
            st.session_state.processed_data = pd.concat(
                [st.session_state.processed_data, schwab_df],
                ignore_index=True
            )

# Display visualizations
if st.session_state.processed_data is not None:
    display_financial_metrics(st.session_state.processed_data, selected_year, selected_month)
    display_spending_by_category(st.session_state.processed_data, selected_year, selected_month)
    display_monthly_trends(st.session_state.processed_data, selected_year)
    
    st.header("Transaction Details")
    display_transaction_table(st.session_state.processed_data, selected_year, selected_month)
    
    st.header("Category Breakdown")
    display_category_breakdown(st.session_state.processed_data, selected_year, selected_month)
else:
    st.info("Please upload and process your financial data to view the dashboard.") 