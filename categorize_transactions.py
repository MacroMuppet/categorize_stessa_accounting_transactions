import pandas as pd
import re
from datetime import datetime
import json
import requests
import os

MODEL_NAME = "nomic-embed-text:latest"  # "llama3.1:latest" #"deepseek-r1:14b"  # Change this one line to switch models

def parse_stessa_fields(filename):
    """Parse the Stessa fields file into a dictionary of categories and subcategories"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Stessa fields file '{filename}' not found")
        
    categories = {}
    subcategories = []  # List to store all subcategories
    current_category = None
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('-'):
                # This is a main category
                current_category = line
                categories[current_category] = []
            elif line.startswith('-'):
                # This is a subcategory
                subcategory = line.lstrip('- ')
                if current_category:
                    categories[current_category].append(subcategory)
                    subcategories.append((subcategory, current_category))
    
    print(f"Loaded {len(categories)} categories with {len(subcategories)} subcategories from {filename}")
    return categories, subcategories

def clean_amount(amount_str):
    """Clean amount string by removing currency symbols and converting to float"""
    if isinstance(amount_str, (int, float)):
        return float(amount_str)
    
    # Remove currency symbols, commas, and extra spaces
    cleaned = amount_str.replace('$', '').replace(',', '').strip()
    
    try:
        return float(cleaned)
    except ValueError:
        print(f"Warning: Could not convert amount '{amount_str}' to float")
        return 0.0

def read_csv_transactions(filename):
    """Read transactions from CSV file into a pandas DataFrame"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"CSV file '{filename}' not found")
        
    # Read the CSV file
    df = pd.read_csv(filename)
    print(f"Loaded {len(df)} transactions from {filename}")
    print(f"Columns found: {df.columns.tolist()}")
    
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Clean up Amount column
    df['Amount'] = df['Amount'].apply(clean_amount)
    
    # Clean up Balance column if it exists
    if 'Balance' in df.columns:
        df['Balance'] = df['Balance'].apply(clean_amount)
    
    return df

def call_deepseek(description, amount, categories, subcategories):
    """Call the local LLM model to categorize a transaction"""
    # Create a formatted string of all subcategories with their main categories
    subcategories_str = ""
    for subcat, maincat in subcategories:
        subcategories_str += f"- {subcat} (under {maincat})\n"
    
    prompt = f"""You are a transaction categorization system. Given this transaction:
Description: "{description}"
Amount: ${amount}

Categorize it into exactly one of these subcategories:
{subcategories_str}

Rules:
1. "MICHAEL SHEETS" or "MICHAEL G" transactions are mortgage-related
2. "JONATHAN" or "JONATHAN SHEETS" transactions are:
   - negative amount = Owner Distributions
   - positive amount = Owner Contributions
3. AIRBNB/VRBO income = Short Term Rents
4. Utilities go under specific utility subcategories
5. Choose specific repair subcategories when possible
6. Transactions under $200 from grocery or retail stores (like Meijer, Target, Trader Joe's, Walmart) 
   should be categorized as "Linens, Soaps, & Other Consumables" under Repairs & Maintenance
7. Any "M2M" transactions follow the same rule as Jonathan's transactions:
   - negative amount = Owner Distributions
   - positive amount = Owner Contributions
8. Any recurring streaming or subscription services (like Netflix, YouTube TV, Showtime, Disney+, etc.) 
   should be categorized as "Software Subscriptions" under Admin & Other

IMPORTANT: Return ONLY the subcategory name, with no explanation or additional text."""

    try:
        # Make API call to local model
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "raw": True,
                "temperature": 0.1  # Added lower temperature for more focused responses
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            # Clean up response to only take first line and remove any extra text
            subcategory = result['response'].strip().split('\n')[0].strip()
            print(f"Categorized '{description}' (${amount}) as '{subcategory}'")
            return subcategory
        else:
            print(f"Error from {MODEL_NAME} API: {response.status_code}")
            return "Uncategorized"
    except Exception as e:
        print(f"Error calling {MODEL_NAME} API: {e}")
        return "Uncategorized"

def check_deepseek_running():
    """Check if Deepseek model is running and accessible"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL_NAME,  # Use the configured model name
                "prompt": "hi",
                "stream": False
            },
            timeout=5  # 5 second timeout
        )
        
        if response.status_code == 200:
            print(f"✓ {MODEL_NAME} model is running and accessible")
            return True
        else:
            print(f"✗ {MODEL_NAME} model returned error status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ Could not connect to {MODEL_NAME} model at http://localhost:11434")
        print("  Please make sure Ollama is running with:")
        print(f"  ollama run {MODEL_NAME}")
        return False
    except Exception as e:
        print(f"✗ Error checking {MODEL_NAME} model: {e}")
        return False

def main():
    print("Starting transaction categorization...")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if Deepseek is running before proceeding
    if not check_deepseek_running():
        print("Exiting due to Deepseek model not being accessible")
        return
        
    try:
        # Parse Stessa fields
        categories, subcategories = parse_stessa_fields('stessa_fields.txt')
        
        # Read transactions from CSV file
        df = read_csv_transactions('transactions.csv')
        
        # Add category columns
        df['Subcategory'] = ''
        
        # Process each transaction
        total = len(df)
        for idx, row in df.iterrows():
            try:
                subcategory = call_deepseek(row['Description'], row['Amount'], categories, subcategories)
                df.at[idx, 'Subcategory'] = subcategory
                if (idx + 1) % 10 == 0:  # Print progress every 10 transactions
                    print(f"Processed {idx + 1}/{total} transactions")
            except Exception as e:
                print(f"Error processing transaction {idx + 1}: {e}")
                df.at[idx, 'Subcategory'] = 'Error'
        
        # Extract model name for the output filename
        model_suffix = MODEL_NAME.split(':')[0].lower()  # Get the part before ':' and convert to lowercase
        output_filename = f'categorized_transactions_{model_suffix}.csv'
        
        # Save results
        df.to_csv(output_filename, index=False)
        print(f"Done! Saved {len(df)} categorized transactions to {output_filename}")
        
        # Print first few rows as verification
        print("\nFirst few rows of output:")
        print(df.head())
        
    except Exception as e:
        print(f"Error in main process: {e}")

if __name__ == "__main__":
    main() 