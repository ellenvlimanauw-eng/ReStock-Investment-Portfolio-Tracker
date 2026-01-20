"""
Portfolio Tracker
Fetches real-time stock prices and calculates portfolio performance
Includes sector information and dividend tracking
"""

import yfinance as yf
from datetime import datetime
import time
from config import *


class PortfolioTracker:
    """Tracks portfolio holdings and calculates performance metrics"""
    
    def __init__(self):
        self.price_cache = {}
        self.failed_tickers = []
    
    def get_stock_price(self, ticker):
        """
        Fetch current stock price and dividend info using yfinance
        
        Returns:
            dict with 'price', 'change_pct', 'name', 'sector', 'annual_dividend', 'dividend_yield', or None if failed
        """
        # Check cache first
        if ticker in self.price_cache:
            return self.price_cache[ticker]
        
        # Try to fetch
        for attempt in range(MAX_RETRIES):
            try:
                if VERBOSE:
                    print(f"  Fetching {ticker}...", end=" ")
                
                stock = yf.Ticker(ticker)
                
                # Get current data
                info = stock.info
                hist = stock.history(period="2d")
                
                if hist.empty or len(hist) < 1:
                    raise ValueError("No price data available")
                
                # Current price
                current_price = hist['Close'].iloc[-1]
                
                # Calculate daily change
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[-2]
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                else:
                    change_pct = 0
                
                # Company name
                name = info.get('longName', info.get('shortName', ticker))
                
                # Sector information
                sector = info.get('sector', 'Unknown')
                industry = info.get('industry', 'Unknown')
                
                # Dividend information
                annual_dividend = info.get('dividendRate', 0)  # Annual dividend per share
                dividend_yield = info.get('dividendYield', 0)  # As decimal (e.g., 0.0052 = 0.52%)
                
                result = {
                    'price': current_price,
                    'change_pct': change_pct,
                    'name': name,
                    'sector': sector,
                    'industry': industry,
                    'annual_dividend': annual_dividend if annual_dividend else 0,
                    'dividend_yield': dividend_yield if dividend_yield else 0,
                    'success': True
                }
                
                # Cache it
                self.price_cache[ticker] = result
                
                if VERBOSE:
                    div_info = f" | Div: ${annual_dividend:.2f}" if annual_dividend > 0 else ""
                    print(f"${current_price:.2f} ({change_pct:+.2f}%) | {sector}{div_info}")
                
                return result
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    if VERBOSE:
                        print(f"Retry {attempt + 1}/{MAX_RETRIES}...")
                    time.sleep(RETRY_DELAY)
                else:
                    if VERBOSE:
                        print(f"[!] FAILED: {str(e)}")
                    self.failed_tickers.append(ticker)
                    return None
        
        return None
    
    def calculate_position(self, ticker, shares, avg_cost, current_price_data, realized_gain_loss=0):
        """
        Calculate all metrics for a single position including dividends
        
        Args:
            ticker: Stock ticker symbol
            shares: Number of shares
            avg_cost: Average cost per share
            current_price_data: Dict with price info
            realized_gain_loss: Realized gains from past sells (default: 0)
        
        Returns:
            dict with all calculated values including dividend info
        """
        if not current_price_data or not shares or shares <= 0:
            return None
        
        current_price = current_price_data['price']
        day_change_pct = current_price_data['change_pct']
        annual_dividend = current_price_data.get('annual_dividend', 0)
        dividend_yield = current_price_data.get('dividend_yield', 0)
        
        # Basic calculations
        cost_basis = shares * avg_cost
        market_value = shares * current_price
        unrealized_gain_loss = market_value - cost_basis
        unrealized_gain_loss_pct = (unrealized_gain_loss / cost_basis * 100) if cost_basis > 0 else 0
        
        # Today's gain/loss
        prev_price = current_price / (1 + day_change_pct / 100)
        day_gain_loss = shares * (current_price - prev_price)
        
        # Total gain/loss (realized + unrealized)
        total_gain_loss = unrealized_gain_loss + realized_gain_loss
        
        # Dividend calculations
        annual_income = shares * annual_dividend
        
        return {
            'ticker': ticker,
            'name': current_price_data['name'],
            'sector': current_price_data.get('sector', 'Unknown'),
            'industry': current_price_data.get('industry', 'Unknown'),
            'shares': shares,
            'avg_cost': avg_cost,
            'current_price': current_price,
            'market_value': market_value,
            'cost_basis': cost_basis,
            'gain_loss': unrealized_gain_loss,
            'gain_loss_pct': unrealized_gain_loss_pct,
            'realized_gain_loss': realized_gain_loss,
            'total_gain_loss': total_gain_loss,
            'day_change_pct': day_change_pct,
            'day_gain_loss': day_gain_loss,
            'annual_dividend': annual_dividend,
            'dividend_yield': dividend_yield,
            'annual_income': annual_income,
            'allocation': 0  # Calculated later
        }
    
    def calculate_sector_allocation(self, positions):
        """
        Calculate sector allocation from positions
        
        Args:
            positions: List of position dicts
        
        Returns:
            dict with sector allocations
        """
        sector_data = {}
        total_value = sum(p['market_value'] for p in positions)
        
        for position in positions:
            sector = position.get('sector', 'Unknown')
            
            if sector not in sector_data:
                sector_data[sector] = {
                    'sector': sector,
                    'market_value': 0,
                    'cost_basis': 0,
                    'gain_loss': 0,
                    'positions': 0,
                    'tickers': []
                }
            
            sector_data[sector]['market_value'] += position['market_value']
            sector_data[sector]['cost_basis'] += position['cost_basis']
            sector_data[sector]['gain_loss'] += position['gain_loss']
            sector_data[sector]['positions'] += 1
            sector_data[sector]['tickers'].append(position['ticker'])
        
        # Calculate percentages
        for sector in sector_data.values():
            sector['allocation_pct'] = (sector['market_value'] / total_value * 100) if total_value > 0 else 0
            sector['gain_loss_pct'] = (sector['gain_loss'] / sector['cost_basis'] * 100) if sector['cost_basis'] > 0 else 0
        
        # Sort by allocation
        sorted_sectors = sorted(sector_data.values(), key=lambda x: x['allocation_pct'], reverse=True)
        
        return sorted_sectors
    
    def print_sector_allocation(self, sector_allocation):
        """Print sector allocation summary"""
        print("\n" + "="*70)
        print("SECTOR ALLOCATION")
        print("="*70)
        
        for sector in sector_allocation:
            bar_length = int(sector['allocation_pct'] / 2)  # Scale to 50 chars max
            bar = "#" * bar_length
            
            gain_symbol = "[+]" if sector['gain_loss'] >= 0 else "[-]"
            
            print(f"\n{sector['sector']}")
            print(f"  {bar} {sector['allocation_pct']:.1f}%")
            print(f"  Value: ${sector['market_value']:,.2f} | Positions: {sector['positions']}")
            print(f"  {gain_symbol} G/L: ${sector['gain_loss']:+,.2f} ({sector['gain_loss_pct']:+.2f}%)")
            print(f"  Tickers: {', '.join(sector['tickers'])}")
        
        print("="*70)
    
    def calculate_portfolio_summary(self, positions):
        """
        Calculate overall portfolio metrics including dividend income
        
        Args:
            positions: List of position dicts
        
        Returns:
            dict with portfolio totals
        """
        total_market_value = sum(p['market_value'] for p in positions)
        total_cost_basis = sum(p['cost_basis'] for p in positions)
        total_unrealized_gain_loss = sum(p['gain_loss'] for p in positions)
        total_realized_gain_loss = sum(p.get('realized_gain_loss', 0) for p in positions)
        total_gain_loss = total_unrealized_gain_loss + total_realized_gain_loss
        total_day_gain_loss = sum(p['day_gain_loss'] for p in positions)
        total_annual_income = sum(p.get('annual_income', 0) for p in positions)
        
        total_gain_loss_pct = (total_unrealized_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0
        portfolio_yield = (total_annual_income / total_market_value * 100) if total_market_value > 0 else 0
        
        # Calculate allocation percentages
        for position in positions:
            position['allocation'] = (position['market_value'] / total_market_value * 100) if total_market_value > 0 else 0
        
        # Find best and worst performers
        if positions:
            best_performer = max(positions, key=lambda p: p['gain_loss_pct'])
            worst_performer = min(positions, key=lambda p: p['gain_loss_pct'])
        else:
            best_performer = worst_performer = None
        
        return {
            'total_positions': len(positions),
            'total_market_value': total_market_value,
            'total_cost_basis': total_cost_basis,
            'total_unrealized_gain_loss': total_unrealized_gain_loss,
            'total_realized_gain_loss': total_realized_gain_loss,
            'total_gain_loss': total_gain_loss,
            'total_gain_loss_pct': total_gain_loss_pct,
            'total_day_gain_loss': total_day_gain_loss,
            'total_annual_income': total_annual_income,
            'portfolio_yield': portfolio_yield,
            'best_performer': best_performer,
            'worst_performer': worst_performer
        }
    
    def print_summary(self, summary):
        """Print portfolio summary to console"""
        print("\n" + "="*70)
        print("PORTFOLIO SUMMARY")
        print("="*70)
        
        print(f"\nTotal Positions: {summary['total_positions']}")
        print(f"Total Market Value: ${summary['total_market_value']:,.2f}")
        print(f"Total Cost Basis: ${summary['total_cost_basis']:,.2f}")
        
        # Unrealized gains
        unrealized_gl = summary['total_unrealized_gain_loss']
        unrealized_pct = summary['total_gain_loss_pct']
        unrealized_symbol = "[+]" if unrealized_gl >= 0 else "[-]"
        
        print(f"\n{unrealized_symbol} Unrealized Gain/Loss: ${unrealized_gl:+,.2f} ({unrealized_pct:+.2f}%)")
        
        # Realized gains
        if summary['total_realized_gain_loss'] != 0:
            realized_gl = summary['total_realized_gain_loss']
            realized_symbol = "[+]" if realized_gl >= 0 else "[-]"
            print(f"{realized_symbol} Realized Gain/Loss: ${realized_gl:+,.2f}")
            
            # Total
            total_gl = summary['total_gain_loss']
            total_symbol = "[+]" if total_gl >= 0 else "[-]"
            print(f"{total_symbol} Total Gain/Loss: ${total_gl:+,.2f}")
        
        day_gain = summary['total_day_gain_loss']
        day_symbol = "[^]" if day_gain >= 0 else "[v]"
        print(f"{day_symbol} Today's Change: ${day_gain:+,.2f}")
        
        # Dividend income
        if summary['total_annual_income'] > 0:
            print(f"\n[$] Annual Dividend Income: ${summary['total_annual_income']:,.2f}")
            print(f"Portfolio Yield: {summary['portfolio_yield']:.2f}%")
        
        # Best and worst
        if summary['best_performer']:
            best = summary['best_performer']
            print(f"\n[+] Best Performer: {best['ticker']} ({best['gain_loss_pct']:+.2f}%)")
        
        if summary['worst_performer']:
            worst = summary['worst_performer']
            print(f"[-] Worst Performer: {worst['ticker']} ({worst['gain_loss_pct']:+.2f}%)")
        
        print("\n" + "="*70)
    
    def get_failed_tickers(self):
        """Return list of tickers that failed to update"""
        return self.failed_tickers
