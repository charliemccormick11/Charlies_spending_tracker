import streamlit as st
import calendar
import utils.graphing as gp
import utils.open_ai_calls as oaic
from io import StringIO
import pandas as pd
import time


def current_spending_page(relevant_columns, client):
    def page_selected(selected_value):
            return st.session_state.spend_df[st.session_state.spend_df["Category"]==selected_value]

    col1, col2 = st.columns(2)

    # Year dropdown with "All Time" option
    if "Year" in st.session_state.spend_df.columns:
        st.session_state.spend_df["Year"] = st.session_state.spend_df["Year"].astype(int)
    years = sorted(st.session_state.spend_df["Year"].unique(), reverse=True)
    year_options = ["All Time"] + years
    with col1:
        selected_year = st.selectbox("Select Year", year_options)

    # Month dropdown with "Whole Year" option
    month_options = ["All Transactions"] + list(range(1, 13))
    with col2:
        selected_month = st.selectbox(
            "Select Month",
            month_options,
            format_func=lambda x: "All Transactions" if x == "All Transactions" else calendar.month_name[x]
        )

    # Display data on pages
    filtered_data_spend_ym = gp.filter_data_year_month(st.session_state.spend_df, selected_year, selected_month)
    filtered_data_spend_ym["Amount"] = (pd.to_numeric(filtered_data_spend_ym["Amount"], errors="coerce"))
    spending_df = gp.spending_table(filtered_data_spend_ym, st.session_state.spend_df, selected_month, selected_year)
    options = ["Overall Spending 💸"] + [cat for cat in spending_df['Category'].unique() if cat != "Reimbursements 💸🔙"]
    
    # Initialize selected_value in session state if not exists
    if 'selected_value' not in st.session_state:
        st.session_state.selected_value = "Overall Spending 💸"
    
    # Check if current selected value is still valid in the new filtered data
    if st.session_state.selected_value not in options:
        st.session_state.selected_value = "Overall Spending 💸"
    
    st.session_state.selected_value = st.selectbox("Select a category:", options, index=options.index(st.session_state.selected_value))


    # Create a copy of the DataFrame for styling
    styled_df = spending_df.copy()
    if selected_month != "All Transactions":
        styled_df.index = styled_df.index + 1
    
    # Apply styling to the copy only if "Month % Change" column exists
    if "Month % Change" in styled_df.columns:
        styled_data = styled_df.style.applymap(
            lambda x: 'color: red' if isinstance(x, str) and x.startswith('+') else 'color: green' if isinstance(x, str) and x.startswith('-') else 
            'color: black' if isinstance(x, str) and (x.startswith('0') or x == '0%') else '',
            subset=["Month % Change"])
    else:
        styled_data = styled_df.style

    if st.session_state.selected_value == "Overall Spending 💸":
        st.markdown('### Overall Spending 💸')
        # Apply filters to data
       
        filtered_data_ym = gp.filter_data_year_month(st.session_state.spend_df, selected_year, selected_month)
        filtered_data_ym["Amount"] = pd.to_numeric(filtered_data_ym["Amount"], errors="coerce")
        total_spend_ym = filtered_data_ym['Amount'].sum()

        if selected_month != "All Transactions":
            st.metric("Total Month Spend:", f"-${total_spend_ym:,.2f}")

            st.subheader("Spending Breakdown")
        
            st.table(styled_data)
        else:

            if selected_year =="All Time":
                st.metric("All Time Spend:", f"-${total_spend_ym:,.2f}")
                st.subheader("Spending Breakdown")
                st.table(spending_df[["Category", "Total Amount", "Transactions"]])

            else:
                st.metric("Total Annual Spend:", f"-${total_spend_ym:,.2f}")

                st.subheader("Spending Breakdown")
                    
                st.table(spending_df)


        # Sort for display with error handling
        try:
            # Ensure Transaction Date column exists and has valid data
            if "Transaction Date" in st.session_state.spend_df.columns:
                # Convert to datetime if possible, handle errors gracefully
                st.session_state.spend_df["Transaction Date"] = pd.to_datetime(
                    st.session_state.spend_df["Transaction Date"], 
                    errors='coerce'
                )
                # Remove rows with invalid dates for sorting
                valid_dates_df = st.session_state.spend_df.dropna(subset=["Transaction Date"])
                if not valid_dates_df.empty:
                    sorted_df = valid_dates_df.sort_values("Transaction Date", ascending=False)
                else:
                    sorted_df = st.session_state.spend_df
            else:
                sorted_df = st.session_state.spend_df
        except:
            sorted_df = st.session_state.spend_df

        # Cache categories in session state to avoid recalculating on every render
        if 'all_categories' not in st.session_state:
            st.session_state.all_categories = sorted(set(st.session_state.spend_df['Category'].unique()))
        else:
            # Only update if the underlying data has changed
            current_categories = set(st.session_state.spend_df['Category'].unique())
            if current_categories != set(st.session_state.all_categories):
                st.session_state.all_categories = sorted(current_categories)
        
        # Cache column configuration to avoid recreating on every render
        if 'column_config' not in st.session_state or st.session_state.get('column_config_categories') != st.session_state.all_categories:
            st.session_state.column_config = {
                "Description": st.column_config.TextColumn(
                    "Description",
                    help="Edit the transaction description",
                    max_chars=None,
                    validate=None
                ),
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    options=st.session_state.all_categories,
                    required=True
                )
            }
            st.session_state.column_config_categories = st.session_state.all_categories.copy()

        # Show editor
        edited_df = st.data_editor(
            sorted_df,
            column_config=st.session_state.column_config,
            disabled=[col for col in sorted_df.columns if col not in ["Category", "Description"]],
            column_order=["Transaction Date", "Description", "Category", "Amount"],
            key="spending_data_editor",
            use_container_width=True,
            hide_index=True
        )
        st.write("You can edit the Description and Category columns. Press below to save changes! 🔥")

        updated_spend_df = st.session_state.spend_df.copy()

        category_changer = st.button("Press to Save Category Changes!")

        if category_changer:
            from_indicies = updated_spend_df.index

            for idx in from_indicies:
                updated_spend_df.loc[idx, "Category"] = edited_df.loc[idx, "Category"]
                updated_spend_df.loc[idx, "Description"] = edited_df.loc[idx, "Description"]

                st.session_state.spend_df = updated_spend_df
            st.session_state.spend_df.sort_values("Transaction Date", ascending=False)
            st.success("Category Updated!")
            time.sleep(2)
            st.rerun()




    elif (st.session_state.selected_value!= "Overall Spending 💸") and (st.session_state.selected_value!= "Remaining") and (st.session_state.selected_value!=  "Payback 💸🔙"):
        st.header(st.session_state.selected_value)
        gp.default_page_graphs(page_selected(st.session_state.selected_value), selected_month, selected_year, relevant_columns)


    elif st.session_state.selected_value == "Remaining":
        if st.session_state.total_remaining_df.empty:
            st.write("✅ All transactions have been categorized!")
        else:
            st.header("Remaining Transactions")
            gp.default_page_graphs(st.session_state.total_remaining_df, selected_month, selected_year, relevant_columns)


            






    
