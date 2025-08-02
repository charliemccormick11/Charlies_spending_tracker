import pandas as pd

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