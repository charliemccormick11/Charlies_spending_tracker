import streamlit as st
import os
import pandas as pd
import json
import io

def open_ai_headers(uploaded_credit, credit_card, client):

    st.sidebar.success(f"{len(uploaded_credit)} credit file(s) uploaded.")
    dfs_credit = [pd.read_csv(file, header=None) for file in uploaded_credit]
    total_credit_df = pd.concat(dfs_credit, ignore_index=True)

    credit_sample = total_credit_df.head(1)
    #Code that is calling the open AI API
    # Modify prompt to conditionally check the credit card type
    prompt = f"""
    I have uploaded the following transaction header, or, first row:

    {credit_sample}

    Please:
    1. Check if this is a header.
    1.1 If the first row contains column names (e.g., "Transaction Date", "Amount"), set 'header' to True.
    1.2 If the first row contains data (e.g., values like "2023-01-01", "100"), set 'header' to False.
    2. Regardless of if there's a header, provide the column indices (starting from 0) for the following columns:
    - Transaction Date
    - Description (cannot be null) 
    - Amount
    - Category (index is likely 3)
    3. If there are two amount columns (Credit and Debit), provide their indices and include them as "credit" and "debit".
    3.4 If there is one amount column, put it as 'debit'.
    4. Return ONLY the response as a Python JSON dictionary with the following keys: 'header', 'transaction_date', 'description', 'credit', 'debit', 'category'. No additional text, explanations, or strings.
    5. Remove anything else but the dictionary
    """

    # Additional check before sending the prompt
    if credit_card == "Chase":
        # If it's Chase, add additional logic to handle category column index if necessary
        prompt = prompt.replace("Please:", "Please that the category column index is provided as this is a Chase credit card!")

    else:
        prompt = prompt.replace("- Category (Food & Drink, Groceries, Entertainment, Shopping, etc.) index is likely 3", "")
        prompt = prompt.replace(", 'category'.", ".")


    completion = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{
        "role": "user",
        "content": prompt,
    }], temperature=0
    )

    # Parse OpenAI response into a dictionary
    try:
    # Parse the JSON response
        st.session_state.column_info = json.loads(completion.choices[0].message.content)
        if not isinstance(st.session_state.column_info['description'], int):
            st.session_state.column_info['description'] = 3
        

        
    except Exception as e:
        st.error(f"Please ensure you are uploading a CSV file listing the Transaction Date, Description, and Amount")
        st.session_state.column_info = {}
    # Process credit data
    if not st.session_state.column_info:
        st.error("Error: No valid data found in the response")
        st.stop()
    else:
        if st.session_state.column_info.get('header') == True:
            # If the header is present, assign the first row as column names and remove it from data
            total_credit_df.columns = total_credit_df.iloc[0]
            total_credit_df = total_credit_df.drop(0, axis=0).reset_index(drop=True)
            
            # Assign columns based on OpenAI's response
            total_credit_df["Transaction Date"] = total_credit_df.iloc[:, st.session_state.column_info['transaction_date']]
            total_credit_df["Description"] = total_credit_df.iloc[:, st.session_state.column_info['description']]
            if st.session_state.credit_card == "Chase" and (st.session_state.column_info['category'] is not None):
                total_credit_df["Category"] = total_credit_df.iloc[:, st.session_state.column_info['category']]
            total_credit_df["Amount"] = total_credit_df.iloc[:, st.session_state.column_info['debit']]
            
        # Handle missing Category column
            if credit_card == "Other":
                total_credit_df = total_credit_df[["Transaction Date", "Description", "Amount"]]
            else:
                total_credit_df = total_credit_df[["Transaction Date", "Description", "Category", "Amount"]]
        elif st.session_state.column_info['header'] == False:
            # For non-Chase statements without headers, assign columns based on indices
            total_credit_df["Transaction Date"] = total_credit_df.iloc[:, st.session_state.column_info['transaction_date']]
            total_credit_df["Description"] = total_credit_df.iloc[:, st.session_state.column_info['description']]
            total_credit_df["Amount"] = total_credit_df.iloc[:, st.session_state.column_info['debit']]
            # Only keep the three essential columns since this is a non-Chase statement
            total_credit_df = total_credit_df[["Transaction Date", "Description", "Amount"]]
            
        else:   
            st.error("Error: No header found in the data")
            st.stop()
        
        return total_credit_df

    
