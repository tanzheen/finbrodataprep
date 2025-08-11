import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime
import os


class FinvizScraper: 
    def __init__(self):
        self.base_url = "https://finviz.com/screener.ashx"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_total_results(self, soup):
        """Extract total number of results"""
        try:
            # Look for text like "Total: 45"
            total_element = soup.find('td', string=re.compile(r'Total:'))
            if total_element:
                total_text = total_element.get_text()
                total_match = re.search(r'Total:\s*(\d+)', total_text)
                if total_match:
                    return int(total_match.group(1))
            
            # Alternative: look for pagination info
            pagination = soup.find('option', selected=True)
            if pagination:
                page_text = pagination.get_text()  # e.g., "1 - 20 of 45"
                match = re.search(r'of\s+(\d+)', page_text)
                if match:
                    return int(match.group(1))
            
            return 0
        except:
            return 0
    
    def scrape_page(self, filters=None, table_type='111', page=1):
        """Scrape a single page"""
        
        params = {
            'v': table_type,
            'r': str((page - 1) * 20 + 1)  # Start row for pagination
        }
        
        if filters:
            params['f'] = ','.join(filters)
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find main table
            table = soup.find('table', class_='screener_table')
            if not table:
                return None, 0
            
            # Get total results on first page
            total_results = self.get_total_results(soup) if page == 1 else 0
            
            # Extract headers
            header_row = table.find('tr')
            headers = [th.get_text().strip() for th in header_row.find_all(['td', 'th'])]
            
            # Extract data
            data_rows = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = []
                
                for cell in cells:
                    # Handle ticker links
                    link = cell.find('a')
                    if link and '/quote.ashx?t=' in link.get('href', ''):
                        row_data.append(link.get_text().strip())
                    else:
                        row_data.append(cell.get_text().strip())
                
                if len(row_data) == len(headers):
                    data_rows.append(row_data)
            
            return pd.DataFrame(data_rows, columns=headers), total_results
            
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            return None, 0
    

    def scrape_all_pages(self, filters=None, table_type='111'):
        """Scrape all pages of results - fixed version"""
        
        print(f"Starting scrape with filters: {filters}")
        
        all_data = []
        page = 1
        
        while True:
            print(f"Scraping page {page}...")
            
            df_page, total_results = self.scrape_page(filters, table_type, page)
            
            if df_page is None or df_page.empty:
                print(f"No more data found at page {page}")
                break
            
            all_data.append(df_page)
            print(f"Page {page}: Got {len(df_page)} stocks")
            
            # If we get less than 20 results, this is likely the last page
            if len(df_page) < 20:
                print(f"Last page reached (only {len(df_page)} results on this page)")
                break
            
            page += 1
            time.sleep(1)  # Be respectful with delays
            
            # Safety limit
            if page > 50:
                print("Reached safety limit of 50 pages")
                break
        
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            print(f"Successfully scraped {len(final_df)} total stocks from {len(all_data)} pages")
            return final_df
        else:
            print("No data found")
            return None


