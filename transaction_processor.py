"""
Transaction Processor
Reads transactions and calculates consolidated portfolio positions
Supports buy and sell transactions
"""

from datetime import datetime
from config import *


class TransactionProcessor:
    """Processes transactions and builds portfolio"""
    
    def process_transactions(self, transactions):
        """
        Group transactions by ticker and calculate average cost
        Handles both BUY and SELL transactions
        
        Args:
            transactions: List of transaction dicts
        
        Returns:
            Tuple of (active_portfolio, all_portfolio)
        """
        if VERBOSE:
            print(f"\n[i] Processing {len(transactions)} transactions...")
        
        # Group by ticker
        portfolio = {}
        
        for txn in transactions:
            ticker = txn.get('ticker', '')
            shares = txn.get('shares', 0)
            price = txn.get('price', 0)
            name = txn.get('name', '')
            txn_type = txn.get('type', 'BUY').upper()
            
            # Validate transaction has required fields
            if not ticker:
                if VERBOSE:
                    print(f"  [!] Skipping transaction with no ticker")
                continue
            
            if shares <= 0 or price <= 0:
                if VERBOSE:
                    print(f"  [!] Skipping {ticker}: invalid shares or price")
                continue
            
            if ticker not in portfolio:
                portfolio[ticker] = {
                    'ticker': ticker,
                    'name': name,
                    'total_shares': 0,
                    'total_cost': 0,
                    'realized_gain_loss': 0,
                    'transactions': [],
                    'buy_transactions': [],
                    'sell_transactions': []
                }
            
            portfolio[ticker]['transactions'].append(txn)
            
            # Update name if it was empty before
            if not portfolio[ticker]['name'] and name:
                portfolio[ticker]['name'] = name
            
            if txn_type == 'BUY':
                # Add to position
                portfolio[ticker]['total_shares'] += shares
                portfolio[ticker]['total_cost'] += (shares * price)
                portfolio[ticker]['buy_transactions'].append(txn)
                
            elif txn_type == 'SELL':
                # Calculate realized gain/loss for this sell
                if portfolio[ticker]['total_shares'] > 0 and portfolio[ticker]['total_cost'] > 0:
                    # Current average cost before sell
                    avg_cost = portfolio[ticker]['total_cost'] / portfolio[ticker]['total_shares']
                    
                    # Realized gain/loss = (sell_price - avg_cost) * shares_sold
                    realized_gl = (price - avg_cost) * shares
                    portfolio[ticker]['realized_gain_loss'] += realized_gl
                    
                    # Reduce position
                    cost_basis_reduction = avg_cost * shares
                    portfolio[ticker]['total_shares'] -= shares
                    portfolio[ticker]['total_cost'] -= cost_basis_reduction
                    
                    # Ensure we don't go negative
                    if portfolio[ticker]['total_shares'] < 0:
                        if VERBOSE:
                            print(f"  [!] Warning: {ticker} sold more shares than owned!")
                        portfolio[ticker]['total_shares'] = 0
                        portfolio[ticker]['total_cost'] = 0
                
                portfolio[ticker]['sell_transactions'].append(txn)
        
        # Calculate average cost for each position
        for ticker, data in portfolio.items():
            if data['total_shares'] > 0 and data['total_cost'] > 0:
                data['avg_cost'] = data['total_cost'] / data['total_shares']
            else:
                data['avg_cost'] = 0
        
        # Remove tickers with zero shares (fully sold positions)
        active_portfolio = {
            ticker: data for ticker, data in portfolio.items() 
            if data['total_shares'] > 0
        }
        
        if VERBOSE:
            print(f"[+] Found {len(active_portfolio)} active positions")
            for ticker, data in active_portfolio.items():
                realized_info = f" (Realized G/L: ${data['realized_gain_loss']:+,.2f})" if data['realized_gain_loss'] != 0 else ""
                print(f"  {ticker}: {data['total_shares']} shares @ ${data['avg_cost']:.2f} avg{realized_info}")
            
            # Show fully sold positions
            sold_out = {ticker: data for ticker, data in portfolio.items() if data['total_shares'] == 0 and data['realized_gain_loss'] != 0}
            if sold_out:
                print(f"\n[+] Fully closed positions ({len(sold_out)}):")
                for ticker, data in sold_out.items():
                    print(f"  {ticker}: Realized G/L: ${data['realized_gain_loss']:+,.2f}")
        
        # Return as tuple (active_portfolio, all_portfolio)
        return (active_portfolio, portfolio)
    
    def get_portfolio_holdings(self, portfolio):
        """
        Convert portfolio dict to list of holdings for tracking
        
        Args:
            portfolio: Dict from process_transactions
        
        Returns:
            List of holdings dicts
        """
        holdings = []
        
        for ticker, data in portfolio.items():
            if data['total_shares'] > 0:  # Only include active positions
                holdings.append({
                    'ticker': ticker,
                    'name': data['name'],
                    'shares': data['total_shares'],
                    'avg_cost': data['avg_cost'],
                    'realized_gain_loss': data['realized_gain_loss']
                })
        
        return holdings
    
    def print_transaction_summary(self, active_portfolio, all_portfolio):
        """Print summary of transactions"""
        print("\n" + "="*70)
        print("TRANSACTION SUMMARY")
        print("="*70)
        
        # Active positions
        total_invested = sum(data['total_cost'] for data in active_portfolio.values())
        total_realized = sum(data['realized_gain_loss'] for data in all_portfolio.values())
        
        print(f"\nActive Positions: {len(active_portfolio)}")
        print(f"Total Invested: ${total_invested:,.2f}")
        
        if total_realized != 0:
            symbol = "[+]" if total_realized >= 0 else "[-]"
            print(f"{symbol} Total Realized Gains/Losses: ${total_realized:+,.2f}")
        
        print(f"\nCurrent Holdings:")
        for ticker in sorted(active_portfolio.keys()):
            data = active_portfolio[ticker]
            realized_str = f" | Realized: ${data['realized_gain_loss']:+,.2f}" if data['realized_gain_loss'] != 0 else ""
            print(f"  {ticker:6} -> {data['total_shares']:>6.0f} shares @ ${data['avg_cost']:>8.2f} avg = ${data['total_cost']:>10,.2f}{realized_str}")
        
        # Fully closed positions
        closed_positions = {
            ticker: data for ticker, data in all_portfolio.items() 
            if data['total_shares'] == 0 and data['realized_gain_loss'] != 0
        }
        
        if closed_positions:
            print(f"\n[X] Fully Closed Positions:")
            for ticker in sorted(closed_positions.keys()):
                data = closed_positions[ticker]
                symbol = "[+]" if data['realized_gain_loss'] >= 0 else "[-]"
                print(f"  {ticker:6} {symbol} Realized G/L: ${data['realized_gain_loss']:+,.2f}")
        
        print("="*70)
    
    def get_transaction_stats(self, all_portfolio):
        """Get overall transaction statistics"""
        total_buys = sum(len(data['buy_transactions']) for data in all_portfolio.values())
        total_sells = sum(len(data['sell_transactions']) for data in all_portfolio.values())
        total_realized = sum(data['realized_gain_loss'] for data in all_portfolio.values())
        
        return {
            'total_buy_transactions': total_buys,
            'total_sell_transactions': total_sells,
            'total_realized_gain_loss': total_realized,
            'active_positions': len([d for d in all_portfolio.values() if d['total_shares'] > 0]),
            'closed_positions': len([d for d in all_portfolio.values() if d['total_shares'] == 0 and d['realized_gain_loss'] != 0])
        }
