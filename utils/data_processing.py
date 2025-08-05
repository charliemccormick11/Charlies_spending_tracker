import pandas as pd 
import utils.categorization.bars as bars
import utils.categorization.golf as golf
import utils.categorization.uberlyft as uberlyft
import utils.categorization.Food as Food
import utils.categorization.takeout as takeout
import utils.categorization.fashion as fashion
import streamlit as st

def transaction_name_parsing(df):
    df["Clean Description"] = (
        df["Description"]
        .str.replace('TST\*', '', regex=True)  # Remove "TST*" from descriptions
        .str.replace('GLF', '', regex=True)
        .str.replace('CPI*', '', regex=True)
        .str.replace('CTLP', '', regex = True)
        .str.replace(r'\bLEYE\b', '', regex = True)
        .str.replace(r'\bDD \*\s*', '', regex=True)
        .str.replace(r'\bSQ\b', '', regex=True)  
        .str.replace(r'\bLGA\b', '', regex=True)
        .str.replace(r'\bPY\b', '', regex=True)
        .str.replace("'", '', regex=True)      # Remove apostrophes
        .str.replace("&", '', regex=True)      # Remove ampersands
        .str.replace(r"\bamp\b", '', regex=True)      # Remove ampersands
        .str.replace("\+", '', regex=True)     # Remove plus signs
        .str.replace("\-", ' ', regex=True)     # Remove plus signs
        .str.replace("\.", ' ', regex=True) 
        .str.replace("\;", '', regex=True) 
        .str.replace("\*", '', regex=True) 
        .str.replace("SQ", '', regex=True) 
        .str.replace("@", ' ', regex=True) 
        .str.replace(",", '', regex=True) 
        .str.replace("\/", '', regex=True) 
        .str.replace(r'\b\w*\d\w*\b', '', regex=True)
        .str.replace(r'\bleye\b', '' )  # Remove single-letter words
        .str.replace('#', '', regex=True)
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()                            # Remove trailing/leading spaces
        .str.lower()
        .str.replace("chicago il", '')
        .str.replace("madison wi", '')
        .str.replace('web id:', '') 
        .str.replace("schaumburg il", '')     )               # Convert to lowercase
    return df



def check_amount_sign(df):
    # Make a copy of the DataFrame to avoid modifying the original
    df = df.copy()
    
    # Ensure Amount column is numeric
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    
    # Get first 5 rows of Amount column, handling NaN values
    first_5 = df['Amount'].head(5).dropna()
    
    # If we have less than 5 rows, use all available rows
    if len(first_5) < 5:
        first_5 = df['Amount'].dropna()
    
    # Count negative values
    negative_count = sum(1 for x in first_5 if x < 0)
    
    # If 4 or more are negative, make all amounts negative
    if negative_count >= 4:
        df['Amount'] = -(df['Amount'])
    else:
        df['Amount'] = abs(df['Amount'])
    
    return df

#Extracting Key Transaction Words
def extract_description(name):
    generic_words = {"on", "at", "and", "the", "by", "of"}
    words=name.split()
    keywords = [
        word for word in words 
        if word.lower() not in generic_words  # Remove generic words
        
    ]
    if len(keywords) == 1:
        return (keywords[0], )

    elif len(keywords) >= 2:
        return (keywords[0], keywords[1])

    return tuple()

def process_credit_transactions(df):

    df["Raw Description"]=df["Description"].astype(str)
    df["Raw Amount"]=df["Amount"].astype(str)
    df["Raw Date"]=df["Transaction Date"].astype(str)
    df["Description"]=df["Description"].astype(str)
    df["Source"]= "credit"


    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = check_amount_sign(df)

    "Cleans and Processes Transactions"
    #Making Each Transaction Simpler and Readable
    df= transaction_name_parsing(df)

    df["Extracted Description"] = df["Clean Description"].apply(extract_description)
    sportsbooks=["draftkings", "hard rock", "caesars", "fanduelsbkprimary", "mgmbetmgm", "prizepicks", "espn bet"]
    pub_transport=["ventra", "metra", "paygo"]
    subscriptions= ["netflix", "microsoftxbox", "help max", "apple"] 
    def match_sportsbook(desc):
        for item in sportsbooks:
            if item in desc:
                return item
    def match_transport(desc):
        for item in pub_transport:
            if item in desc:
                return item
            
    def match_sub(desc):
        for item in subscriptions:
            if item in desc and ("applepay" not in desc):
                if item == "help max":
                    return "hbo max"
                
                else:
                    return item
            
    df.loc[(df["Extracted Description"].apply(lambda x: any("walgreens" in str(item).lower() for item in x))) & (df["Amount"] > -25),"Category"] = "Groceries"
    df.loc[(df["Extracted Description"].apply(lambda x: any("target" in str(item).lower() for item in x))) & (df["Amount"] > -50),"Category"] = "Groceries"
    df = df[~df["Clean Description"].str.contains("online payment", na=False)]
    df = df[~df["Clean Description"].str.contains("payment", na=False)]
    df["Matched Bar"] = df["Extracted Description"].apply(bars.matched_credit_bar_transaction)
    df["Matched Sub"]=df["Clean Description"].apply(match_sub)
    df["Matched Book"] = df["Clean Description"].apply(match_sportsbook)
    df["Matched Transport"]=df["Clean Description"].apply(match_transport)
    df["Matched Course"]=df["Description"].apply(golf.matched_credit_course_transaction)
    df["Matched Takeout"]=df["Extracted Description"].apply(takeout.matched_credit_takeout_transaction)
    df["Matched Restaurant"]=df["Extracted Description"].apply(takeout.matched_credit_restaurant_transaction)
    df["Matched Fashion"]=df["Clean Description"].apply(fashion.matched_fashion_transaction)

    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors='coerce')
    df = df.dropna(subset=["Transaction Date"])
    df["Year"] = df["Transaction Date"].dt.year.astype(str)
    df["Month"] = df["Transaction Date"].dt.month
    
    return df



def title_names(title):
    generic_words = {"on", "at", "and", "by", "of"}
    title=title.lower()
    title = title.replace("tst*", "")
    title = title.replace("*", "")
    title = title.replace("py", "")
    title = title.replace("sq", "")
    title = title.replace("amp;", "")
    title = title.replace("#", "")
    title=title.replace(r'\b\d{3,}\b', '')
    if ("wrigley field" or "wrigleyfield") in title:
        return "Wrigley Field"
    titles=title.split()

    title_cased_name = ' '.join(word.capitalize() if word not in generic_words else word for word in titles)
    
    return title_cased_name

def health_matched(ext_description):
    if ("xsport" or "pxsport"or "fitness") in ext_description:
        return "yes"


def filter_new_transactions(uploaded_df, master_df, subset_cols):    

    # Create composite key for fast comparison
    uploaded_df["_merge_key"] = uploaded_df[subset_cols].astype(str).agg("|".join, axis=1)
    master_df["_merge_key"] = master_df[subset_cols].astype(str).agg("|".join, axis=1)

    # Keep only novel transactions
    filtered_df = uploaded_df[~uploaded_df["_merge_key"].isin(master_df["_merge_key"])].copy()
    filtered_df.drop(columns="_merge_key", inplace=True)

    return filtered_df
