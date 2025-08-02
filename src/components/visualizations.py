import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def display_financial_metrics(df, selected_year, selected_month):
    """Display financial metrics."""
    if df is None:
        return
    
    # Filter data based on selected year and month
    filtered_df = df.copy()
    if selected_year != "All Years":
        filtered_df = filtered_df[filtered_df["Year"] == selected_year]
    if selected_month != "All Months":
        filtered_df = filtered_df[filtered_df["Month"] == selected_month]
    
    # Calculate metrics
    total_spending = filtered_df[filtered_df["Amount"] < 0]["Amount"].sum()
    total_income = filtered_df[filtered_df["Amount"] > 0]["Amount"].sum()
    net_income = total_income + total_spending
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Spending", f"${abs(total_spending):,.2f}")
    with col2:
        st.metric("Total Income", f"${total_income:,.2f}")
    with col3:
        st.metric("Net Income", f"${net_income:,.2f}")

def display_spending_by_category(df, selected_year, selected_month):
    """Display spending by category."""
    if df is None:
        return
    
    # Filter data based on selected year and month
    filtered_df = df.copy()
    if selected_year != "All Years":
        filtered_df = filtered_df[filtered_df["Year"] == selected_year]
    if selected_month != "All Months":
        filtered_df = filtered_df[filtered_df["Month"] == selected_month]
    
    # Calculate spending by category
    category_spending = filtered_df[filtered_df["Amount"] < 0].groupby("Category")["Amount"].sum().abs()
    
    # Create pie chart
    fig = px.pie(
        values=category_spending.values,
        names=category_spending.index,
        title="Spending by Category"
    )
    st.plotly_chart(fig)

def display_monthly_trends(df, selected_year):
    """Display monthly spending trends."""
    if df is None:
        return
    
    # Filter data based on selected year
    filtered_df = df.copy()
    if selected_year != "All Years":
        filtered_df = filtered_df[filtered_df["Year"] == selected_year]
    
    # Calculate monthly spending
    monthly_spending = filtered_df[filtered_df["Amount"] < 0].groupby("Month")["Amount"].sum().abs()
    
    # Create line chart
    fig = px.line(
        x=monthly_spending.index,
        y=monthly_spending.values,
        title="Monthly Spending Trends",
        labels={"x": "Month", "y": "Amount"}
    )
    st.plotly_chart(fig)

def display_transaction_table(df, selected_year, selected_month):
    """Display transaction table."""
    if df is None:
        return
    
    # Filter data based on selected year and month
    filtered_df = df.copy()
    if selected_year != "All Years":
        filtered_df = filtered_df[filtered_df["Year"] == selected_year]
    if selected_month != "All Months":
        filtered_df = filtered_df[filtered_df["Month"] == selected_month]
    
    # Display table
    st.dataframe(filtered_df)

def display_category_breakdown(df, selected_year, selected_month):
    """Display detailed category breakdown."""
    if df is None:
        return
    
    # Filter data based on selected year and month
    filtered_df = df.copy()
    if selected_year != "All Years":
        filtered_df = filtered_df[filtered_df["Year"] == selected_year]
    if selected_month != "All Months":
        filtered_df = filtered_df[filtered_df["Month"] == selected_month]
    
    # Calculate category metrics
    category_metrics = filtered_df.groupby("Category").agg({
        "Amount": ["sum", "count", "mean"]
    }).round(2)
    
    # Display metrics
    st.dataframe(category_metrics) 