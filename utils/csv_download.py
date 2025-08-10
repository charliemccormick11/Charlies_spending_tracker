import streamlit as st
import utils.data_processing as dp
import boto3
from io import StringIO
import pandas as pd


def download_as_csv():
    
    subset_cols = ["Raw Description", "Raw Amount", "Raw Date"]
    if st.session_state.spend_df_preload is not None:
        st.session_state.spend_df_preload["Dataset"] = "spending"
        if (st.session_state.processed_credit_df is not None):
            new_transactions = dp.filter_new_transactions(st.session_state.spend_df_newload, st.session_state.spend_df_preload, subset_cols)
            st.session_state.spend_df = pd.concat([st.session_state.spend_df_preload, new_transactions], ignore_index=True)
            st.session_state.spend_df_upload= st.session_state.spend_df[["Transaction Date", "Description" , "Category" , "Amount", "Year", "Month", "Raw Description", "Raw Amount", "Raw Date"]]
            st.dataframe(st.session_state.spend_df)

        else:
            st.session_state.spend_df = st.session_state.spend_df_preload

    else:
        if (st.session_state.processed_credit_df is not None):
            st.session_state.spend_df = st.session_state.spend_df_newload
            st.session_state.spend_df_upload= st.session_state.spend_df[["Transaction Date", "Description" , "Category" , "Amount", "Year", "Month", "Raw Description", "Raw Amount", "Raw Date"]]


    if 'all_categories' not in st.session_state:
        st.session_state.spend_df['Category'] = st.session_state.spend_df['Category'].astype(str)
        st.session_state.all_categories = sorted(set(st.session_state.spend_df['Category'].unique()))
    else:
        st.session_state.spend_df['Category'] = st.session_state.spend_df['Category'].astype(str)
        # Only update if the underlying data has changed
        current_categories = set(st.session_state.spend_df['Category'].unique())
        if current_categories != set(st.session_state.all_categories):
            st.session_state.all_categories = sorted(current_categories)
    
    # Cache column configuration to avoid recreating on every render
    if 'column_config' not in st.session_state or st.session_state.get('column_config_categories') != st.session_state.all_categories:
        st.session_state.column_config = {
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=st.session_state.all_categories,
                required=True
            )
        }
        st.session_state.column_config_categories = st.session_state.all_categories.copy()

    #Designated type of row in downloadable CSV
    st.session_state.spend_df["Financial Type"] = "Spending"


    #code setting up future categories
    st.session_state.future_categories = st.session_state.spend_df[["Description", "Category"]].drop_duplicates(subset=["Description"])
    st.session_state.future_categories["Financial Type"] = "Future Category"
