import streamlit as st
import utils.categorization.categorization_credit as cg
import pandas as pd
from utils.data_processing import title_names
import utils.open_ai_calls as oaic


def combine_all_spending(credit_card):
    if st.session_state.processed_credit_df is not None:
        if 'previous_categories' in st.session_state:
            categorized_previous= cg.categorize_previous_transactions(st.session_state.processed_credit_df)[0]
            remaining_transactions_returning = cg.categorize_previous_transactions(st.session_state.processed_credit_df)[1]
            data_to_categorize = remaining_transactions_returning

        else:
            data_to_categorize = st.session_state.processed_credit_df

        if credit_card == "Chase":
            categorized_data = cg.categorize_first_pass(data_to_categorize)
            remaining_credit_df = categorized_data.get("remaining")
            if not remaining_credit_df.empty:
                remaining_credit_categorized = cg.categorize_transactions_second_pass(remaining_credit_df)
                if remaining_credit_categorized:
                    merged_dict = {}

                    for key in categorized_data:
                        if key in remaining_credit_categorized:
                            merged_dict[key] = pd.concat([categorized_data[key], remaining_credit_categorized[key]], ignore_index=True)   

                    categorized_data = merged_dict

        else:
            categorized_data = cg.categorize_first_pass(data_to_categorize)

    



        bar_df = categorized_data.get("bar")
        restaurant_df = categorized_data.get("restaurant")
        takeout_df = categorized_data.get("takeout")
        grocery_df = categorized_data.get("grocery")
        misc_food_df = categorized_data.get("miscfood")
        golf_df = categorized_data.get("golf")
        gambling_df = categorized_data.get("gambling")
        entertainment_df = categorized_data.get("entertainment")
        fashion_df = categorized_data.get("fashion")
        shopping_df = categorized_data.get("shopping")
        rideshare_df = categorized_data.get("rideshare")
        travel_df = categorized_data.get("travel")
        gas_df = categorized_data.get("gas")
        transport_df = categorized_data.get("transport")
        insurance_df = categorized_data.get("insurance")
        car_df = categorized_data.get("car")
        health_df = categorized_data.get("health")
        gifts_df = categorized_data.get("gifts")
        bills_df = categorized_data.get("bills")
        subs_df = categorized_data.get("subs")
        fees_df = categorized_data.get("fees")

        if credit_card == "Chase":
            if remaining_credit_categorized:
                st.session_state.remaining_credit_df = remaining_credit_categorized.get("remaining")

            else:
                st.session_state.remaining_credit_df = pd.DataFrame()

        else:
            st.session_state.remaining_credit_df = categorized_data.get("remaining")


        categories = {
            "Alcohol 🍺": bar_df,
            "Dining 🍴": restaurant_df,
            "Takeout 🍔": takeout_df,
            "Groceries 🛒": grocery_df,
            "Misc Food 🚀🍔🍴": misc_food_df,
            "Golf ⛳": golf_df,
            "Gambling 🎰": gambling_df,
            "Misc Entertainment🎟️": entertainment_df,
            "Fashion 👚": fashion_df,
            "Misc Shopping 🚀🛍️": shopping_df,
            "Rideshare 🚘💼": rideshare_df,
            "Misc Travel✈️": travel_df,
            "Gas ⛽": gas_df,
            "Public Transporation 🚍": transport_df,
            "Insurance 🛡️": insurance_df,
            "Misc Car🚗": car_df,
            "Health 💪": health_df,
            "Gifts/Donations 🎁🙏": gifts_df,
            "Bills 📜": bills_df,
            "Subscriptions 💳🎬": subs_df,
            "Fees & Adjustments ⚖️": fees_df,
            "Remaining": st.session_state.remaining_credit_df
        }
        
        for category, df in categories.items():
            df["Category"] = category
            
    
        # Concatenate all the dataframes into a single dataframe
        combined_data = pd.concat(categories.values(), ignore_index=True)
    
        st.session_state.spend_df_newload = combined_data
        if st.session_state.agree:
            oaic.open_ai_random_categorization(st.session_state.client)
    
        if 'previous_categories' in st.session_state:
            st.session_state.spend_df_newload = pd.concat([st.session_state.spend_df_newload, categorized_previous], ignore_index=True)

        #st.dataframe(st.session_state.spend_df_newload)
    
        st.session_state.spend_df_newload["Description"]=st.session_state.spend_df_newload["Clean Description"]
        st.session_state.spend_df_newload["Description"] = st.session_state.spend_df_newload["Description"].astype(str).apply(title_names)
    
            
