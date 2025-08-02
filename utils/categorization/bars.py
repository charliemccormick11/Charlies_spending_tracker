import pandas as pd 
import re

#Importing Chicago Bar Names
chi_bars_df= pd.read_csv('reference_csvs/Chicago_Alc.csv')
chi_bars_df["DOING BUSINESS AS NAME"] = chi_bars_df["DOING BUSINESS AS NAME"].str.strip().str.lower()
chi_bars_df["LEGAL NAME"] = chi_bars_df["LEGAL NAME"].str.strip().str.lower()

#Making Bar Names Simpler and Readable
chi_bar_names= pd.concat([chi_bars_df["DOING BUSINESS AS NAME"], chi_bars_df["LEGAL NAME"]]).dropna().unique()
chi_bar_names_set = set(chi_bar_names)
chi_bar_names_set ={bar.replace("'", "") for bar in chi_bar_names_set}
chi_bar_names_set ={bar.replace("&", " ") for bar in chi_bar_names_set}
chi_bar_names_set ={bar.replace("+", " ") for bar in chi_bar_names_set}
chi_bar_names_set ={bar.replace("-", " ") for bar in chi_bar_names_set}
chi_bar_names_set ={bar.replace("*", " ") for bar in chi_bar_names_set}
chi_bar_names_set ={bar.replace(",", " ") for bar in chi_bar_names_set}
chi_bar_names_set ={bar.replace("/", " ") for bar in chi_bar_names_set}

#Removing Basic Bar Words
generic_words = {"on", "at", "and", "the", "by", "of"}

#Extract Top Two Words form the bar name
def extract_key_bar_words(name):
    """ Remove generic words and return the most unique parts of the name """
    cleaned_name = re.sub('[^a-zA-Z\s]', '', name)
    words = cleaned_name.split()
   
    keywords = [
        word for word in words 
        if word.lower() not in generic_words  # Remove generic words
        and not re.search('\d', word)       # Remove numbers
    ]
    if len(keywords) == 1:
        return (keywords[0], )

    elif len(keywords) >= 2:
        return (keywords[0], keywords[1])

    return tuple()


chi_bar_keywords = {extract_key_bar_words(name) for name in chi_bar_names_set if extract_key_bar_words(name)}

def matched_credit_bar_transaction(ext_description):
    if len(ext_description) == 2:
        if ext_description in chi_bar_keywords:
            return ext_description
        elif "beer" in ext_description:
            return ("misc", "bar")

    elif len(ext_description) == 1:
        for bar in chi_bar_keywords:
            if ext_description[0] in bar:  # Match one word in the tuple
                return ext_description
    else:
        return None
    
def matched_venmo_bar_transaction(ext_description):
    if len(ext_description) == 2:
        if tuple(ext_description) in chi_bar_keywords:
            return ext_description

    elif len(ext_description) == 1:
        for bar in chi_bar_keywords:
            if ext_description[0] in bar and (len(ext_description[0]) > 7):  # Match one word in the tuple
                return ext_description
            
    else:
        return None
    
def check_alc_keywords(ext_description):
    alc_words=["beer", "bier", "rinse", "alc", "beers", "drink", "drinks", "noon", "🍻", "high noon", "high noons" ]
    for word in ext_description:
        if word.lower() in alc_words:
            return "yes"
        return None
    


       

    
    

