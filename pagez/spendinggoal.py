import streamlit as st
import pandas as pd
import datetime
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import utils.graphing as gp
import calendar
import utils.open_ai_calls as oaic

def get_days_in_current_month(selected_month) -> int:
    today = date.today()
    return calendar.monthrange(today.year, selected_month)[1]

def spending_goal(spending_df, months, selected_month):
    # First get the last 12 months of data
    today = date.today()
    past_spending_df = gp.filter_data_last_months(spending_df, 12)[1]
    selected_month_spending_df=gp.filter_data_year_month(spending_df, today.year, selected_month)


    past_alcohol_df=past_spending_df[past_spending_df['Category'] == "Beverages 🍺"]
    past_takeout_df=past_spending_df[past_spending_df['Category'] == "Takeout 🍔"]
    past_groceries_df=past_spending_df[past_spending_df['Category'] == "Groceries 🛒"]
    past_gambling_df = past_spending_df[past_spending_df['Category'] == "Gambling 🎰"]
    past_misc_entertainment_df = past_spending_df[past_spending_df['Category'] == "Misc Entertainment 🚀"]
    past_health_df = past_spending_df[past_spending_df['Category'] == "Health 💪"]
    past_subscription_df= past_spending_df[past_spending_df['Category']== "Subscriptions 💳🎬"]
    past_misc_shopping_df=past_spending_df[past_spending_df['Category']== "Misc Shopping 🚀"]
    past_bills_df=past_spending_df[past_spending_df['Category']== "Bills 📜"]
    past_fashion_df = past_spending_df[past_spending_df['Category'] == "Fashion 👚"]
    past_golf_df= past_spending_df[past_spending_df['Category'] == "Golf ⛳"]

    selected_month_alcohol_df=selected_month_spending_df[selected_month_spending_df['Category'] == "Beverages 🍺"]
    selected_month_takeout_df=selected_month_spending_df[selected_month_spending_df['Category'] == "Takeout 🍔"]
    selected_month_groceries_df=selected_month_spending_df[selected_month_spending_df['Category'] == "Groceries 🛒"]
    selected_month_gambling_df = selected_month_spending_df[selected_month_spending_df['Category'] == "Gambling 🎰"]
    selected_month_misc_entertainment_df = selected_month_spending_df[selected_month_spending_df['Category'] == "Misc Entertainment 🚀"]
    selected_month_health_df = selected_month_spending_df[selected_month_spending_df['Category'] == "Health 💪"]
    selected_month_subscription_df= selected_month_spending_df[selected_month_spending_df['Category']== "Subscriptions 💳🎬"]
    selected_month_misc_shopping_df=selected_month_spending_df[selected_month_spending_df['Category']== "Misc Shopping 🚀"]
    selected_month_bills_df=selected_month_spending_df[selected_month_spending_df['Category']== "Bills 📜"]
    selected_month_fashion_df = selected_month_spending_df[selected_month_spending_df['Category'] == "Fashion 👚"]
    selected_month_golf_df= selected_month_spending_df[selected_month_spending_df['Category'] == "Golf ⛳"]




    # Get current month data using existing category dataframes
    today = date.today()
    current_year = today.year
    
    selected_month_data = {
        'alcohol': gp.filter_data_year_month(selected_month_alcohol_df, current_year, selected_month),
        'takeout': gp.filter_data_year_month(selected_month_takeout_df, current_year, selected_month),
        'groceries': gp.filter_data_year_month(selected_month_groceries_df, current_year, selected_month),
        'gambling': gp.filter_data_year_month(selected_month_gambling_df, current_year, selected_month),
        'entertainment': gp.filter_data_year_month(selected_month_misc_entertainment_df, current_year, selected_month),
        'health': gp.filter_data_year_month(selected_month_health_df, current_year, selected_month),
        'spending':gp.filter_data_year_month(selected_month_spending_df, current_year, selected_month),
        'subscription': gp.filter_data_year_month(selected_month_subscription_df, current_year, selected_month),
        'misc_shopping': gp.filter_data_year_month(selected_month_misc_shopping_df, current_year, selected_month),
        'bills': gp.filter_data_year_month(selected_month_bills_df, current_year, selected_month),
        'fashion': gp.filter_data_year_month(selected_month_fashion_df, current_year, selected_month),
        'golf': gp.filter_data_year_month(selected_month_golf_df, current_year, selected_month)
    }

    # Function to group and sum by month
    def group_by_month(df):
        if df.empty:
            return pd.DataFrame()
        try:
            # Ensure Date column is datetime
            df['Date'] = pd.to_datetime(df['Transaction Date'])
            # Group by month and sum Amount
            monthly_sum = df.groupby(df['Date'].dt.to_period('M'))['Amount'].sum().reset_index()
            # Convert period to datetime for easier handling
            monthly_sum['Date'] = monthly_sum['Date'].dt.to_timestamp()
            return monthly_sum.sort_values('Date')
        except (KeyError, ValueError) as e:
            # Return empty DataFrame if there are issues with columns or date parsing
            return pd.DataFrame()

    # Function to calculate average of lowest months
    def get_lowest_months_avg(df, num_months):
        if df.empty:
            return 0
        try:
            # Get the absolute values since Amount is negative
            df['Amount'] = df['Amount'].abs()
            # Sort by Amount and take the lowest num_months
            lowest_months = df.nsmallest(num_months, 'Amount')
            return lowest_months['Amount'].mean()
        except (KeyError, ValueError) as e:
            # Return 0 if there are issues with the Amount column
            return 0

    # Apply grouping to each category
    alcohol_monthly = group_by_month(past_alcohol_df)
    takeout_monthly = group_by_month(past_takeout_df)
    groceries_monthly = group_by_month(past_groceries_df)
    gambling_monthly = group_by_month(past_gambling_df)
    entertainment_monthly = group_by_month(past_misc_entertainment_df)
    health_monthly = group_by_month(past_health_df)
    subscription_monthly = group_by_month(past_subscription_df)
    spending_monthly=group_by_month(past_spending_df)
    misc_shopping_monthly=group_by_month(past_misc_shopping_df)
    bills_monthly=group_by_month(past_bills_df)
    golf_monthly = group_by_month(past_golf_df)
    fashion_monthly = group_by_month(past_fashion_df)

    # Calculate averages of lowest months for each category
    lowest_months_avg = {
        'alcohol': get_lowest_months_avg(alcohol_monthly, months),
        'takeout': get_lowest_months_avg(takeout_monthly, months),
        'groceries': get_lowest_months_avg(groceries_monthly, months),
        'gambling': get_lowest_months_avg(gambling_monthly, months),
        'entertainment': get_lowest_months_avg(entertainment_monthly, months),
        'health': get_lowest_months_avg(health_monthly, months),
        'subscription': get_lowest_months_avg(subscription_monthly, months),
        'spending': get_lowest_months_avg(spending_monthly, months),
        'misc_shopping': get_lowest_months_avg(misc_shopping_monthly, months),
        'bills': get_lowest_months_avg(bills_monthly, months),
        'golf': get_lowest_months_avg(golf_monthly, months),
        'fashion': get_lowest_months_avg(fashion_monthly, months)
    }

    return {
        'monthly_data': {
            'alcohol': alcohol_monthly,
            'takeout': takeout_monthly,
            'groceries': groceries_monthly,
            'gambling': gambling_monthly,
            'entertainment': entertainment_monthly,
            'health': health_monthly,
            'subscription': subscription_monthly,
            'spending': spending_monthly,
            'misc_shopping': misc_shopping_monthly,
            'bills': bills_monthly,
            'golf': golf_monthly,
            'fashion': fashion_monthly
        },
        'lowest_months_avg': lowest_months_avg,
        'selected_month_data': selected_month_data
    }

