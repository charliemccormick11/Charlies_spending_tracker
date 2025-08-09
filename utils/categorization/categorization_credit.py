import pandas as pd
import numpy as np
import utils.data_processing as dp
import streamlit as st
import boto3
import os 


#s3 = boto3.client('s3')


def categorize_previous_transactions(processed_nonchase_df):
    
    # Add Category column if it doesn't exist
    if "Category" not in processed_nonchase_df.columns:
        processed_nonchase_df["Category"] = None
    
    # Create a lookup dictionary from previous categories
    previous_category_lookup = {}
    if not st.session_state.previous_categories.empty:
        for _, row in st.session_state.previous_categories.iterrows():
            description = row["Description"]
            category = row["Category"]
            previous_category_lookup[description] = category

        st.write(st.session_state.previous_categories)
    
    # Check each transaction against previous categories
    for idx, row in processed_nonchase_df.iterrows():
        transaction_description = row["Description"]
        
        # Check if this transaction description exists in previous categories
        if transaction_description in previous_category_lookup:
            # Assign the category from the previous categories lookup
            processed_nonchase_df.loc[idx, "Category"] = previous_category_lookup[transaction_description]
    

    st.session_state.categorized_transactions_returning = processed_nonchase_df[processed_nonchase_df["Category"].notna()]
    st.dataframe(st.session_state.categorized_transactions_returning)
    st.session_state.remaining_transactions_returning = processed_nonchase_df[processed_nonchase_df["Category"].isna()]


    return st.session_state.categorized_transactions_returning, st.session_state.remaining_transactions_returning




def categorize_first_pass(processed_nonchase_df):
    # Load the historical transaction data
    try:
        historical_data = pd.read_csv("Historic Data.csv")
    except FileNotFoundError:
        st.error("Historical transaction data file not found. Please ensure 'Historic Data.csv' exists in the project folder.")
        return None

    # Initialize empty DataFrames for each category
    category_keys = [
        "bar", "restaurant", "takeout", "grocery", "miscfood", "golf", "gambling", "entertainment",
        "fashion", "shopping", "rideshare", "travel", "gas", "transport", "insurance", "car",
        "health", "gifts", "bills", "subs", "fees", "remaining"
    ]
    categories = {key: pd.DataFrame() for key in category_keys}

    # Create a lookup dictionary using normalized extracted descriptions
    category_lookup = {}
    for _, row in historical_data.iterrows():
        ext_desc = row["Extracted Description"]
        norm_ext_desc = tuple(str(ext_desc).lower().split())
        category = row["Category"]
        category_lookup[norm_ext_desc] = category

    # List to track categorized rows
    rows_to_remove = []

    for _, row in processed_nonchase_df.iterrows():
        extracted_desc_raw = row["Extracted Description"]
        clean_desc = row["Clean Description"]
        transaction_amount = row["Amount"]
        row_pre = row.copy()

        # Normalize the extracted description
        ext_desc = tuple(str(extracted_desc_raw).lower().split())

        # Match against historical data
        if ext_desc in category_lookup:
            category = category_lookup[ext_desc]
            categories[category] = pd.concat([categories[category], pd.DataFrame([row])], ignore_index=True)
            rows_to_remove.append(row_pre)
            continue

        # Rule-based fallback categorization
        if "target" in ext_desc:
            row["Description"] = "Target"
            category = "grocery" if transaction_amount > -50 else "shopping"
        elif "walgreens" in ext_desc:
            row["Description"] = "Walgreens"
            category = "grocery" if transaction_amount > -25 else "health"
        elif "amazon" in ext_desc or "amzn" in ext_desc:
            row["Description"] = "Amazon"
            category = "shopping"
        elif "sptsbk" in ext_desc or ("espn" in ext_desc and "bet" in ext_desc) or "caesars" in ext_desc:
            category = "gambling"
        elif "zelle" in ext_desc or "atm" in clean_desc.lower() or "withdrawal" in clean_desc.lower():
            category = "fees"
        elif "apts" in ext_desc:
            category = "bills"
        elif "gas" in ext_desc:
            category = "gas"
        else:
            continue  # Leave it for now in remaining

        categories[category] = pd.concat([categories[category], pd.DataFrame([row])], ignore_index=True)
        rows_to_remove.append(row_pre)

    # Mark uncategorized transactions as "remaining"
    categorized_rows = pd.DataFrame(rows_to_remove)
    if not categorized_rows.empty:
        categories["remaining"] = processed_nonchase_df[
            ~processed_nonchase_df.index.isin(categorized_rows.index)
        ]
    else:
        categories["remaining"] = processed_nonchase_df.copy()

    return categories


