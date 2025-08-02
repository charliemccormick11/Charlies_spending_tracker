import streamlit as st
import pandas as pd
from openai import OpenAI
import os
import json
from src.utils.data_processing import (
    process_credit_transactions,
    process_checking_transactions,
    process_venmo_transactions
)

def create_sidebar():
    """Create the sidebar with file uploaders and processing button."""

    credit_card = st.sidebar.selectbox("Select Your Credit Card 💳", options = ["Chase", "Other"])
    st.sidebar.divider()

    st.sidebar.subheader("Upload Credit Card Statements 🧾")
    uploaded_credit=st.sidebar.file_uploader("Upload Credit Card CSV files", type = ["csv"], accept_multiple_files= True)
    st.sidebar.divider()

    st.sidebar.subheader("Upload Checking Statements 🧾")
    uploaded_checking = st.sidebar.file_uploader("Upload Checking CSV files", type = ["csv"], accept_multiple_files= True)
    st.sidebar.divider()

    st.sidebar.subheader("Upload Venmo Files 🧾")
    uploaded_venmos = st.sidebar.file_uploader("Upload Venmo CSV files", type = ["csv"], accept_multiple_files= True)


def process_uploaded_files(uploaded_credit, uploaded_checking, uploaded_venmos, client):
    """Process uploaded files and store results in session state."""
    if uploaded_credit or uploaded_checking or uploaded_venmos:
        if st.sidebar.button("Process Data"):
            with st.spinner("Processing data..."):
                process_credit_data(uploaded_credit, client)
                process_checking_data(uploaded_checking)
                process_venmo_data(uploaded_venmos)
            st.success("Data processing complete!")

def process_credit_data(uploaded_credit, client):
    """Process credit card data."""
    if uploaded_credit:
        st.sidebar.success(f"{len(uploaded_credit)} credit file(s) uploaded.")
        dfs_credit = [pd.read_csv(file, header=None) for file in uploaded_credit]
        total_credit_df = pd.concat(dfs_credit, ignore_index=True)

        credit_sample = total_credit_df.head(15)
        prompt = f"""
        I have uploaded the following CSV data:

        {credit_sample}

        Please:
        1. Check if there is a header row in the data.
            1.1 If the first row contains column names (e.g., "Transaction Date", "Amount"), set 'header' to True.
            1.2 If the first row contains data (e.g., values like "2023-01-01", "100"), set 'header' to False.
        2. Regardless of if there's a header, provide the column indices (starting from 0) for the following columns:
        - Transaction Date
        - Transaction Description (names of places purchased)
        - Amount
        - Category (if present)
            - these would be Dining, Food, Groceries, etc.
        3. If the Category column is missing, mention that as None.
        4. If there are two amount columns (Credit and Debit), provide their indices and include them as "credit" and "debit".
            4.4 If there is one amount column, put it as 'debit'.
        6. Return ONLY the response as a Python JSON dictionary with the following keys: 'header', 'transaction_date', 'transaction_name', 'credit', 'debit', 'category'. No additional text, explanations, or strings. Only return the dictionary, nothing else. Make format identical for with or without headers!
        7. Remove anything else but the dictionary and don't display as a code block
        """

        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        try:
            st.session_state.column_info = json.loads(completion.choices[0].message.content)
        except:
            st.error("Error parsing OpenAI response")
            st.session_state.column_info = {}

        if st.session_state.column_info:
            process_credit_dataframe(total_credit_df)

