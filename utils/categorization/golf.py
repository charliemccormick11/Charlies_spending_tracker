import pandas as pd 


chi_golf_df= pd.read_csv('reference_csvs/Chi_Golf.csv')
chi_golf_df["COURSE NAME"] = chi_golf_df["COURSE NAME"].str.strip().str.lower()

chi_golf_courses_set= set(chi_golf_df["COURSE NAME"])

chi_golf_courses_set ={course.replace("'", "") for course in chi_golf_courses_set}
chi_golf_courses_set ={course.replace("&", " ") for course in chi_golf_courses_set}
chi_golf_courses_set ={course.replace("+", " ") for course in chi_golf_courses_set}
chi_golf_courses_set ={course.replace("-", " ") for course in chi_golf_courses_set}
chi_golf_courses_set ={course.replace("*", " ") for course in chi_golf_courses_set}
chi_golf_courses_set ={course.replace(",", " ") for course in chi_golf_courses_set}
chi_golf_courses_set ={course.replace("/", " ") for course in chi_golf_courses_set}

generic_course_words = {"course", "club", "golf", "country"}

def extract_key_course_words(name):
    words = name.split()
    if len(words) ==1:
        return (words[0], )
    
    elif len(words) ==2:
        return (words[0], words[1])
    
    elif len(words) ==3:
        return (words[0], words[1], words[2])
    
    return tuple()

chi_course_keywords = {extract_key_course_words(name) for name in chi_golf_courses_set if extract_key_course_words(name)}

def matched_credit_course_transaction(description):
    if ("GLF*" in description) or ("golf" in description.lower()) or ("country club" in description.lower()) or("gc" in description.lower()):
        return description  
    
    extracted =tuple(description.split()[:2]) 
    if extracted in chi_course_keywords:
        return description
    
    else:
        return None
    

def check_golf_keywords(ext_description):
    golf_words=["golf", "galf", "links", "green", "greens", "⛳", "gawlf", "par" ]
    for word in ext_description:
        if word.lower() in golf_words:
            return "yes"
            
    return None
    