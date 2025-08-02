import pandas as pd 
import re

chi_takeout_df= pd.read_csv('reference_csvs/Chi_Takeout.csv')
chi_takeout_df["FOOD NAME"] = chi_takeout_df["FOOD NAME"].str.strip().str.lower()

chi_takeout_set= set(chi_takeout_df["FOOD NAME"])

chi_takeout_set ={place.replace("'", "") for place in chi_takeout_set}
chi_takeout_set ={place.replace("-", " ") for place in chi_takeout_set}

chi_takeout_words= {tuple(place.split()) for place in chi_takeout_set}

def matched_credit_takeout_transaction(ext_description):
    if "culvers" in ext_description:
        return "Culvers"
    
    if "chipotle" in ext_description:
        return "Chipotle"

    for place in chi_takeout_words:
        if set(ext_description).issubset(set(place)):
            return " ".join(place).title()
        
    return None

chi_restaurants_df= pd.read_csv('reference_csvs/Chi_Restaurants.csv')
chi_restaurants_df["DBA Name"] = chi_restaurants_df["DBA Name"].str.strip().str.lower()
chi_restaurants_df["AKA Name"] = chi_restaurants_df["AKA Name"].str.strip().str.lower()

#Making Restaurant Names Simpler and Readable
chi_restaurants_names= pd.concat([chi_restaurants_df["DBA Name"], chi_restaurants_df["AKA Name"]]).dropna().unique()

#Making Bar Names Simpler and Readable
chi_restaurants_names= pd.concat([chi_restaurants_df["DBA Name"], chi_restaurants_df["AKA Name"]]).dropna().unique()
chi_restaurants_names_set = set(chi_restaurants_names)
chi_restaurants_names_set ={bar.replace("'", "") for bar in chi_restaurants_names}
chi_restaurants_names_set ={bar.replace("&", " ") for bar in chi_restaurants_names}
chi_restaurants_names_set ={bar.replace("+", " ") for bar in chi_restaurants_names}
chi_restaurants_names_set ={bar.replace("-", " ") for bar in chi_restaurants_names}
chi_restaurants_names_set ={bar.replace("*", " ") for bar in chi_restaurants_names}
chi_restaurants_names_set ={bar.replace(",", " ") for bar in chi_restaurants_names}
chi_restaurants_names_set ={bar.replace("/", " ") for bar in chi_restaurants_names}

#Removing Basic Bar Words
generic_words = {"on", "at", "and", "the", "by", "of"}

#Extract Top Two Words form the bar name
def extract_key_rest_words(name):
    """ Remove generic words and return the most unique parts of the name """
    cleaned_name = re.sub('[^a-zA-Z\s]', '', name)
    words = cleaned_name.split()
   
    keywords = [
        word for word in words 
        if word.lower() not in generic_words  # Remove generic words
    ]
    if len(keywords) == 1:
        return (keywords[0], )

    elif len(keywords) >= 2:
        return (keywords[0], keywords[1])

    return tuple()

chi_rest_keywords = {extract_key_rest_words(name) for name in chi_restaurants_names_set if extract_key_rest_words(name)}

def matched_credit_restaurant_transaction(ext_description):
   
    if len(ext_description) == 2:
        if ext_description in chi_rest_keywords:
            return ext_description

    elif len(ext_description) == 1:
        for rest in chi_rest_keywords:
            if ext_description[0] in rest:  # Match one word in the tuple
                return ext_description
        

    else:
        return None
    

def matched_venmo_restaurant_transaction(ext_description):
    if len(ext_description) == 2:
        if ext_description in chi_rest_keywords:
            return ext_description
    elif len(ext_description)==1:     
        for rest in chi_rest_keywords:
            if len(rest)==1:
                if ext_description[0] == rest[0]:   
                    return ext_description

    else:
        return None