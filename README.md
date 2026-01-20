# ReStock - Investment Portfolio Tracker
A Python-based portfolio management system that automatically syncs stock transactions to Google Sheets, tracks real-time prices, dividends, and performance metrics.

## Prerequisites
- Python 3.8 or higher
- Google Cloud account (free)
- Google Sheets

## Installation
1. Clone the repository
2. Install dependencies (install -r requirements.txt)
3. Set up Google Sheets API
      a. Go to Google Cloud Console
      b. Create a new project
      c. Enable Google Sheets API and Google Drive API
      d. Create Service Account credentials
      e. Download JSON key and save as credentials.json in project root
      f. Copy the service account email (looks like xxx@xxx.iam.gserviceaccount.com)
4. Create your Google Sheet
      a. Create a new Google Sheet
      b. Share it with your service account email (make sure it has editor access!)
      c. Create two tabs: MyPortfolio and MyTransactions
5. Configure the app
      a. Open config.py
      b. Update SHEET_NAME with your Google Sheet name
6. Set up your google sheets (Use this template by making a copy here: 
<br>https://docs.google.com/spreadsheets/d/1ZXmKKT_JIAyPMi7DegvO5yrag0Obj9WlmDRrvsNbMoo/edit?usp=sharing)
7. Run the main

## Usage
### Adding Transactions
Add your stock transactions to the MyTransactions tab

### Running the Tracker
When you run python main.py, the app will:
- Read all transactions from MyTransactions
- Calculate consolidated positions (average cost, realized gains)
- Sync holdings to MyPortfolio tab
- Fetch current prices and dividend data
- Update all performance metrics
- Display summary in terminal and Google Sheets

## Tech Stack
Python 3.8+ - Core language
yfinance - Real-time stock data
gspread - Google Sheets API wrapper
google-auth - Authentication
pandas - Data processing (via yfinance)

## Configuration
Edit config.py to customize:
  ### Sheet settings
  SHEET_NAME = 'Your Portfolio Sheet Name'
  <br>PORTFOLIO_TAB = 'MyPortfolio'
  <br>TRANSACTIONS_TAB = 'MyTransactions'
  
  ### Features
  VERBOSE = True              # Detailed console output
  <br>UPDATE_SHEET = True         # Auto-update Google Sheets
  <br>SHOW_SUMMARY = True         # Display portfolio summary
  <br>TRACK_DIVIDENDS = True      # Include dividend tracking
  
  ### API settings
  MAX_RETRIES = 3            # Retry failed API calls

## Features in Detail
### Transaction Processing
- Supports BUY and SELL transactions
- Automatically calculates average cost basis across multiple purchases
- Tracks realized gains/losses when positions are sold
- Handles partial sells correctly
### Performance Tracking
- Unrealized Gains - Current profit/loss on open positions
- Realized Gains - Locked-in profit/loss from closed positions
- Day Change - Today's performance
- Portfolio Allocation - Percentage weight of each position
### Dividend Income
- Annual dividend per share
- Dividend yield percentage
- Projected annual income
- Portfolio-wide dividend yield
### Sector Analysis
- Automatic sector classification
- Sector allocation percentages
- Sector-level performance

## ⚠️ Disclaimer
This tool is for educational and personal portfolio tracking purposes only. It is not financial advice. Always do your own research before making investment decisions. 
Stock prices are fetched from Yahoo Finance and may be delayed. For real-time trading decisions, use official broker platforms.

## Acknowledgments
- yfinance - Stock data API
- gspread - Google Sheets Python API

## Contact
Project Link: https://github.com/ellenvlimnauaw/ReStock
Email: ellenvlimanauw@gmail.com
