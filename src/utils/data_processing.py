import pandas as pd
import re

def process_credit_transactions(df):
    """Process credit card transactions."""
    df = df.copy()
    df['Category'] = df['Category'].fillna('Uncategorized')
    return df

def process_checking_transactions(df):
    """Process checking account transactions."""
    df = df.copy()
    df['Category'] = 'Checking'
    return df

def process_venmo_transactions(df):
    """Process Venmo transactions."""
    df = df.copy()
    df['Category'] = 'Venmo'
    return df

def categorize_transactions(df):
    """Categorize transactions into spending categories."""
    categories = {
        'Bar': ['bar', 'pub', 'tavern', 'brewery'],
        'Restaurant': ['restaurant', 'dining', 'cafe', 'bistro'],
        'Takeout': ['takeout', 'delivery', 'grubhub', 'doordash', 'ubereats'],
        'Groceries': ['grocery', 'market', 'supermarket', 'whole foods', 'trader joe'],
        'Shopping': ['store', 'shop', 'retail', 'amazon', 'target', 'walmart'],
        'Entertainment': ['movie', 'theater', 'concert', 'show', 'event'],
        'Travel': ['flight', 'hotel', 'airbnb', 'uber', 'lyft', 'train'],
        'Utilities': ['electric', 'gas', 'water', 'internet', 'phone'],
        'Healthcare': ['doctor', 'pharmacy', 'medical', 'hospital'],
        'Other': []
    }
    
    df['Category'] = df['Category'].fillna('Uncategorized')
    for category, keywords in categories.items():
        mask = df['Description'].str.lower().str.contains('|'.join(keywords), na=False)
        df.loc[mask, 'Category'] = category
    
    return df

def checking_to_credit(checking_df, credit_df):
    """Process checking and credit data together."""
    if checking_df is None or credit_df is None:
        return None
    
    checking_df = checking_df.copy()
    credit_df = credit_df.copy()
    
    # Add dataset identifier
    checking_df['Dataset'] = 'Checking'
    credit_df['Dataset'] = 'Credit'
    
    # Combine dataframes
    combined_df = pd.concat([checking_df, credit_df], ignore_index=True)
    return combined_df

def process_income_data(checking_df):
    """Process income data from checking account."""
    if checking_df is None:
        return None
    
    income_df = checking_df[checking_df['Amount'] > 0].copy()
    income_df['Category'] = 'Income'
    income_df['Dataset'] = 'Income'
    return income_df

def process_schwab_data(checking_df):
    """Process Schwab data from checking account."""
    if checking_df is None:
        return None
    
    schwab_df = checking_df[checking_df['Description'].str.contains('SCHWAB', case=False, na=False)].copy()
    schwab_df['Category'] = 'Schwab'
    schwab_df['Dataset'] = 'Schwab'
    return schwab_df 