def process_credit_dataframe(total_credit_df):
    """Process the credit card dataframe with column information."""
    if st.session_state.column_info['header'] == True:
        total_credit_df.columns = total_credit_df.iloc[0]
        total_credit_df = total_credit_df.drop(0, axis=0).reset_index(drop=True)
        
        total_credit_df["Transaction Date"] = total_credit_df.iloc[:, st.session_state.column_info['transaction_date']]
        total_credit_df["Description"] = total_credit_df.iloc[:, st.session_state.column_info['transaction_name']]
        total_credit_df["Category"] = total_credit_df.iloc[:, st.session_state.column_info.get('category', None)]
        total_credit_df["Amount"] = total_credit_df.iloc[:, st.session_state.column_info['debit']]
        
        if st.session_state.column_info.get('category') is None:
            total_credit_df = total_credit_df[["Transaction Date", "Description", "Amount"]]
        else:
            total_credit_df = total_credit_df[["Transaction Date", "Description", "Category", "Amount"]]
    
    total_credit_df['Amount'] = pd.to_numeric(total_credit_df['Amount'], errors='coerce')
    st.session_state.processed_credit_df = process_credit_transactions(total_credit_df)
    st.session_state.processed_credit_df["Transaction Date"] = pd.to_datetime(st.session_state.processed_credit_df["Transaction Date"], errors='coerce')
    st.session_state.processed_credit_df = st.session_state.processed_credit_df.dropna(subset=["Transaction Date"])
    st.session_state.processed_credit_df["Year"] = st.session_state.processed_credit_df["Transaction Date"].dt.year.astype(int).astype(str)
    st.session_state.processed_credit_df["Month"] = st.session_state.processed_credit_df["Transaction Date"].dt.month
    st.session_state.processed_credit_df["Amount"] = -st.session_state.processed_credit_df["Amount"]

def process_checking_data(uploaded_checking):
    """Process checking account data."""
    if uploaded_checking:
        col_names = ["Details", "Posting Date", "Description", "Amount", "Balance"]
        st.sidebar.success(f"{len(uploaded_checking)} checking file(s) uploaded.")
        dfs_checking = [pd.read_csv(file, names=col_names, usecols=[0,1,2,3,5]) for file in uploaded_checking]
        total_checking_df = pd.concat(dfs_checking, ignore_index=True)
        total_checking_df = total_checking_df.drop(index=0)
        st.session_state.total_checking_df = total_checking_df
        st.session_state.processed_checking_df = process_checking_transactions(total_checking_df)
        st.session_state.processed_checking_df["Amount"] = pd.to_numeric(st.session_state.processed_checking_df["Amount"], errors='coerce')
        st.session_state.processed_checking_df["Amount"] = -st.session_state.processed_checking_df["Amount"]
        st.session_state.processed_checking_df["Posting Date"] = pd.to_datetime(st.session_state.processed_checking_df["Posting Date"], errors='coerce')
        st.session_state.processed_checking_df["Transaction Date"] = st.session_state.processed_checking_df["Posting Date"]
        st.session_state.processed_checking_df = st.session_state.processed_checking_df.drop(columns=["Posting Date"])
        st.session_state.processed_checking_df["Year"] = st.session_state.processed_checking_df["Transaction Date"].dt.year.astype(str)
        st.session_state.processed_checking_df["Month"] = st.session_state.processed_checking_df["Transaction Date"].dt.month

def process_venmo_data(uploaded_venmos):
    """Process Venmo data."""
    if uploaded_venmos:
        st.sidebar.success(f"{len(uploaded_venmos)} venmo file(s) uploaded.")
        dfs_venmo = [pd.read_csv(file) for file in uploaded_venmos]
        total_venmo_df = pd.concat(dfs_venmo, ignore_index=True)
        st.session_state.processed_venmo_df = process_venmo_transactions(total_venmo_df)
        total_venmo_df = total_venmo_df.iloc[:, 1:]
        total_venmo_df["Amount (total)"] = pd.Series(total_venmo_df["Amount (total)"]).str.replace('[\$\+\,]', '', regex=True).str.replace(' ', '').astype(float)
        total_venmo_df["Amount"] = -total_venmo_df["Amount (total)"]
        total_venmo_df["Description"] = total_venmo_df["Note"]
        total_venmo_df['Transaction Date'] = pd.to_datetime(total_venmo_df["Datetime"])
        st.session_state.processed_venmo_df = process_venmo_transactions(total_venmo_df)
        st.session_state.processed_venmo_df["Year"] = st.session_state.processed_venmo_df["Transaction Date"].dt.year.astype(str)
        st.session_state.processed_venmo_df["Month"] = st.session_state.processed_venmo_df["Transaction Date"].dt.month 