import pandas as pd 


fashion_df= pd.read_csv('reference_csvs/fashion.csv')
fashion_df["BrandName"] = fashion_df["BrandName"].str.strip().str.lower()

fashion= fashion_df["BrandName"].tolist()

fashion ={place.replace("'", "") for place in fashion}
fashion ={place.replace("-", " ") for place in fashion}


def matched_fashion_transaction(description):

    for place in fashion:
        if place in description:
            return (place).title()
        
    return None