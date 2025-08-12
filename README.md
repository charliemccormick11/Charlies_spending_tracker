# Charlie's Spending Tracker
Charlie's Spending Tracker is a personal finance tracker built with Python, Streamlit, and OpenAI's API. This app helps you track all of your credit card expenses, categorize them, and get valuable insights into your spending habits.
Originally designed for Chase credit cards, this app leverages transaction names paired with Chase's pre-designated categories in order to filter your transactions in ways that give a better overview to where your money is actually going.
For all transactions that cannot be categorized, the user has the option to leverage OpenAI to categorize transactions. Each transaction's category can be manually updated later. 

# Pages
## Current Spending 📍  
    Get a clear picture of your spending habits. Use the year and month dropdowns to explore how much you’ve spent in each category, how often you visit your favorite places, and how much you spend there.  
    You can also re-categorize individual transactions to refine your financial data.  
    **Note:** Don’t forget to click the **“Download”** button on this page to save your categorized transactions. You’ll need this file next time you return to the app!
    
    ---
    
## Budgeting Goals 💰
    Track your monthly spending across variable categories. Your budget goal for each category is based on the average of your **6 lowest-spending months** over the past year. For the current month, we’ll pro-rate the target to show whether you’re on track.  
    To help you improve, **BudgetGPT** analyzes your recent transactions and suggests actionable strategies to cut spending in each category.
    
    ---
    
## Future Categorization 📊 
    Customize how each vendor is categorized moving forward. After uploading your previously saved file under **"Returning Users ↩️"**, the app will automatically apply your preferences to new transactions — so everything stays organized your way.
