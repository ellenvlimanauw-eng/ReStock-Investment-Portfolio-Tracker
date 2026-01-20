"""
Portfolio Manager
Automatically syncs transactions to portfolio and updates prices
Supports buy/sell transactions and dividend tracking
"""

from sheets_manager import SheetsManager
from transaction_processor import TransactionProcessor
from portfolio_tracker import PortfolioTracker
from config import *
from datetime import datetime
import sys
import traceback

def main():
    """Main execution function"""
    
    print("\n" + "="*70)
    print("PORTFOLIO MANAGER")
    print("="*70)
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Sheet: {SHEET_NAME}")
    print("="*70)
    
    # Initialize components
    sheets = SheetsManager()
    processor = TransactionProcessor()
    tracker = PortfolioTracker()
    
    # Connect to Google Sheets
    if not sheets.connect():
        print("\n[!] Failed to connect to Google Sheets")
        return
    
    # Step 1: Read transactions
    print("\n" + "="*70)
    print("STEP 1: Reading Transactions...")
    print("="*70)
    
    transactions = sheets.read_transactions()
    
    if not transactions:
        print("\n[!] No transactions found")
        print(f"\nAdd transactions to the '{TRANSACTIONS_TAB}' tab:")
        print("  Column A: Date")
        print("  Column B: Ticker")
        print("  Column C: Type (BUY or SELL)")
        print("  Column D: Company Name")
        print("  Column E: Number of Shares")
        print("  Column F: Price per Share")
        return
    
    # Step 2: Process transactions into portfolio
    print("\n" + "="*70)
    print("STEP 2: Processing Transactions (BUY/SELL)...")
    print("="*70)
    
    active_portfolio, all_portfolio = processor.process_transactions(transactions)
    processor.print_transaction_summary(active_portfolio, all_portfolio)
    
    # Show transaction stats
    stats = processor.get_transaction_stats(all_portfolio)
    print(f"\n[i] Transaction Stats:")
    print(f"  Total BUY transactions: {stats['total_buy_transactions']}")
    print(f"  Total SELL transactions: {stats['total_sell_transactions']}")
    print(f"  Active positions: {stats['active_positions']}")
    print(f"  Closed positions: {stats['closed_positions']}")
    
    # Step 3: Sync to Portfolio tab
    print("\n" + "="*70)
    print("STEP 3: Syncing to Portfolio Tab (Google Sheets)...")
    print("="*70)
    
    portfolio_holdings = processor.get_portfolio_holdings(active_portfolio)
    
    if not portfolio_holdings:
        print("\n[!] No active positions to sync (all positions may be sold)")
        return
    
    if UPDATE_SHEET:
        sheets.sync_portfolio(portfolio_holdings)
    
    # Step 4: Fetch current prices and dividends
    print("\n" + "="*70)
    print("STEP 4: Fetching Prices & Dividends...")
    print("="*70)
    
    positions = []
    
    for holding in portfolio_holdings:
        ticker = holding['ticker']
        shares = holding['shares']
        avg_cost = holding['avg_cost']
        realized_gl = holding.get('realized_gain_loss', 0)
        
        print(f"\n{ticker}: {shares} shares @ ${avg_cost:.2f}")
        
        # Get current price and dividend data
        price_data = tracker.get_stock_price(ticker)
        
        if not price_data:
            print(f"  [!] Could not fetch data, skipping...")
            continue
        
        # Calculate position metrics
        position = tracker.calculate_position(
            ticker, shares, avg_cost, price_data, realized_gl
        )
        
        if position:
            positions.append(position)
            
            gain_symbol = "[+]" if position['gain_loss'] >= 0 else "[-]"
            total_info = ""
            if position['realized_gain_loss'] != 0:
                total_symbol = "[+]" if position['total_gain_loss'] >= 0 else "[-]"
                total_info = f" | {total_symbol} Total G/L: ${position['total_gain_loss']:+,.2f}"
            
            div_info = ""
            if position['annual_dividend'] > 0:
                div_info = f"\n  Dividend: ${position['annual_dividend']:.2f}/share ({position['dividend_yield']*100:.2f}% yield) | Annual Income: ${position['annual_income']:,.2f}"
            
            print(f"  {gain_symbol} Value: ${position['market_value']:,.2f} | "
                  f"Unrealized G/L: ${position['gain_loss']:+,.2f} ({position['gain_loss_pct']:+.2f}%){total_info}{div_info}")
    
    if not positions:
        print("\n[!] No positions could be calculated")
        return
    
    # Step 5: Calculate portfolio summary
    print("\n" + "="*70)
    print("STEP 5: Calculating Portfolio Totals...")
    print("="*70)
    
    summary = tracker.calculate_portfolio_summary(positions)
    tracker.print_summary(summary)
    
    # Step 6: Update Google Sheets with all data
    if UPDATE_SHEET:
        print("\n" + "="*70)
        print("STEP 6: Updating Google Sheets...")
        print("="*70)
        
        # Update portfolio prices and dividends
        if sheets.update_portfolio_prices(positions):
            print("[+] Portfolio data updated")
        
        print("\nAll data synced to Google Sheets")
    
    # Show failed tickers
    failed = tracker.get_failed_tickers()
    if failed:
        print(f"\n[!] Failed to fetch data for: {', '.join(failed)}")
    
    print("\n" + "="*70)
    print("Portfolio sync complete")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

