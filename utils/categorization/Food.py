import pandas as pd 

def check_food_keywords(ext_description):
    food_words=["food", "grub", "bbq", "pizza", "greens", "za", "dinner", "din", "chomp", "lunch", "🍕", "thai", "tenders", "coffee", "donut", "tip", "breakfast"]
    for word in ext_description:
        if word.lower() in food_words:
            return "yes"
        return None