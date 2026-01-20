"""
Configuration for Portfolio Manager with Transaction Sync + Dividends
"""

# ==========================================
# GOOGLE SHEETS SETTINGS
# ==========================================
CREDENTIALS_FILE = 'credentials.json'
SHEET_NAME = 'ReStock [TEMPLATE]'  # Change this to your Google Sheet name
PORTFOLIO_TAB = 'MyPortfolio'
TRANSACTIONS_TAB = 'MyTransactions'

# ==========================================
# TRANSACTION COLUMNS (0-indexed)
# ==========================================
TXN_DATE_COL = 0        # A: Date
TXN_TICKER_COL = 1      # B: Ticker
TXN_TYPE_COL = 2        # C: Type (BUY/SELL)
TXN_NAME_COL = 3        # D: Name
TXN_SHARES_COL = 4      # E: Shares
TXN_PRICE_COL = 5       # F: Buy/Sell Price

# ==========================================
# PORTFOLIO COLUMNS (0-indexed) - PHASE 2
# ==========================================
TICKER_COL = 0          # A: Stock ticker
NAME_COL = 1            # B: Company name
SECTOR_COL = 2          # C: Sector
SHARES_COL = 3          # D: Number of shares
AVG_COST_COL = 4        # E: Average cost per share
CURRENT_PRICE_COL = 5   # F: Current market price
MARKET_VALUE_COL = 6    # G: Current total value
COST_BASIS_COL = 7      # H: Total amount invested
GAIN_LOSS_COL = 8       # I: Profit/Loss in dollars
GAIN_LOSS_PCT_COL = 9   # J: Profit/Loss in percentage
REALIZED_GL_COL = 10    # K: Realized Gain/Loss
DAY_CHANGE_COL = 11     # L: Today's price change %
DAY_GAIN_LOSS_COL = 12  # M: Today's dollar gain/loss
ALLOCATION_COL = 13     # N: Portfolio allocation %
ANNUAL_DIVIDEND_COL = 14    # O: Annual dividend per share
DIVIDEND_YIELD_COL = 15     # P: Dividend yield %
ANNUAL_INCOME_COL = 16      # Q: Annual dividend income
LAST_UPDATED_COL = 17       # R: Last update timestamp

# ==========================================
# UPDATE SETTINGS
# ==========================================
VERBOSE = True
UPDATE_SHEET = True
SKIP_EMPTY_ROWS = True
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Retry settings for API calls
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# ==========================================
# DIVIDEND TRACKING
# ==========================================
TRACK_DIVIDENDS = True

# ==========================================
# SECTOR ALLOCATION - DISABLED
# ==========================================
SHOW_SECTOR_ALLOCATION = False
