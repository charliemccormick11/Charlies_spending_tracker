import streamlit as st
import os
import pandas as pd
import utils.data_processing as dp
from dotenv import load_dotenv
from openai import OpenAI
import pagez.spendinggoal as sg
import pagez.currentspending as cs
import utils.open_ai_calls as oaic
import utils.categorization.categorization_combined_spend as ccs
import utils.csv_download as csvd
from datetime import datetime
import io
import time
import logging

st.set_page_config(page_title="Charlie's Spending Tracker", layout="wide", initial_sidebar_state="expanded")

logging.getLogger().setLevel(logging.WARNING)
st.set_option("client.showErrorDetails", False)

secret_key = st.secrets["openai"]["api_key"]
st.session_state.client = OpenAI(
    # This is the default and can be omitted
    api_key=secret_key
)


# Initialize session state variables if they don't exist
if 'processed_credit_df' not in st.session_state:
    st.session_state.processed_credit_df = None
if 'column_info' not in st.session_state:
    st.session_state.column_info = None
if 'spend_df' not in st.session_state:
    st.session_state.spend_df = None
    st.session_state.spend_df_preload = None



if st.session_state.spend_df is not None:
        st.session_state.spend_df["Financial Type"] = "Spending"
        download_spend= st.session_state.spend_df[["Transaction Date", "Description" , "Category" , "Amount", "Year", "Month", "Raw Description", "Raw Amount", "Raw Date", "Financial Type"]]
        
        if "future_categories" in st.session_state:
            download_categories = st.session_state.future_categories

            downloadable_df = pd.concat([download_spend, download_categories])

        else:
            downloadable_df = download_spend



        now = datetime.now()
        datetime_str = now.strftime("%Y-%m-%d %I:%M %p")
        buf = io.StringIO()
        downloadable_df.to_csv(buf, index=False)
        st.download_button(
            label="Download File for Next Session!",
            data=buf.getvalue(),
            file_name='Charlies_Spending_Tracker ' + datetime_str + '.csv',
            mime="text/csv"
        )

        

else:
    st.title("Charlie's Spending Tracker")

tabs = ["Current Spending 📍", "Budgeting Goals 💰", "Future Categorization 📊"]


selected_tab= st.pills("Select a Financial Tool", options = tabs, selection_mode="single")


#Sidebar for Uploading CSV files
#st.session_state.demo_mode = st.sidebar.checkbox("Try Demo Mode (with sample data)!")
#st.sidebar.divider()


relevant_columns = ["Transaction Date", "Description", "Amount", "Category"]


#if st.session_state.demo_mode:
 #   if st.session_state.spend_df is None:
  #      st.session_state.spend_df = pd.read_csv("demo_data.csv")


new_or_returning = st.sidebar.subheader("New or Returning Users")
users = st.sidebar.radio(label = "Have you used this app before?",
options = 
["New Users 💥", "Returning Users ↩️"],
captions=[
    "This is your first time",
    "You've been here before",
    
],
)
st.sidebar.divider()

if users == "New Users 💥":
    st.session_state.credit_card = st.sidebar.selectbox("Select Your Credit Card 💳", options = ["Chase", "Other"])

    st.sidebar.subheader("Upload Credit Card Statements 🧾")
    uploaded_credit=st.sidebar.file_uploader("Credit Card CSV files", type = ["csv"], accept_multiple_files= True)


    uploaded_previous = False



elif users == "Returning Users ↩️":

    st.sidebar.subheader("Upload File From Last Session 📊")
    uploaded_previous_file = st.sidebar.file_uploader("Upload Previous File", type = ["csv"], accept_multiple_files= False)

    st.sidebar.divider()

    st.session_state.credit_card = st.sidebar.selectbox("Select Your Credit Card 💳", options = ["Chase", "Other"])
    st.sidebar.divider()

    st.sidebar.subheader("Upload Credit Card Statements 🧾")
    uploaded_credit=st.sidebar.file_uploader("Upload Credit Card CSV files", type = ["csv"], accept_multiple_files= True)

    uploaded_previous = True