class FinvizScreener:
    """
    A comprehensive Finviz screener class for finding investment opportunities.
    Based on the URL: https://finviz.com/screener.ashx?v=111&f=exch_nasd,fa_epsyoyttm_pos,fa_evebitda_o10,fa_pe_u25,fa_roa_o10,fa_roe_o15,fa_salesyoyttm_o5&ft=2&r=21
    """
    
    def __init__(self, base_filters: Optional[List[str]] = None):
        """
        Initialize the screener with optional base filters.
        
        Args:
            base_filters: List of base filters to apply to all screens
        """
        self.base_filters = base_filters or []
        self.scraper = FinvizScraper()
        self.current_results = None
        self.current_df = None
        
    def quality_growth_screen(self, market_cap: str = 'largeover') -> pd.DataFrame:
        """
        Screen for quality growth stocks based on your URL parameters.
        
        Args:
            market_cap: Market cap filter ('largeover', 'midover', 'smallover', etc.)
            
        Returns:
            DataFrame with screening results
        """
        filters = self.base_filters + [
            f'cap_{market_cap}',           # Market cap
            'exch_nasd',                   # NASDAQ exchange
            'fa_epsyoyttm_pos',           # Positive EPS growth YoY
            'fa_evebitda_o10',            # EV/EBITDA over 10
            'fa_pe_u25',                  # P/E under 25
            'fa_roa_o10',                 # ROA over 10%
            'fa_roe_o15',                 # ROE over 15%
            'fa_salesyoyttm_o5'           # Sales growth YoY over 5%
        ]
        
        self.current_df = self.scraper.scrape_all_pages(filters, table_type='111')
        return self.current_df
    
    def dividend_growth_screen(self, min_yield: float = 2.0) -> pd.DataFrame:
        """
        Screen for dividend growth stocks.
        
        Args:
            min_yield: Minimum dividend yield percentage
            
        Returns:
            DataFrame with screening results
        """
        yield_filter = f'fa_div_o{int(min_yield)}'
        filters = self.base_filters + [
            'cap_largeover',
            'exch_nasd',
            'fa_div_pos',                 # Positive dividend
            yield_filter,                 # Minimum yield
            'fa_pe_u20',                  # P/E under 20
            'fa_roe_o10',                 # ROE over 10%
            'fa_payoutratio_u60'          # Payout ratio under 60%
        ]
        
        self.current_df = self.scraper.scrape_all_pages(filters, table_type='121')  # Dividends table
        return self.current_df
    
    def value_screen(self) -> pd.DataFrame:
        """
        Screen for undervalued stocks.
        
        Returns:
            DataFrame with screening results
        """
        filters = self.base_filters + [
            'cap_largeover',
            'exch_nasd',
            'fa_pe_u15',                  # P/E under 15
            'fa_pb_u2',                   # P/B under 2
            'fa_pfcf_u15',                # P/FCF under 15
            'fa_roe_o10',                 # ROE over 10%
            'fa_roa_o5',                  # ROA over 5%
            'fa_debt_u0.5'                # Debt/Equity under 0.5
        ]
        
        self.current_df = self.scraper.scrape_all_pages(filters, table_type='161')  # Valuation table
        return self.current_df
    
    def momentum_screen(self) -> pd.DataFrame:
        """
        Screen for momentum stocks.
        
        Returns:
            DataFrame with screening results
        """
        filters = self.base_filters + [
            'cap_largeover',
            'exch_nasd',
            'ta_perf_13w_o10',            # 13-week performance over 10%
            'ta_perf_26w_o20',            # 26-week performance over 20%
            'ta_rsi_no60',                # RSI not overbought (under 60)
            'fa_epsyoyttm_o20',           # EPS growth over 20%
            'ta_sma20_pa',                # Price above 20-day MA
            'ta_sma50_pa'                 # Price above 50-day MA
        ]
        
        self.current_df = self.scraper.scrape_all_pages(filters, table_type='111')  # Performance table
        return self.current_df
    
    def custom_screen(self, filters: List[str], table: str = 'Overview', 
                     order: str = 'ticker') -> pd.DataFrame:
        """
        Create a custom screen with specified filters.
        
        Args:
            filters: List of filter strings
            table: Table to display ('Overview', 'Performance', 'Valuation', etc.)
            order: Column to sort by (ignored in scraper version)
            
        Returns:
            DataFrame with screening results
        """
        all_filters = self.base_filters + filters
        
        # Map table types to finviz table codes
        table_map = {
            'Overview': '111',
            'Performance': '111', 
            'Valuation': '161',
            'Dividends': '121',
            'Financial': '161'
        }
        
        table_type = table_map.get(table, '111')
        self.current_df = self.scraper.scrape_all_pages(all_filters, table_type=table_type)
        return self.current_df
    
    def export_results(self, filename: str, format: str = 'csv') -> str:
        """
        Export screening results to file.
        
        Args:
            filename: Output filename (without extension)
            format: Export format ('csv' or 'sqlite')
            
        Returns:
            Path to exported file
        """
        if self.current_df is None or self.current_df.empty:
            raise ValueError("No screening results to export. Run a screen first.")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == 'csv':
            filepath = f"{filename}_{timestamp}.csv"
            self.current_df.to_csv(filepath, index=False)
        elif format.lower() == 'sqlite':
            filepath = f"{filename}_{timestamp}.sqlite3"
            import sqlite3
            conn = sqlite3.connect(filepath)
            self.current_df.to_sql('screening_results', conn, if_exists='replace', index=False)
            conn.close()
        else:
            raise ValueError("Format must be 'csv' or 'sqlite'")
        
        return filepath
    
    def get_top_stocks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top N stocks from current screening results.
        
        Args:
            limit: Number of stocks to return
            
        Returns:
            List of stock dictionaries
        """
        if self.current_df is None or self.current_df.empty:
            raise ValueError("No screening results available. Run a screen first.")
        
        return self.current_df.head(limit).to_dict('records')
    
    def analyze_stock(self, ticker: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific stock from current results.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with stock information
        """
        if self.current_df is None or self.current_df.empty:
            raise ValueError("No screening results available. Run a screen first.")
        
        # Find the row with matching ticker (assuming first column is ticker)
        ticker_col = self.current_df.columns[0]  # Usually 'No.' or 'Ticker'
        
        # Try to find ticker in first few columns
        for col in self.current_df.columns[:3]:
            try:
                # Convert to string and handle NaN values
                col_values = self.current_df[col].astype(str).str.upper()
                matching_rows = self.current_df[col_values == ticker.upper()]
                if not matching_rows.empty:
                    return matching_rows.iloc[0].to_dict()
            except:
                continue
        
        raise ValueError(f"Ticker {ticker} not found in current screening results.")
    
    def get_screening_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of current screening results.
        
        Returns:
            Dictionary with summary information
        """
        if self.current_df is None or self.current_df.empty:
            raise ValueError("No screening results available. Run a screen first.")
        
        if len(self.current_df) == 0:
            return {"total_stocks": 0, "message": "No stocks found matching criteria"}
        
        df = self.current_df
        
        # Try to find ticker column (usually second column after 'No.')
        ticker_col = None
        for col in df.columns[1:4]:  # Check first few columns for ticker
            try:
                # Check if this looks like a ticker column (short strings, typically 1-5 chars)
                sample_lengths = df[col].str.len().head(5)
                if sample_lengths.max() <= 5 and sample_lengths.min() >= 1:
                    ticker_col = col
                    break
            except:
                continue
        
        summary = {
            "total_stocks": len(df),
            "sample_stocks": df[ticker_col].head(10).tolist() if ticker_col else [],
        }
        
        # Add more stats if we can find the right columns
        for col in df.columns:
            if 'P/E' in col or 'PE' in col:
                try:
                    pe_values = pd.to_numeric(df[col].replace('-', None), errors='coerce')
                    summary["avg_pe"] = pe_values.mean()
                except:
                    pass
            elif 'Sector' in col:
                try:
                    summary["sectors"] = df[col].value_counts().to_dict()
                except:
                    pass
            elif 'Change' in col:
                try:
                    change_values = pd.to_numeric(df[col].str.replace('%', ''), errors='coerce')
                    top_performers_idx = change_values.nlargest(5).index
                    summary["top_performers"] = df.loc[top_performers_idx, ticker_col].tolist() if ticker_col else []
                except:
                    pass
        
        return summary
    
    def print_results(self, limit: Optional[int] = None):
        """
        Print screening results to console.
        
        Args:
            limit: Maximum number of results to print
        """
        if self.current_df is None or self.current_df.empty:
            raise ValueError("No screening results available. Run a screen first.")
        
        if limit:
            print(self.current_df.head(limit).to_string())
        else:
            print(self.current_df.to_string())


# Predefined screening strategies
class ScreeningStrategies:
    """Predefined screening strategies for different investment approaches."""
    
    @staticmethod
    def warren_buffett_style() -> List[str]:
        """Warren Buffett style value investing filters."""
        return [
            'cap_largeover',              # Large cap
            'fa_roe_o15',                # ROE > 15%
            'fa_pe_u20',                 # P/E < 20
            'fa_debt_u0.4',              # Low debt
            'fa_eps5years_o10',          # 5-year EPS growth > 10%
            'fa_epsyoy_o5'               # YoY EPS growth > 5%
        ]
    
    @staticmethod
    def peter_lynch_style() -> List[str]:
        """Peter Lynch style growth investing filters."""
        return [
            'cap_midover',               # Mid to large cap
            'fa_epsyoy_o15',            # EPS growth > 15%
            'fa_pe_u25',                # P/E < 25
            'fa_peg_u1.5',              # PEG < 1.5
            'ta_perf_52w_o10'           # 52-week performance > 10%
        ]
    
    @staticmethod
    def dividend_aristocrat_style() -> List[str]:
        """Dividend aristocrat style filters."""
        return [
            'cap_largeover',             # Large cap
            'fa_div_pos',               # Positive dividend
            'fa_div_o2',                # Dividend yield > 2%
            'fa_payoutratio_u60',       # Payout ratio < 60%
            'fa_roe_o12'                # ROE > 12%
        ]


# Example usage and testing
'''
if __name__ == "__main__":
    # Initialize screener
    screener = FinvizScreener()
    
    # Run quality growth screen
    print("=== Quality Growth Screen ===")
    results = screener.quality_growth_screen()
    
    if results is not None and not results.empty:
        # Get top 10 stocks
        top_stocks = screener.get_top_stocks(10)
        
        # Find ticker column (usually second column)
        ticker_col = None
        price_col = None
        for i, col in enumerate(results.columns):
            if i == 1:  # Usually ticker is second column
                ticker_col = col
            if 'Price' in col:
                price_col = col
        
        for stock in top_stocks:
            ticker = stock.get(ticker_col, 'N/A') if ticker_col else 'N/A'
            price = stock.get(price_col, 'N/A') if price_col else 'N/A'
            print(f"{ticker}: ${price}")
        
        # Export results
        export_path = screener.export_results("quality_growth_stocks")
        print(f"\nResults exported to: {export_path}")
        
        # Get summary
        summary = screener.get_screening_summary()
        print(f"\nTotal stocks found: {summary['total_stocks']}")
    else:
        print("No results found or error occurred.")
'''