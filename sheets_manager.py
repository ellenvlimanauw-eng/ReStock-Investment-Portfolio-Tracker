"""
Sheets Manager - Combined
Handles all Google Sheets operations for portfolio and transactions
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import *
import traceback


class SheetsManager:
    """Manages all Google Sheets operations"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.transactions_sheet = None
        self.portfolio_sheet = None
        self.connected = False
    
    def connect(self):
        """Connect to Google Sheets"""
        try:
            print(f"\n[>] Connecting to: {SHEET_NAME}")
            
            # Authenticate
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_file(
                CREDENTIALS_FILE,
                scopes=scope
            )
            
            self.client = gspread.authorize(credentials)
            
            # Open spreadsheet
            self.spreadsheet = self.client.open(SHEET_NAME)
            
            # Get Transactions tab
            try:
                self.transactions_sheet = self.spreadsheet.worksheet(TRANSACTIONS_TAB)
                print(f"[+] Connected to tab: {TRANSACTIONS_TAB}")
            except gspread.exceptions.WorksheetNotFound:
                print(f"[!] ERROR: Tab '{TRANSACTIONS_TAB}' not found!")
                print(f"   Please create a tab named '{TRANSACTIONS_TAB}' in your sheet")
                return False
            
            # Get Portfolio tab
            try:
                self.portfolio_sheet = self.spreadsheet.worksheet(PORTFOLIO_TAB)
                print(f"[+] Connected to tab: {PORTFOLIO_TAB}")
            except gspread.exceptions.WorksheetNotFound:
                print(f"[!] ERROR: Tab '{PORTFOLIO_TAB}' not found!")
                print(f"   Please create a tab named '{PORTFOLIO_TAB}' in your sheet")
                return False
            
            self.connected = True
            return True
            
        except FileNotFoundError:
            print(f"[!] ERROR: {CREDENTIALS_FILE} not found!")
            return False
            
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"[!] ERROR: Sheet '{SHEET_NAME}' not found!")
            return False
            
        except Exception as e:
            print(f"[!] Connection error: {str(e)}")
            return False
    
    def read_transactions(self):
        """
        Read all transactions from Transactions tab
        
        Returns:
            List of transaction dicts
        """
        if not self.connected:
            print("[!] Not connected to Google Sheets")
            return []
        
        try:
            # Get all data
            all_data = self.transactions_sheet.get_all_values()
            
            if len(all_data) < 2:
                print("[!] No transactions found in sheet")
                return []
            
            headers = all_data[0]
            rows = all_data[1:]
            
            transactions = []
            
            for row_num, row in enumerate(rows, start=2):
                # Skip empty rows
                if len(row) <= TXN_TICKER_COL or not row[TXN_TICKER_COL].strip():
                    continue
                
                # Parse transaction
                date = row[TXN_DATE_COL].strip() if len(row) > TXN_DATE_COL else ""
                ticker = row[TXN_TICKER_COL].strip().upper() if len(row) > TXN_TICKER_COL else ""
                txn_type = row[TXN_TYPE_COL].strip().upper() if len(row) > TXN_TYPE_COL else "BUY"
                name = row[TXN_NAME_COL].strip() if len(row) > TXN_NAME_COL else ""
                shares = self._parse_number(row[TXN_SHARES_COL]) if len(row) > TXN_SHARES_COL else 0
                price = self._parse_number(row[TXN_PRICE_COL]) if len(row) > TXN_PRICE_COL else 0
                
                # Skip if no ticker
                if not ticker:
                    continue
                
                # Validate transaction type
                if txn_type not in ['BUY', 'SELL']:
                    if VERBOSE:
                        print(f"  [!] Row {row_num}: Invalid transaction type '{txn_type}', defaulting to BUY")
                    txn_type = 'BUY'
                
                # Skip if no shares or price
                if not shares or not price or shares <= 0 or price <= 0:
                    continue
                
                transactions.append({
                    'date': date,
                    'ticker': ticker,
                    'type': txn_type,
                    'name': name,
                    'shares': shares,
                    'price': price,
                    'row_number': row_num
                })
            
            print(f"[+] Read {len(transactions)} transactions")
            return transactions
            
        except Exception as e:
            print(f"[!] Error reading transactions: {str(e)}")
            traceback.print_exc()
            return []
    
    def _parse_number(self, value):
        """Parse number from string"""
        if not value or value == '':
            return None
        
        try:
            # Remove $, commas, spaces
            clean = str(value).replace('$', '').replace(',', '').replace(' ', '').strip()
            return float(clean)
        except:
            return None
    
    def sync_portfolio(self, holdings):
        """
        Sync holdings to Portfolio tab
        Updates existing tickers or adds new ones
        
        Args:
            holdings: List of holding dicts with ticker, name, shares, avg_cost, realized_gain_loss
        """
        if not self.connected:
            return False
        
        try:
            print(f"\n[>] Syncing {len(holdings)} positions to Portfolio tab...")
            
            # Get current portfolio data
            all_data = self.portfolio_sheet.get_all_values()
            
            # Build ticker -> row mapping
            ticker_rows = {}
            if len(all_data) > 1:
                for row_num, row in enumerate(all_data[1:], start=2):
                    if len(row) > TICKER_COL and row[TICKER_COL].strip():
                        ticker = row[TICKER_COL].strip().upper()
                        ticker_rows[ticker] = row_num
            
            # Update or add each holding
            updates = []
            new_rows = []
            
            for holding in holdings:
                ticker = holding['ticker']
                name = holding['name']
                shares = holding['shares']
                avg_cost = holding['avg_cost']
                realized_gl = holding.get('realized_gain_loss', 0)
                
                if ticker in ticker_rows:
                    # Update existing row
                    row = ticker_rows[ticker]
                    updates.append({
                        'row': row,
                        'ticker': ticker,
                        'name': name,
                        'shares': shares,
                        'avg_cost': avg_cost,
                        'realized_gl': realized_gl
                    })
                    print(f"  [~] Updating {ticker} at row {row}")
                else:
                    # Will add new row
                    new_rows.append({
                        'ticker': ticker,
                        'name': name,
                        'shares': shares,
                        'avg_cost': avg_cost,
                        'realized_gl': realized_gl
                    })
                    print(f"  [+] Adding new ticker {ticker}")
            
            # Apply updates to existing rows
            if updates:
                cell_list = []
                for update in updates:
                    row = update['row']
                    cell_list.append(gspread.Cell(row, TICKER_COL + 1, update['ticker']))
                    cell_list.append(gspread.Cell(row, NAME_COL + 1, update['name']))
                    cell_list.append(gspread.Cell(row, SHARES_COL + 1, update['shares']))
                    cell_list.append(gspread.Cell(row, AVG_COST_COL + 1, f"${update['avg_cost']:.2f}"))
                    cell_list.append(gspread.Cell(row, REALIZED_GL_COL + 1, update['realized_gl']))
                
                self.portfolio_sheet.update_cells(cell_list)
                print(f"[+] Updated {len(updates)} existing positions")
            
            # Add new rows
            if new_rows:
                for new in new_rows:
                    row_data = [''] * (LAST_UPDATED_COL + 1)
                    row_data[TICKER_COL] = new['ticker']
                    row_data[NAME_COL] = new['name']
                    row_data[SHARES_COL] = new['shares']
                    row_data[AVG_COST_COL] = f"${new['avg_cost']:.2f}"
                    row_data[REALIZED_GL_COL] = new['realized_gl']
                    
                    self.portfolio_sheet.append_row(row_data, value_input_option='USER_ENTERED')
                
                print(f"[+] Added {len(new_rows)} new positions")
            
            print("[+] Portfolio sync complete")
            return True
            
        except Exception as e:
            print(f"[!] Error syncing portfolio: {str(e)}")
            traceback.print_exc()
            return False
    
    def update_portfolio_prices(self, positions):
        """
        Update price, performance, and dividend data in Portfolio tab
        
        Args:
            positions: List of position dicts with calculated values
        """
        if not self.connected:
            return False
        
        try:
            # Get current portfolio to find row numbers
            all_data = self.portfolio_sheet.get_all_values()
            
            # Build ticker -> row mapping
            ticker_rows = {}
            if len(all_data) > 1:
                for row_num, row in enumerate(all_data[1:], start=2):
                    if len(row) > TICKER_COL and row[TICKER_COL].strip():
                        ticker = row[TICKER_COL].strip().upper()
                        ticker_rows[ticker] = row_num
            
            # Update each position
            cell_list = []
            timestamp = datetime.now().strftime(DATE_FORMAT)
            
            for pos in positions:
                ticker = pos['ticker']
                
                if ticker not in ticker_rows:
                    print(f"[!] Ticker {ticker} not found in portfolio")
                    continue
                
                row = ticker_rows[ticker]
                
                # Sector
                cell_list.append(gspread.Cell(row, SECTOR_COL + 1, pos['sector']))
                
                # Current price
                cell_list.append(gspread.Cell(row, CURRENT_PRICE_COL + 1, 
                                             f"${pos['current_price']:.2f}"))
                
                # Market value
                cell_list.append(gspread.Cell(row, MARKET_VALUE_COL + 1, 
                                             f"${pos['market_value']:,.2f}"))
                
                # Cost basis
                cell_list.append(gspread.Cell(row, COST_BASIS_COL + 1, 
                                             f"${pos['cost_basis']:,.2f}"))
                
                # Gain/Loss (dollars) - unrealized
                cell_list.append(gspread.Cell(row, GAIN_LOSS_COL + 1, 
                                             f"${pos['gain_loss']:+,.2f}"))
                
                # Gain/Loss (percent) - as decimal for Google Sheets
                cell_list.append(gspread.Cell(row, GAIN_LOSS_PCT_COL + 1, 
                                             pos['gain_loss_pct'] / 100))
                
                # Realized G/L - as plain number for Google Sheets formatting
                cell_list.append(gspread.Cell(row, REALIZED_GL_COL + 1, 
                                             pos['realized_gain_loss']))
                
                # Day change % - as decimal
                cell_list.append(gspread.Cell(row, DAY_CHANGE_COL + 1, 
                                             pos['day_change_pct'] / 100))
                
                # Day gain/loss
                cell_list.append(gspread.Cell(row, DAY_GAIN_LOSS_COL + 1, 
                                             f"${pos['day_gain_loss']:+,.2f}"))
                
                # Allocation %
                cell_list.append(gspread.Cell(row, ALLOCATION_COL + 1, 
                                             f"{pos['allocation']:.1f}%"))
                
                # Dividend data
                cell_list.append(gspread.Cell(row, ANNUAL_DIVIDEND_COL + 1, 
                                             f"${pos['annual_dividend']:.2f}"))
                
                # Dividend yield - write as raw decimal, Google Sheets percentage format will display correctly
                cell_list.append(gspread.Cell(row, DIVIDEND_YIELD_COL + 1, 
                                             pos['dividend_yield']))
                
                cell_list.append(gspread.Cell(row, ANNUAL_INCOME_COL + 1, 
                                             f"${pos['annual_income']:,.2f}"))
                
                # Timestamp
                cell_list.append(gspread.Cell(row, LAST_UPDATED_COL + 1, timestamp))
            
            # Update all cells
            if cell_list:
                self.portfolio_sheet.update_cells(cell_list)
                print(f"[+] Updated prices for {len(positions)} positions")
                return True
            
            return False
            
        except Exception as e:
            print(f"[!] Error updating prices: {str(e)}")
            traceback.print_exc()
            return False