# Add submit button in the sidebar
if uploaded_credit or uploaded_previous:
    if st.sidebar.button("Process Data"):
        with st.spinner("Processing data..."):

            if users == "Returning Users ↩️":
                if uploaded_previous:
                    try:
                        st.session_state.total_df_downloaded = pd.read_csv(uploaded_previous_file, dtype={'Raw Amount': 'float64'})
                        st.session_state.total_df_downloaded['Raw Amount'] = st.session_state.total_df_downloaded['Raw Amount'].map(lambda x: f"{x:.2f}")
                        st.session_state.total_df_downloaded_spending = st.session_state.total_df_downloaded[st.session_state.total_df_downloaded["Financial Type"] == "Spending"]
                        st.session_state.spend_df_preload = st.session_state.total_df_downloaded_spending.reset_index()
                        st.session_state.previous_categories = st.session_state.total_df_downloaded[st.session_state.total_df_downloaded["Financial Type"] == "Future Category"]
                        st.session_state.previous_categories = st.session_state.previous_categories.reset_index()

                    except:
                        st.error("Please ensure you select you include your file from last session in the first file upload, not a new credit statement!")
                        time.sleep(5)
                        st.rerun()
            if uploaded_credit:
                try:
                    total_credit_df= oaic.open_ai_headers(uploaded_credit, st.session_state.credit_card, st.session_state.client)

                except:
                    st.error("Please ensure you select 'Other' on the sidebar for credit card if you don't use Chase!")
                    time.sleep(5)
                    st.rerun()

                # Process the credit transactions
                st.session_state.processed_credit_df=dp.process_credit_transactions(total_credit_df)

                ccs.combine_all_spending(st.session_state.credit_card)


            csvd.download_as_csv()

        

if selected_tab == "Current Spending 📍" and st.session_state.spend_df is not None:
    cs.current_spending_page(relevant_columns, st.session_state.client)

    
if selected_tab == "Budgeting Goals 💰" and st.session_state.spend_df is not None:
    sg.budgeting_page(st.session_state.spend_df, st.session_state.client)

if selected_tab =="Future Categorization 📊" and st.session_state.spend_df is not None:
    st.markdown('### Future Categorization 📊')
    st.write("""This page allows you to categorize how you want future transactions to be categorized! Press on the category of a transaction name from the
             dropdown, and hit the submit button below! 📊""")

    unique_transactions = st.session_state.spend_df[["Description", "Category"]].drop_duplicates(subset=["Description"])

            # Show editor
    edited_df = st.data_editor(
        unique_transactions,
        column_config=st.session_state.column_config,
        disabled=[col for col in unique_transactions.columns if col != "Category"],
        column_order=["Description", "Category"],
        key="category_data_editor",
        use_container_width=True,
        hide_index=True
    )

    category_changer = st.button("Press to Save Category Selections For Next Session!")

    if category_changer:
        st.session_state.future_categories = edited_df
        st.session_state.future_categories["Financial Type"] = "Future Category"

        st.success("Category Updated!")
        time.sleep(2)
        st.rerun()


    
elif (selected_tab not in ["Current Spending 📍", "Budgeting Goals 💰", "Future Categorization 📊"]) and (st.session_state.spend_df is not None):
    st.markdown("""
    ### **Current Spending 📍**  
    Get a clear picture of your spending habits. Use the year and month dropdowns to explore how much you’ve spent in each category, how often you visit your favorite places, and how much you spend there.  
    You can also re-categorize individual transactions to refine your financial data.  
    **Note:** Don’t forget to click the **“Download”** button on this page to save your categorized transactions. You’ll need this file next time you return to the app!
    
    ---
    
    ### **Budgeting Goals 💰**  
    Track your monthly spending across variable categories. Your budget goal for each category is based on the average of your **6 lowest-spending months** over the past year. For the current month, we’ll pro-rate the target to show whether you’re on track.  
    To help you improve, **BudgetGPT** analyzes your recent transactions and suggests actionable strategies to cut spending in each category.
    
    ---
    
    ### **Future Categorization 📊**  
    Customize how each vendor is categorized moving forward. After uploading your previously saved file under **"Returning Users ↩️"**, the app will automatically apply your preferences to new transactions — so everything stays organized your way.
    """)


elif st.session_state.spend_df is None:
   # Description with more emphasis
    st.markdown("""
    This tool helps you **analyze** your spending habits by turning your credit card transactions into meaningful insights!  
    📥 Simply upload your **credit card statements** from your credit card company in **CSV** format, and watch your data get neatly categorized.

    💡 If you don't have a Chase card, many transactions may be categorized as "remaining." No worries! With or without a Chase card, we can send your transactions to **ChatGPT** for quick categorization — and you can always fine-tune them manually later!

    🔎 Want to demo the app? Ask [ChatGPT](https://chatgpt.com/) to make you a fake credit card statement in CSV format and upload it to this tool!

    ---
    
                
    ### ChatGPT Agreement:           
    """)

    st.info("This app is for personal use and educational purposes only. The developer is not responsible for financial decisions made based on this tool. Use at your own risk.")

    st.session_state.agree = st.checkbox("I understand that when I use AI categorization, my transaction data **(Descriptions and Amounts)** will be sent to OpenAI for processing to automatically categorize my transactions. I can change any categories afterward and this feature is optional. **No other information is shared**")
    if st.session_state.agree:
        st.info("""Great! Press "Process Data" to begin!""")

    
