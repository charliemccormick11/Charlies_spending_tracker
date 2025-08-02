import pandas as pd

def add_venmo_info(df, venmo_df):
    """Add Venmo information to the main dataframe."""
    if df is None or venmo_df is None:
        return df, venmo_df
    
    # Add Venmo transactions to the main dataframe
    venmo_df['Dataset'] = 'Venmo'
    combined_df = pd.concat([df, venmo_df], ignore_index=True)
    
    return combined_df, pd.DataFrame()  # Return empty DataFrame for remaining Venmo transactions

def categorize_venmos(venmo_df, credit_df):
    """Categorize Venmo transactions."""
    if venmo_df is None:
        return {}
    
    categories = {
        'rent': ['rent', 'apartment', 'housing'],
        'bar': ['bar', 'pub', 'tavern', 'brewery'],
        'takeout': ['takeout', 'delivery', 'grubhub', 'doordash', 'ubereats'],
        'restaurant': ['restaurant', 'dining', 'cafe', 'bistro'],
        'rideshare': ['uber', 'lyft', 'ride'],
        'golf': ['golf', 'course', 'range'],
        'food': ['food', 'lunch', 'dinner', 'breakfast'],
        'bills': ['bill', 'utility', 'electric', 'gas', 'water', 'internet', 'phone'],
        'entertainment': ['movie', 'theater', 'concert', 'show', 'event'],
        'gambling': ['casino', 'bet', 'gamble'],
        'gifts': ['gift', 'present', 'donation'],
        'remaining': []
    }
    
    categorized_dfs = {}
    remaining_df = venmo_df.copy()
    
    for category, keywords in categories.items():
        mask = remaining_df['Description'].str.lower().str.contains('|'.join(keywords), na=False)
        if mask.any():
            categorized_dfs[category] = remaining_df[mask].copy()
            remaining_df = remaining_df[~mask]
    
    categorized_dfs['remaining'] = remaining_df
    return categorized_dfs 