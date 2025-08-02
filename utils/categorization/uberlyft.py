import pandas as pd 




def check_rideshare_venmo(ext_description):
    rideshare_keywords = ['uber', 'lyft', 'ride']

    for word in ext_description:
        if word.lower() in rideshare_keywords:
            return "yes"
    return None