def budgeting_page(spending_df, client):
    st.markdown('### Budgeting Goals 💰')
    st.write("""This page takes the average of your lowest 6 spending months within the past year and sets them as monthly targets for your main variable catgories. 
             This way, you know you can hit them as you've done it before! """)
    st.write("""You will see three columns. The first column states what you're pro-rated target is and takes into account the current day within the month.
             The second shows if you are meeting that target, and the third is your total monthly budget. Happy saving! 💰""")
    today = date.today()
    current_year = today.year
    current_month = today.month
    

    current_month = int(today.month)

    # Create month options for YTD
    month_options = list(range(1, current_month + 1))

    

    selected_month = st.selectbox(
            "Select Month",
            options=month_options,
            format_func=lambda x: calendar.month_name[x],
            index=len(month_options)-1  # Default to current month
        )

    # Calculate the day to use for pro-rating
    if selected_month == current_month:
        day_of_month = today.day
    else:
        day_of_month = calendar.monthrange(current_year, selected_month)[1]

    low_months_average= 6
    
    # Call spending_goal once and store the result
    spending_goal_result = spending_goal(spending_df, low_months_average, selected_month)
    
    alcohol_low_value = spending_goal_result['lowest_months_avg']['alcohol']
    takeout_low_value = spending_goal_result['lowest_months_avg']['takeout']
    grocery_low_value = spending_goal_result['lowest_months_avg']['groceries']
    misc_shopping_low_value = spending_goal_result['lowest_months_avg']['misc_shopping']
    health_low_value = spending_goal_result['lowest_months_avg']['health']
    bills_low_value = spending_goal_result['lowest_months_avg']['bills']
    spending_low_value = spending_goal_result['lowest_months_avg']['spending']
    misc_entertainment_low_value = spending_goal_result['lowest_months_avg']['entertainment']
    fashion_low_value = spending_goal_result['lowest_months_avg']['fashion']
    gambling_low_value = spending_goal_result['lowest_months_avg']['gambling']
    no_bills_spending_low_value = spending_low_value - bills_low_value
    entertainment_total_low_value = misc_entertainment_low_value + gambling_low_value
    shopping_total_low_value = fashion_low_value + misc_shopping_low_value


    alcohol_current_value= spending_goal_result['selected_month_data']['alcohol']["Amount"].sum()
    takeout_current_value= spending_goal_result['selected_month_data']['takeout']["Amount"].sum()
    grocery_current_value= spending_goal_result['selected_month_data']['groceries']["Amount"].sum()
    misc_shopping_current_value= spending_goal_result['selected_month_data']['misc_shopping']["Amount"].sum()
    health_current_value= spending_goal_result['selected_month_data']['health']["Amount"].sum()
    bills_current_value= spending_goal_result['selected_month_data']['bills']["Amount"].sum()
    misc_entertainment_current_value =spending_goal_result['selected_month_data']['entertainment']["Amount"].sum()
    gambling_current_value =spending_goal_result['selected_month_data']['gambling']["Amount"].sum()
    fashion_current_value = spending_goal_result['selected_month_data']['fashion']["Amount"].sum()
    spending_current_value= spending_goal_result['selected_month_data']['spending']["Amount"].sum()
    no_bills_spending_current_value = spending_current_value - bills_current_value
    entertainment_current_value = misc_entertainment_current_value + gambling_current_value
    shopping_total_current_value = misc_shopping_current_value + fashion_current_value

    if low_months_average is not 0:
        # Create a container for the metrics
        metrics_container = st.container()
        with metrics_container:
            st.markdown("### Budget Progress")
            
            # Create rows for each metric group
            def create_metric_row(label, current, month_target, days_in_month):
                st.markdown(f"#### {label}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if days_in_month > 0:
                        day_target = month_target*(day_of_month/days_in_month)
                    else:
                        day_target = month_target
                    st.metric("Pro-rated Budget Threshold", f"${day_target:.2f}")
                with col2:
                    if day_target != 0:
                        day_ratio=current/day_target
                    else:
                        day_ratio = 0
                    day_difference = current - day_target
                    if day_ratio > 1:
                        st.metric("Money Spent So Far", f"{current:.2f}", 
                                delta=f"{day_difference:.2f}", 
                                delta_color="inverse")
                    else:
                        st.metric("Money Spent So Far", f"{current:.2f}", 
                                delta=f"{day_difference:.2f}", 
                                delta_color="inverse")
                with col3:
                    st.metric("Monthly Target", f"${month_target:.2f}")

            # Create rows for each category
            create_metric_row("Beverages 🍺", alcohol_current_value, alcohol_low_value, get_days_in_current_month(selected_month))
            create_metric_row("Takeout 🍔", takeout_current_value, takeout_low_value, get_days_in_current_month(selected_month))
            create_metric_row("Groceries 🛒", grocery_current_value, grocery_low_value, get_days_in_current_month(selected_month))
            create_metric_row("Shopping 👚🚀", shopping_total_current_value, shopping_total_low_value, get_days_in_current_month(selected_month))
            create_metric_row("Health 💪", health_current_value, health_low_value, get_days_in_current_month(selected_month))
            create_metric_row("Entertainment 🎰🚀", entertainment_current_value, entertainment_total_low_value, get_days_in_current_month(selected_month))
            create_metric_row("Total Spending (No Bills) 💰", no_bills_spending_current_value, no_bills_spending_low_value, get_days_in_current_month(selected_month))
            st.divider()
            st.markdown("### BudgetGPT")
            st.write("BudgetGPT is a tool that will help you set goals for your categories with the most room to save as well as your overall monthly spend. Select a category to get advice on how to save!")
            col1, col2 = st.columns(2)
            with col1:
                category_selected = st.selectbox("Select a Category", ["Beverages 🍺", "Takeout 🍔", "Groceries 🛒", "Shopping 👚🚀", "Health 💪", "Entertainment 🎰🚀", "Total Spending (No Bills) 💰"])
                budgetGPT_button=st.button("Get Advice")
            if category_selected == "Beverages 🍺":
                dataframe_selected = gp.filter_data_year(spending_df[spending_df['Category'] == "Beverages 🍺"], current_year, selected_month)
            elif category_selected == "Takeout 🍔":
                dataframe_selected = gp.filter_data_year(spending_df[spending_df['Category'] == "Takeout 🍔"], current_year, selected_month)
            elif category_selected == "Groceries 🛒":
                dataframe_selected = gp.filter_data_year(spending_df[spending_df['Category'] == "Groceries 🛒"], current_year, selected_month)
            elif category_selected == "Shopping 👚🚀":
                dataframe_selected = gp.filter_data_year(pd.concat([spending_df[spending_df['Category'] == "Fashion 👚"], spending_df[spending_df['Category']== "Misc Shopping 🚀"]], ignore_index=True), current_year, selected_month)
            elif category_selected == "Health 💪":
                dataframe_selected = gp.filter_data_year(spending_df[spending_df['Category'] == "Health 💪"], current_year, selected_month)
            elif category_selected == "Entertainment 🎰🚀":
                dataframe_selected = gp.filter_data_year(pd.concat([spending_df[spending_df['Category'] == "Misc Entertainment 🚀"],spending_df[spending_df['Category'] == "Gambling 🎰"]], ignore_index=True), current_year, selected_month)
            elif category_selected == "Total Spending (No Bills) 💰":
                dataframe_selected = gp.filter_data_year(spending_df, current_year, selected_month)
            with col2:
                None

            if budgetGPT_button:
                with st.spinner("BudgetGPT is analyzing your spending patterns and generating personalized advice..."):
                    oaic.open_ai_budgetGPT(alcohol_low_value, takeout_low_value, grocery_low_value, shopping_total_low_value, entertainment_total_low_value, health_low_value, no_bills_spending_low_value, dataframe_selected, category_selected, client)
