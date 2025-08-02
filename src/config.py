import os

# Base directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
REFERENCE_DIR = os.path.join(DATA_DIR, 'reference')

# Reference file paths
REFERENCE_FILES = {
    'bars': os.path.join(REFERENCE_DIR, 'bars.csv'),  # Using Chicago_Alc.csv renamed to bars.csv
    'food': os.path.join(REFERENCE_DIR, 'food.csv'),
    'takeout': os.path.join(REFERENCE_DIR, 'takeout.csv'),
    'golf': os.path.join(REFERENCE_DIR, 'golf.csv'),
    'fashion': os.path.join(REFERENCE_DIR, 'fashion.csv'),
    'fast_food': os.path.join(REFERENCE_DIR, 'fast_food.csv')
}

# Categorization settings
CATEGORIES = {
    'Bar': ['bar', 'pub', 'tavern', 'brewery', 'liquor', 'wine', 'spirits'],
    'Restaurant': ['restaurant', 'dining', 'cafe', 'bistro'],
    'Takeout': ['takeout', 'delivery', 'grubhub', 'doordash', 'ubereats'],
    'Golf': ['golf', 'driving range', 'pro shop'],
    'Fashion': ['clothing', 'apparel', 'shoes', 'accessories'],
    'Fast Food': ['fast food', 'quick service', 'drive thru']
} 