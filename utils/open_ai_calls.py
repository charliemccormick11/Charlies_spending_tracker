import streamlit as st
import os
import pandas as pd
import json
import io

def open_ai_headers(uploaded_credit, credit_card, client):

    st.sidebar.success(f"{len(uploaded_credit)} credit file(s) uploaded.")
    dfs_credit = [pd.read_csv(file, header=None) for file in uploaded_credit]
    total_credit_df = pd.concat(dfs_credit, ignore_index=True)

    credit_sample = total_credit_df.head(5)
    #Code that is calling the open AI API
    # Modify prompt to conditionally check the credit card type
    prompt = f"""
    I have uploaded the following CSV data:

    {credit_sample}

    Please:
    1. Check if there is a header row in the data.
    1.1 If the first row contains column names (e.g., "Transaction Date", "Amount"), set 'header' to True.
    1.2 If the first row contains data (e.g., values like "2023-01-01", "100"), set 'header' to False.
    2. Regardless of if there's a header, provide the column indices (starting from 0) for the following columns:
    - Transaction Date
    - Description (in all capital letters, names of merchants) 
    - Amount
    - Category (Food & Drink, Groceries, Entertainment, Shopping, etc.) index is likely 3
    4. If there are two amount columns (Credit and Debit), provide their indices and include them as "credit" and "debit".
    4.4 If there is one amount column, put it as 'debit'.
    5. Return ONLY the response as a Python JSON dictionary with the following keys: 'header', 'transaction_date', 'description', 'credit', 'debit', 'category'. No additional text, explanations, or strings. Only return the dictionary, nothing else. Make format identical for with or without headers!
    6. Remove anything else but the dictionary and don't display as a code block
    7. Nothing can be null
    """

    # Additional check before sending the prompt
    if credit_card == "Chase":
        # If it's Chase, add additional logic to handle category column index if necessary
        prompt = prompt.replace("Please:", "Please that the category column index is provided as this is a Chase credit card!")

    else:
        prompt = prompt.replace("Category:", " ")
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

        
    except Exception as e:
        st.error(f"Error parsing OpenAI response: {str(e)}")
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
            readable_remaining_df = st.session_state.spend_df_newload[st.session_state.spend_df_newload["Category"]=="Remaining"]
            readable_remaining_df_feed = readable_remaining_df[["Transaction Date", "Description" , "Amount"]]
            readable_remaining_df_feed.reset_index()
            st.write(len(readable_remaining_df_feed))
            st.dataframe(readable_remaining_df_feed)
            prompt = f"""
        You are a categorization assistant for personal finance transactions.

        Categories for transaction classification:
        - Alcohol 🍺
        - Dining 🍴
        - Takeout 🍔
        - Groceries 🛒
        - Golf ⛳
        - Gambling 🎰
        - Misc Entertainment 🚀
        - Fashion 👚
        - Misc Shopping 🚀
        - Rideshare 🚘💼
        - Misc Travel 🚀
        - Gas ⛽
        - Public Transportation 🚍
        - Insurance 🛡️
        - Misc Car 🚀
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
        - The **number of categories** returned must match the **number of transactions** exactly. If there are 100 transactions, there should be 100 values in the list!
        - Only the categories should be returned — no other text, explanations, or additional information.

        Here are the transactions to categorize:
        {readable_remaining_df_feed.to_csv(index=False, header=False)}

        """


            completion = client.chat.completions.create(
            model="gpt-4",  # Using a more stable model for categorization
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.1  # Low temperature for more predictable results
            )
            
            try:
                # Parse the result from the GPT response
                result_dict = json.loads(completion.choices[0].message.content)

                st.write(result_dict)
                # Convert the CSV content into a DataFrame
                remaining_categorized = pd.DataFrame(result_dict)

            except Exception as e:
                st.error(f"Error processing batch: {str(e)}")
                return


            # Update the Category column in the original readable_remaining_df
            readable_remaining_df["Category"] = remaining_categorized["Category"].values
            


            # Update the main spend_df_newload with the new categories
            st.session_state.spend_df_newload.loc[st.session_state.spend_df_newload["Category"] == "Remaining", "Category"] = readable_remaining_df["Category"]
            
            st.success("Categorization successful! 🎉")




                
        except Exception as e:
            st.error(f"Error in categorization process: {str(e)}")


def open_ai_budgetGPT(alcohol_low_value, takeout_low_value, grocery_low_value, shopping_total_low_value, entertainment_total_low_value, health_low_value, no_bills_spending_low_value, dataframe_selected, category_selected, client):
    try:
        prompt = f"""You are a financial advisor helping a user with their personal finance tracker. The page displays target budget amounts for the following categories based on the average of the lowest X spending months in that category from the previous year. 

        Here are the target values:
        - Alcohol 🍺: {alcohol_low_value}
        - Takeout 🍔: {takeout_low_value}
        - Groceries 🛒: {grocery_low_value}
        - Shopping 👚🚀: {shopping_total_low_value}
        - Entertainment 🎰🚀: {entertainment_total_low_value}
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
