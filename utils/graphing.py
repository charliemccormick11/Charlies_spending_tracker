import streamlit as st
import pandas as pd
import utils.data_processing as dp
import calendar
import altair as alt
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
import time


def convert_month(month):
    try:
        # Try to convert directly to integer (handles cases where months are numbers)
        return int(month)
    except ValueError:
        # If ValueError occurs, convert month name to month number
        return pd.to_datetime(month, format='%B').month


def filter_data_year_month(df, year, month):
    """Filters the dataframe based on selected year and month."""
    filtered_df_year_month = df.copy()

    if year != "All Time":
        filtered_df_year_month = filtered_df_year_month[filtered_df_year_month["Year"].astype(str) == str(year)]

    if month != "All Transactions":
        filtered_df_year_month = filtered_df_year_month[filtered_df_year_month["Month"] == month]

    return filtered_df_year_month


def filter_data_last_months(df, num):
    # Create a copy of the DataFrame to avoid modifying the original
    filtered_df_last_months = df.copy()

    # Ensure 'Transaction Date' is a datetime column (if it's not already)
    # Handle mixed date formats: '2025-03-03 00:00:00' and '2025-03-03T20:12:02'
    def parse_mixed_dates(date_str):
        if pd.isna(date_str):
            return pd.NaT
        try:
            # Try parsing as ISO format first (with T)
            return pd.to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                # Try parsing as standard format (with space)
                return pd.to_datetime(date_str, format='%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    # Fallback to pandas automatic parsing
                    return pd.to_datetime(date_str)
                except ValueError:
                    # If all else fails, return NaT
                    return pd.NaT
    
    filtered_df_last_months['Transaction Date'] = filtered_df_last_months['Transaction Date'].apply(parse_mixed_dates)

    # Get today's date
    today = datetime.today()

    # Get the *first day* of the current month
    first_of_this_month = today.replace(day=1)

    # Calculate the start date: num months before the start of this month
    start_date = first_of_this_month - relativedelta(months=num)

    # Calculate the end date: the last day of the previous month
    end_date = first_of_this_month - relativedelta(days=1)

    # Filter the rows
    mask = (filtered_df_last_months['Transaction Date'] >= start_date) & (filtered_df_last_months['Transaction Date'] <= end_date)
    filtered_df_last_months = filtered_df_last_months[mask]

    average_monthly_spend =(filtered_df_last_months['Amount'].sum())/num


    return average_monthly_spend, filtered_df_last_months



def filter_data_year(df, year, month):
    """Filters the dataframe based on selected year."""
    filtered_df_year = df.copy()
    filtered_df_year["Month"] = filtered_df_year["Month"].apply(convert_month)

    if year != "All Time":
        filtered_df_year = filtered_df_year[(filtered_df_year["Year"].astype(str) == str(year)) & (filtered_df_year["Month"] <=  month)]

    return filtered_df_year

def bar_graph_annual(filtered_data, selected_month, selected_year):
    # Convert numeric months to month names
    filtered_data["Month"] = filtered_data["Month"].apply(lambda x: calendar.month_name[int(x)] if pd.notna(x) else None)
    filtered_data_spend = filtered_data
    if selected_month == "All Transactions":
        if selected_year == "All Time" :
            yearly_data_spend= (filtered_data_spend.groupby("Year")["Amount"].sum().reset_index())
            

            chart = alt.Chart(yearly_data_spend).mark_bar().encode(
            x=alt.X("Year:N", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("Amount:Q", title="Total Amount ($)"),
            color=alt.value("#66b3ff")
            ).properties(
            title="Total Amount Spent Per Year"
            )
            return chart


        else: 
            # Aggregate by month
            monthly_data_spend = (
                filtered_data_spend.groupby("Month")["Amount"]
                .sum()
                .reset_index()
            )


            # Ensure all months are present
            month_order = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            all_months_df = pd.DataFrame({"Month": month_order})
            monthly_data_spend = all_months_df.merge(monthly_data_spend, on="Month", how="left").fillna(0)

            # Ensure correct sorting
            monthly_data_spend["Month"] = pd.Categorical(monthly_data_spend["Month"], categories=month_order, ordered=True)

            # Create Altair bar chart without the average line
            chart = alt.Chart(monthly_data_spend).mark_bar().encode(
                x=alt.X("Month:N", sort=month_order, axis=alt.Axis(labelAngle=-45, titleFontSize=20, titleColor="black", labelColor="black")),
                y=alt.Y("Amount:Q", title="Total Amount ($)", axis=alt.Axis(titleFontSize=20, titleColor="black", labelColor="black")),
                color=alt.value("#66b3ff")
            ).properties(
                title="Total Amount Spent Per Month (Jan - Dec)"
            )

            return chart
    


def top_five_spots(filtered_data):
    top_spots = (
    filtered_data.groupby("Description")
    .agg(Total_Amount=("Amount", "sum"), Visits=("Amount", "count"))  # Count transactions
    .sort_values(by="Total_Amount", ascending=False)
    .head(5)
    .reset_index()
    )
    top_spots["Total Amount"]=top_spots["Total_Amount"].apply(lambda x: f"${x:,.2f}")
    return top_spots

def spending_table(combined_data, full_combined_data, selected_month, selected_year):
    if selected_month != "All Transactions":
        # Aggregating by Category
        current_month_categories = (combined_data.groupby(["Year", "Month", "Category"])
            .agg(Total_Amount=("Amount", "sum"), Transactions=("Amount", "count"))
            .reset_index()
        )
        current_month_categories["Month"] = current_month_categories["Month"].apply(convert_month)

        full_data_categories = (
            full_combined_data.groupby(["Year", "Month", "Category"])
            .agg(Total_Amount=("Amount", "sum"))
            .reset_index()
        )

        full_data_categories["Month"] = full_data_categories["Month"].astype(int)

        # Add the previous month's value by considering the year change (January vs December)
        current_month_categories["Previous_Month_Amount"] = None

        for i, row in current_month_categories.iterrows():
            # Check if the current month is January (to handle year change)
            if row["Month"] == 1:  # January
                # Get the December of the previous year
                previous_year = str(int(float(row["Year"])) - 1)  # Convert float string to float, then to int for subtraction, then back to string
                previous_month = 12
                previous_row = full_data_categories[(full_data_categories["Year"] == previous_year) & 
                                        (full_data_categories["Month"] == previous_month) & 
                                        (full_data_categories["Category"] == row["Category"])]
                if not previous_row.empty:
                    current_month_categories.at[i, "Previous_Month_Amount"] = previous_row["Total_Amount"].values[0]
            else:
                # For other months, just shift the data
                previous_row = full_data_categories[(full_data_categories["Year"] == row["Year"]) & 
                                        (full_data_categories["Month"] == row["Month"] - 1) & 
                                        (full_data_categories["Category"] == row["Category"])]
                if not previous_row.empty:
                    current_month_categories.at[i, "Previous_Month_Amount"] = previous_row["Total_Amount"].values[0]

        current_month_categories["Month % Change"] = ((current_month_categories["Total_Amount"] - current_month_categories["Previous_Month_Amount"]) / current_month_categories["Previous_Month_Amount"]) * 100
        current_month_categories["Month % Change"] = current_month_categories["Month % Change"].fillna(100)

        

        # Aggregating to display by Category in the final table (only showing relevant columns)
        final_categories = (
            current_month_categories.groupby("Category")
            .agg(Total_Amount=("Total_Amount", "sum"), Transactions=("Transactions", "sum"), Month_Percentage_Change=("Month % Change", "last"))
            .sort_values(by="Total_Amount", ascending=False)
            .reset_index()
        )
 

        # Format columns
        final_categories["Total_Amount"] = final_categories["Total_Amount"].apply(lambda x: f"${x:,.2f}")
        final_categories = final_categories.rename(columns={"Total_Amount": "Total Amount"})

        final_categories["Month_Percentage_Change"] = final_categories["Month_Percentage_Change"].apply(
            lambda x: f"{x:+.0f}%" if x != 0 else "0%")
        final_categories = final_categories.rename(columns={"Month_Percentage_Change": "Month % Change"})


        final_categories = final_categories.reset_index(drop=True)  # Reset index to default starting from 0
          # Update index to start from 1
        
        # Display with color formatting
        #styled_data = final_categories.style.applymap(
        #lambda x: 'color: red' if isinstance(x, str) and x.startswith('+') else 'color: green' if isinstance(x, str) and x.startswith('-') else '',
        #subset=["Month % Change"])

        return final_categories
    
    else:
        if selected_year != "All Time":
            # Aggregating by Category
            full_data_categories = (
            combined_data.groupby(["Category"])
            .agg(Total_Amount=("Amount", "sum"), Transactions=("Amount", "count"))
            .sort_values(by="Total_Amount", ascending=False)
            .reset_index()
            )
            full_data_categories["Total_Amount"] = full_data_categories["Total_Amount"].apply(lambda x: f"${x:,.2f}")
            full_data_categories = full_data_categories.rename(columns={"Total_Amount": "Total Amount"})
            full_data_categories.index = full_data_categories.index + 1  # Update index to start from 1

            return full_data_categories

        else:
            # Aggregating by Category
            full_data_categories = (
                full_combined_data.groupby(["Year", "Month", "Category"])
                .agg(Total_Amount=("Amount", "sum"))
                .reset_index()
            )

            full_data_categories["Month"] = full_data_categories["Month"].astype(int)

            # Add the previous month's value by considering the year change (January vs December)
            current_month_categories = (
                combined_data.groupby(["Year", "Month", "Category"])
                .agg(Total_Amount=("Amount", "sum"), Transactions=("Amount", "count"))
                .reset_index()
            )
            current_month_categories["Month"] = current_month_categories["Month"].apply(convert_month)

            current_month_categories["Previous_Month_Amount"] = None

            for i, row in current_month_categories.iterrows():
                # Check if the current month is January (to handle year change)
                if row["Month"] == 1:  # January
                    # Get the December of the previous year
                    previous_year = str(int(float(row["Year"])) - 1)  # Convert float string to float, then to int for subtraction, then back to string
                    previous_month = 12
                    previous_row = full_data_categories[(full_data_categories["Year"] == previous_year) & 
                                                    (full_data_categories["Month"] == previous_month) & 
                                                    (full_data_categories["Category"] == row["Category"])]
                    if not previous_row.empty:
                        current_month_categories.at[i, "Previous_Month_Amount"] = previous_row["Total_Amount"].values[0]
                else:
                    # For other months, just shift the data
                    previous_row = full_data_categories[(full_data_categories["Year"] == row["Year"]) & 
                                                    (full_data_categories["Month"] == row["Month"] - 1) & 
                                                    (full_data_categories["Category"] == row["Category"])]
                    if not previous_row.empty:
                        current_month_categories.at[i, "Previous_Month_Amount"] = previous_row["Total_Amount"].values[0]

            current_month_categories["Month % Change"] = ((current_month_categories["Total_Amount"] - current_month_categories["Previous_Month_Amount"]) / current_month_categories["Previous_Month_Amount"]) * 100
            current_month_categories["Month % Change"] = current_month_categories["Month % Change"].fillna(100)

            # Aggregating to display by Category in the final table (only showing relevant columns)
            final_categories = (
                current_month_categories.groupby("Category")
                .agg(Total_Amount=("Total_Amount", "sum"), Transactions=("Transactions", "sum"), Month_Percentage_Change=("Month % Change", "last"))
                .sort_values(by="Total_Amount", ascending=False)
                .reset_index()
            )

            # Format columns
            final_categories["Total_Amount"] = final_categories["Total_Amount"].apply(lambda x: f"${x:,.2f}")
            final_categories = final_categories.rename(columns={"Total_Amount": "Total Amount"})

            final_categories["Month_Percentage_Change"] = final_categories["Month_Percentage_Change"].apply(
                lambda x: f"{x:+.0f}%" if x != 0 else "0%")
            final_categories = final_categories.rename(columns={"Month_Percentage_Change": "Month % Change"})

            final_categories = final_categories.reset_index(drop=True)  # Reset index to default starting from 0
              # Update index to start from 1
            final_categories.index = final_categories.index + 1  # Update index to start from 1
            
            # Display with color formatting
            #styled_data = final_categories.style.applymap(
            #lambda x: 'color: red' if isinstance(x, str) and x.startswith('+') else 'color: green' if isinstance(x, str) and x.startswith('-') else '',
            #subset=["Month % Change"])

            return final_categories

def check_save_graph(combined_data):
    line_chart = (
    alt.Chart(combined_data)
    .mark_line(point=True)  # Add points to the line for better visibility
    .encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Total Min Balance:Q", title="Total Balance (Checking + Savings)"),
        tooltip=["Year", "Month", "Total Min Balance"]  # Add hover tooltips
    )
    .properties(title="Checking + Savings Balance Over Time")
    .interactive()  # Enable zooming and panning
    )

    return line_chart

def default_page_graphs(category_df, selected_month, selected_year, relevant_columns):

    filtered_data = filter_data_year_month(category_df, selected_year, selected_month)

    st.metric("Total Amount:", f"${filtered_data['Amount'].sum():,.2f}")
    if selected_month == "All Transactions":
        st.altair_chart(bar_graph_annual(filtered_data, selected_month, selected_year), use_container_width=True)
        
    st.subheader("Top 5 by Spending")
    top_five_df = top_five_spots(filtered_data)[["Description", "Total Amount", "Visits"]]
    top_five_df.index = top_five_df.index + 1
    st.table(top_five_df)
    st.subheader("All Transactions")
    edited_df = st.data_editor(
    filtered_data,
    column_config=st.session_state.column_config,
    disabled=[col for col in filtered_data.columns if col != "Category"],
    column_order=["Transaction Date", "Description", "Category", "Amount"],
    key="spending_data_editor",
    use_container_width=True,
    hide_index=True
    )
    selected_rows= edited_df[edited_df['Category']!= st.session_state.selected_value]
    updated_spend_df = st.session_state.spend_df.copy()

    category_changer = st.button("Press to Save Category Changes!")

    if category_changer:
        if not selected_rows.empty:
            row_indices= selected_rows.index
            
            for idx in row_indices:
                updated_spend_df.loc[idx, "Category"] = edited_df.loc[idx, "Category"]
                
                
            st.session_state.spend_df = updated_spend_df
            st.session_state.spend_df.sort_values("Transaction Date", ascending=False)
            st.success("Category changes applied and saved!")
            time.sleep(1.5)
            st.rerun()
    
                  
                


