import streamlit as st
import os
import pandas as pd
import json
import io

def open_ai_headers(uploaded_credit, credit_card, client):


    st.sidebar.success(f"{len(uploaded_credit)} credit file(s) uploaded.")
    dfs_credit = [pd.read_csv(file, header= None) for file in uploaded_credit]
    total_credit_df = pd.concat(dfs_credit, ignore_index=True)

    credit_sample = total_credit_df.head(15)
    #Code that is calling the open AI API
    st.dataframe(credit_sample)
    
    prompt = f"""
    I have uploaded the following CSV data:
    
    {credit_sample}
    
    Please:
    1. Determine if there is a header row in the data:
       - If the first row contains column names (e.g., "Transaction Date", "Amount"), set 'header' to True.
       - If the first row contains data (e.g., values like "2023-01-01", "100"), set 'header' to False.
    
    2. Identify the following columns based on their names (case-sensitive) and return their column indices (starting from 0):
       - Transaction Date
       - Description (names of the places where the purchases were made)
       - Amount
       - Category (if present)
       
       Make sure the column names are exact. If any of these columns are missing or labeled differently, provide your best guess for the column's index. **Do not return null** for the transaction name column (Description). Always make your best guess for the transaction name column, even if it may be incorrect.
    
    3. The transaction name column (Description) is **always the unique name of a merchant**. The name may be in **all caps** or have variations in formatting, but it will represent the merchant or place where the transaction occurred.
    
    4. If there are two amount columns (Credit and Debit), provide their indices and label them as 'credit' and 'debit'. If only one amount column exists, label it as 'debit'.
    
    5. Exclude any rows that appear to be payments to a credit card (such as online payments or payments to financial institutions). Identify payments by their description.
    
    6. **The transaction name column (Description) must never be null**. Even if the description is unclear, missing, or in an unusual format (like all caps), make your best guess for the column index and provide it. If the transaction name is missing or ambiguous, provide your best guess (even if wrong) and proceed with categorization.
    
    7. Return the response **ONLY as a Python JSON dictionary** with the following keys and values:
       - 'header' : Boolean value (True or False)
       - 'transaction_date' : Column index for "Transaction Date" (or `null` if not found)
       - 'transaction_name' : Column index for "Description" (NEVER null, even if guessed)
       - 'credit' : Column index for "Credit" (or `null` if not found)
       - 'debit' : Column index for "Debit" (or `null` if not found)
       - 'category' : Column index for "Category" (or `null` if not found)
    
       Ensure that **none of these columns have the same index number**. If any column is missing or mislabeled, provide the best guess or `null` where necessary.
    
    Please ensure the JSON format is **consistent** regardless of whether the header row is present or not. Do **not** include any additional text, explanations, or strings. The output should **only** be a **JSON dictionary**, nothing else!
    
    The response must be in a valid JSON format and contain no extra information!
    """

    completion = client.chat.completions.create(
    model="gpt-4",
    messages=[{
        "role": "user",
        "content": prompt
    }]
    )

    # Parse OpenAI response into a dictionary
    try:
    # Parse the JSON response
        st.session_state.column_info = json.loads(completion.choices[0].message.content)
        st.write(st.session_state.column_info)

        
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
            total_credit_df["Description"] = total_credit_df.iloc[:, st.session_state.column_info['transaction_name']]
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
            total_credit_df["Description"] = total_credit_df.iloc[:, st.session_state.column_info['transaction_name']]
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
            prompt = f"""
            You are a categorization assistant for personal finance transactions.
            
            Here are the categories that a transaction can be assigned:
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
            
            Rules for categorization:
            - **Chain restaurants** should be categorized as "Takeout 🍔". Be sure to identify the name of the restaurant if applicable and classify it correctly.
            - **Do not leave any transactions uncategorized** unless there is absolutely no appropriate category available. Ensure every transaction gets one of the categories listed above.
            - If a transaction is unclear, try your best to place it in the most appropriate category based on the description.
            - **Here are the column headers for the CSV**:
              - "Transaction Date"
              - "Description"
              - "Amount"
            
            Categorize the following transactions below based on the descriptions, ensuring you assign them the appropriate category from the list above.
            
            Transactions to categorize:
            {readable_remaining_df_feed.to_csv(index=False)}
            
            Return the results as a SINGLE-COLUMN DATAFRAME. The column header should be "Category". Remember - DataFrame!!
            Ensure the number of rows in the output exactly matches the number of rows in the input.
            
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
                result_csv = completion.choices[0].message.content

                st.dataframe(result_csv)
                # Convert the CSV content into a DataFrame
                remaining_categorized = pd.read_csv(io.StringIO(result_csv))

            except Exception as e:
                st.error(f"Error processing batch: {str(e)}")
                return


            # Update the Category column in the original readable_remaining_df
            readable_remaining_df["Category"] = remaining_categorized["Category"].values
            


            # Update the main spend_df_newload with the new categories
            st.session_state.spend_df_newload.loc[st.session_state.spend_df_newload["Category"] == "Remaining", "Category"] = readable_remaining_df["Category"].values
            
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
