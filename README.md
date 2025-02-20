 # Stessa Transaction Categorizer

This tool automatically categorizes financial transactions (depending on format) for real estate businesses using AI models through Ollama (extremely poorly i must add. Better to just go line by line fwiw)0. It's specifically designed to work with Stessa's accounting categories and can process transaction data from various banking institutions (not really, repo is trash as is, but it is good starter code if you run your properties through stessa.com).

## Overview

BE ADVISED: This is a work in progress. Multiple LLMs screw up the categorization. I need to fine tune everything but will only work on this for next years tax season.

The script uses AI to categorize each transaction into Stessa's predefined categories by:
1. Learning from a dataset of previously categorized transactions
2. Using AI to match new transactions to the correct Stessa category
3. Saving progress regularly to prevent data loss
4. Generating a CSV file ready for import into Stessa

## Prerequisites

- Python 3.8+
- Ollama installed (https://ollama.ai)
- NVIDIA GPU (optional but recommended)
- Required Python packages:
  ```bash
  pip install pandas requests
  ```

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/stessa-categorizer.git
   cd stessa-categorizer
   ```
2. Install Ollama and pull one of the supported models:
   ```bash
   ollama pull mistral

3. Prepare your files:
- Place your transaction data in `transactions.csv`
- Ensure `stessa_fields.txt` contains your Stessa categories
- (Optional) Add example transactions in `TransactionsFromStessaHockeystick.csv`

## Usage

1. Start the Ollama model in a terminal: 
   
   ollama run deepseek-coder:14b # or your chosen model


2. In a new terminal, run the categorizer:
   
   python categorize_transactions_deepseek.py


The script will:
- Load your transactions from `transactions.csv`
- Categorize each transaction using AI
- Save progress every 20 transactions
- Output a categorized CSV file named `categorized_transactions_[model_name].csv`

## File Structure

- `categorize_transactions_deepseek.py`: Main script using the Deepseek model
- `categorize_transactions_mistral.py`: Alternative version using Mistral
- `stessa_fields.txt`: List of valid Stessa categories
- `transactions.csv`: Your input transactions
- `TransactionsFromStessaHockeystick.csv`: Example transactions for training

## Features

- this repo sucks, and I would just categorize manually if there was a gun to my head.
- AI-powered categorization
- Learning from example transactions
- Automatic progress saving
- GPU acceleration support
- Handles multiple transaction formats
- Resumes from last saved point if interrupted

## Supported Models

- Deepseek Coder 14B
- Mistral 7B
- ALIEN Intelligence Accounting
- Other Ollama-
