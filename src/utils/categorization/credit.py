import pandas as pd
from src.config import REFERENCE_FILES, CATEGORIES

def load_reference_files():
    """Load all reference files into DataFrames."""
    reference_dfs = {}
    for category, file_path in REFERENCE_FILES.items():
        try:
            reference_dfs[category] = pd.read_csv(file_path)
        except FileNotFoundError:
            print(f"Warning: Reference file {file_path} not found")
            reference_dfs[category] = pd.DataFrame()
    return reference_dfs

def categorize_transactions(df):
    """Categorize credit card transactions into spending categories."""
    # Load reference files
    reference_dfs = load_reference_files()
    
    df['Category'] = df['Category'].fillna('Uncategorized')
    
    # First, try to match against reference files
    for category, ref_df in reference_dfs.items():
        if not ref_df.empty:
            # Get keywords from reference file
            keywords = ref_df['keyword'].tolist()
            mask = df['Description'].str.lower().str.contains('|'.join(keywords), na=False)
            df.loc[mask, 'Category'] = category
    
    # Then, try to match against hardcoded categories
    for category, keywords in CATEGORIES.items():
        mask = df['Description'].str.lower().str.contains('|'.join(keywords), na=False)
        df.loc[mask, 'Category'] = category
    
    return df 