def open_ai_random_categorization(client):

    if st.session_state.remaining_credit_df is not None:
        try:
            # Get remaining transactions
            readable_remaining_df = st.session_state.spend_df_newload[
                st.session_state.spend_df_newload["Category"] == "Remaining"
            ]
            readable_remaining_df_feed = readable_remaining_df[["Transaction Date", "Description", "Amount"]]
    
            st.write(f"Total transactions being categorized by ChatGPT🚀: {len(readable_remaining_df_feed)}")
    
            # Initialize progress bar and lists to collect all results
            batch_size = 40
            all_names = []
            all_categories = []
            progress_bar = st.progress(0)
            total_batches = (len(readable_remaining_df_feed) - 1) // batch_size + 1
    
            # Loop over batches
            for i in range(0, len(readable_remaining_df_feed), batch_size):
                batch = readable_remaining_df_feed.iloc[i:i+batch_size]
    
                prompt = f"""
    You are a categorization assistant for personal finance transactions.
    
    Categories for transaction classification:
    - Alcohol 🍺
    - Dining 🍴
    - Takeout 🍔
    - Groceries 🛒
    - Golf ⛳
    - Gambling 🎰
    - Misc Entertainment🎟️
    - Fashion 👚
    - Misc Shopping 🚀🛍️
    - Rideshare 🚘💼
    - Misc Travel ✈️
    - Gas ⛽
    - Public Transportation 🚍
    - Insurance 🛡️
    - Misc Car 🚗
    - Health 💪
    - Gifts/Donations 🎁🙏
    - Bills 📜
    - Subscriptions 💳🎬
    - Fees & Adjustments ⚖️
    - Remaining (if none of the above seem applicable)
    
    Rules for categorization:
    - If a transaction fits a category, use that category. If unsure, categorize it as "Remaining".
    - Chain restaurants should be categorized as "Takeout 🍔", so be sure to identify the name if applicable.
    - Ensure that every transaction receives a category.
    - If transaction name is null, put "Remaining" as the category
    
    Output Format:
    - Your output must be a **JSON dictionary** with the key "Category". 
    - The value of "Category" should be a **list** of categories, one per transaction, in the same order as the transactions in the input data.
    - The **number of categories** returned must match the **number of transactions** exactly. If there are 30 transactions, there should be 30 values in the list!
    - Only the categories should be returned — no other text, explanations, or additional information.
    
    Here are the transactions to categorize:
    {batch.to_csv(index=False, header=False)}
    """
    
                completion = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.1
                )
    
                try:
                    result_dict = json.loads(completion.choices[0].message.content)
                    all_categories.extend(result_dict.get("Category", []))
                except Exception as e:
                    st.error(f"Error processing batch {i // batch_size + 1}: {str(e)}")
                    all_categories.extend(["Remaining"] * len(batch))
    
                # Update progress bar
                progress_bar.progress(min((i + batch_size) / len(readable_remaining_df_feed), 1.0))
    
            # Merge results into a DataFrame
            categorized_df = pd.DataFrame({
                "Category": all_categories
            })
            # Join back with original DataFrame if needed
            final_df = readable_remaining_df_feed.copy()
            final_df["Category"] = categorized_df["Category"].values
    
            st.session_state.spend_df_newload.loc[st.session_state.spend_df_newload["Category"] == "Remaining", "Category"] = final_df["Category"]
            st.success("Categorization successful! 🎉")

    
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")


def open_ai_budgetGPT(alcohol_low_value, takeout_low_value, grocery_low_value, shopping_total_low_value, entertainment_total_low_value, health_low_value, no_bills_spending_low_value, dataframe_selected, category_selected, client):
    try:
        prompt = f"""You are a financial advisor helping a user with their personal finance tracker. The page displays target budget amounts for the following categories based on the average of the lowest X spending months in that category from the previous year. 

        Here are the target values:
        - Alcohol 🍺: {alcohol_low_value}
        - Takeout 🍔: {takeout_low_value}
        - Groceries 🛒: {grocery_low_value}
        - Shopping 👚🛍️: {shopping_total_low_value}
        - Entertainment 🎰🎟️: {entertainment_total_low_value}
        - Health 💪: {health_low_value}
        - Total Spending (No Bills) 💰: {no_bills_spending_low_value}

        The user has selected the following category: {category_selected}.

        You are to provide 4 actionable strategies to help the user save money in this category (except for the total spending category. Your advice should be based on their spending patterns in this category and may include suggestions such as specific meals, recipes, and tips for saving on groceries. Feel free to think creatively but limit the advice to 4 tips. 
        However, for "Total Spending (No Bills) 💰", you can include up to 10 strategies!

        Additionally, provide insights based on the user's Year-to-Date transaction history for the selected category, showing evidence you've reviewed the data and observed any patterns or trends.

        Here is the YTD transaction history for the selected category, ordered by date:
        {dataframe_selected}

        Focus only on the selected category. Provide concrete examples and avoid general advice. Use bullet points and emojis where relevant. 
        
        
        This app is a spending tracker. Using a spending tracker should NOT be a suggestions. As they are already using a spending tracker."""

        completion = client.chat.completions.create(
                    model="gpt-4-turbo",  # Using faster model
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.1,  # Lower temperature for more consistent results
                    max_tokens=1000  # Limit response size for faster processing
                )

        # Display the response
        st.write(completion.choices[0].message.content)

    except Exception as e:
        st.error(f"An error occurred while getting advice: {str(e)}")
        st.info("Please try again or check your internet connection.")