def categorize_transactions_second_pass(processed_credit_df):
    categorized_data = {}

    if processed_credit_df is not None:

        bar_credit_df_pre= processed_credit_df[processed_credit_df["Matched Bar"].notna() & processed_credit_df["Category"].str.contains("Food", na = False)]
        bar_credit_df = bar_credit_df_pre.copy()
        categorized_data["bar"] = bar_credit_df

        remaining_credit_df_pre = processed_credit_df[~processed_credit_df.apply(tuple, 1).isin(bar_credit_df_pre.apply(tuple, 1))]
        takeout_credit_df_pre= remaining_credit_df_pre[remaining_credit_df_pre["Matched Takeout"].notna() & remaining_credit_df_pre["Category"].str.contains("Food", na = False)]
        takeout_credit_df= takeout_credit_df_pre.copy()
        takeout_credit_df["Description"] =  takeout_credit_df["Matched Takeout"]
        categorized_data["takeout"]=takeout_credit_df


        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(takeout_credit_df_pre.apply(tuple, 1))]
        potential_restaurant_credit_df = remaining_credit_df_pre[remaining_credit_df_pre["Matched Takeout"].isna() & remaining_credit_df_pre["Category"].str.contains("Food", na=False) & processed_credit_df["Matched Bar"].isna()]
        restaurant_credit_df_pre = potential_restaurant_credit_df[potential_restaurant_credit_df["Matched Restaurant"].notna()]
        restaurant_credit_df = restaurant_credit_df_pre.copy()
        categorized_data["restaurant"] = restaurant_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(restaurant_credit_df_pre.apply(tuple, 1))]
        misc_food_credit_df_pre = remaining_credit_df_pre[remaining_credit_df_pre["Category"] == "Food & Drink"]
        misc_food_credit_df = misc_food_credit_df_pre.copy()
        categorized_data["miscfood"]= misc_food_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(misc_food_credit_df_pre.apply(tuple, 1))]
        grocery_credit_df_pre=remaining_credit_df_pre[remaining_credit_df_pre["Category"].str.contains("Groceries", na = False)]
        grocery_credit_df=grocery_credit_df_pre.copy()
        categorized_data["grocery"]=grocery_credit_df     

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(grocery_credit_df_pre.apply(tuple, 1))]
        rideshare_credit_df_pre = remaining_credit_df_pre[remaining_credit_df_pre["Extracted Description"].apply(lambda x: any(keyword in str(x).lower() for keyword in ("uber", "lyft")))]
        rideshare_credit_df = rideshare_credit_df_pre.copy()
        categorized_data["rideshare"] = rideshare_credit_df
    
        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(rideshare_credit_df_pre.apply(tuple, 1))]
        subs_credit_df_pre= remaining_credit_df_pre[remaining_credit_df_pre["Matched Sub"].notna()]
        subs_credit_df = subs_credit_df_pre.copy()
        categorized_data["subs"]=subs_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(subs_credit_df_pre.apply(tuple, 1))]
        golf_credit_df_pre= remaining_credit_df_pre[remaining_credit_df_pre["Matched Course"].notna()]
        golf_credit_df=golf_credit_df_pre.copy()
        categorized_data["golf"]=golf_credit_df
    
        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(golf_credit_df_pre.apply(tuple, 1))]
        gambling_credit_df_pre= remaining_credit_df_pre[remaining_credit_df_pre["Matched Book"].notna()]
        gambling_credit_df=gambling_credit_df_pre.copy()
        categorized_data["gambling"]=gambling_credit_df


        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(gambling_credit_df_pre.apply(tuple, 1))]
        health_credit_df_pre=remaining_credit_df_pre[(remaining_credit_df_pre["Category"].str.contains("Health", na = False) & remaining_credit_df_pre["Matched Course"].isna()) | remaining_credit_df_pre["Clean Description"].str.contains("barber", na = False)
                                            | remaining_credit_df_pre["Clean Description"].str.contains(" clips", na = False)]
        health_credit_df=health_credit_df_pre.copy()
        categorized_data["health"]=health_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(health_credit_df_pre.apply(tuple, 1))]
        entertainment_credit_df_pre=remaining_credit_df_pre[remaining_credit_df_pre["Category"].str.contains("Entertainment", na = False) | 
                                                (remaining_credit_df_pre["Category"].str.contains("Personal", na = False) & ~remaining_credit_df_pre["Clean Description"].str.contains("cleaners", na = False))
                                                | remaining_credit_df_pre["Clean Description"].str.contains("chicago sport", na = False)]
        entertainment_credit_df=entertainment_credit_df_pre.copy()
        categorized_data["entertainment"]= entertainment_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(entertainment_credit_df_pre.apply(tuple, 1))]
        gas_credit_df_pre=remaining_credit_df_pre[remaining_credit_df_pre["Category"].str.contains("Gas", na = False)]
        gas_credit_df=gas_credit_df_pre.copy()
        categorized_data["gas"]=gas_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(gas_credit_df_pre.apply(tuple, 1))]
        insurance_credit_df_pre=remaining_credit_df_pre[remaining_credit_df_pre["Clean Description"].str.contains("usaa", na = False)]
        insurance_credit_df=insurance_credit_df_pre.copy()
        categorized_data["insurance"]=insurance_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(insurance_credit_df_pre.apply(tuple, 1))]
        car_credit_df_pre= remaining_credit_df_pre[remaining_credit_df_pre["Category"].str.contains("Automotive", na = False)]
        car_credit_df=car_credit_df_pre.copy()
        categorized_data["car"]=car_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(car_credit_df_pre.apply(tuple, 1))]
        fashion_credit_df_pre=remaining_credit_df_pre[(remaining_credit_df_pre["Matched Fashion"].notna() & remaining_credit_df_pre["Category"].str.contains("Shopping", na = False)) | remaining_credit_df_pre["Clean Description"].str.contains("cleaners")]
        fashion_credit_df=fashion_credit_df_pre.copy()
        categorized_data["fashion"]=fashion_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(fashion_credit_df_pre.apply(tuple, 1))]
        shopping_credit_df_pre=remaining_credit_df_pre[remaining_credit_df_pre["Category"].str.contains("Shopping", na = False) | remaining_credit_df_pre["Category"].str.contains("Home", na = False) ]
        shopping_credit_df=shopping_credit_df_pre.copy()
        categorized_data["shopping"]=shopping_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(shopping_credit_df_pre.apply(tuple, 1))]
        transport_credit_df_pre=remaining_credit_df_pre[remaining_credit_df_pre["Matched Transport"].notna()]
        transport_credit_df=transport_credit_df_pre.copy()
        categorized_data["transport"]=transport_credit_df
    
        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(transport_credit_df_pre.apply(tuple, 1))]
        travel_credit_df_pre=remaining_credit_df_pre[remaining_credit_df_pre["Category"].str.contains("Travel", na= False) | remaining_credit_df_pre["Clean Description"].str.contains("chase travel", na= False)] 
        travel_credit_df=travel_credit_df_pre.copy()
        categorized_data["travel"]=travel_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(travel_credit_df_pre.apply(tuple, 1))]
        gifts_credit_df_pre= remaining_credit_df_pre[remaining_credit_df_pre["Category"].str.contains("Gifts", na= False)]
        gifts_credit_df=gifts_credit_df_pre.copy()
        categorized_data["gifts"]=gifts_credit_df
        
        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(gifts_credit_df_pre.apply(tuple, 1))]
        fees_credit_df_pre = remaining_credit_df_pre[(remaining_credit_df_pre["Category"].str.contains("Fees", na= False))]
        fees_credit_df=fees_credit_df_pre.copy()
        categorized_data["fees"]=fees_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(fees_credit_df_pre.apply(tuple, 1))]
        bills_credit_df_pre= remaining_credit_df_pre[remaining_credit_df_pre["Category"].str.contains("Bills") | remaining_credit_df_pre["Category"].str.contains("Professional")]
        bills_credit_df=bills_credit_df_pre.copy()
        categorized_data["bills"]=bills_credit_df

        remaining_credit_df_pre = remaining_credit_df_pre[~remaining_credit_df_pre.apply(tuple, 1).isin(bills_credit_df_pre.apply(tuple, 1))]
        remaining_credit_df=remaining_credit_df_pre.copy()
        categorized_data["remaining"]=remaining_credit_df

        return categorized_data
    
