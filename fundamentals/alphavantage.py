

import pandas as pd 
import logging 
import requests
from utils.config import env
import numpy as np 
from utils.config import env
import os
from datetime import datetime 

class AlphavantageFinancialDataGatherer:
    def __init__(self):
        self.api_key = env.ALPHAVANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self._setup_logging()

    def call_api(self, stock_symbol: str, function: str) -> pd.DataFrame:
        try:
            self.logger.info(f"Making API call for {stock_symbol} with function {function}")
            url = f"{self.base_url}?function={function}&symbol={stock_symbol}&apikey={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            if 'Note' in data:
                self.logger.warning(f"API Note: {data['Note']}")
                
            self.logger.info(f"Successfully retrieved data for {stock_symbol}")
            return pd.DataFrame(data['quarterlyEarnings']) if function=="EARNINGS" else pd.DataFrame(data['quarterlyReports'])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {stock_symbol}: {str(e)}")
            raise
        except (KeyError, ValueError) as e:
            self.logger.error(f"Data processing error for {stock_symbol}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in call_api for {stock_symbol}: {str(e)}")
            raise
    
    def filter_timeframe(self, df: pd.DataFrame, timeframe: str = "year") -> pd.DataFrame:
        if timeframe == "year":
            time_delta = 365
        elif timeframe == "month":
            time_delta = 30
        elif timeframe == "week":
            time_delta = 7
        df['fiscalDateEnding'] = pd.to_datetime(df['fiscalDateEnding'])
        df = df[df['fiscalDateEnding'] > pd.Timestamp.now() - pd.Timedelta(days=time_delta)]
        return df
    
    def filter_latest(self, df: pd.DataFrame): 
        '''get the latest 4 quarters data'''
        # Convert 'fiscalDateEnding' to datetime
        df['fiscalDateEnding'] = pd.to_datetime(df['fiscalDateEnding'])

        # Sort the DataFrame by 'fiscalDateEnding' in descending order (latest to earliest)
        df = df.sort_values('fiscalDateEnding', ascending=False)

        # Get the first 4 rows (latest fiscal dates)
        latest_4_rows = df.head(4)
        return latest_4_rows
    
    
    def get_earnings(self, stock_symbol: str) -> pd.DataFrame:
        df = self.call_api(stock_symbol, "EARNINGS")
        

        # filter because there might be missing earnings data or None 
        df['reportedEPS'] = df['reportedEPS'].replace(['None', 'nan', ''], np.nan)
        df = df[df['reportedEPS'].notna()]
         
        # filter columsn to keep 
        columns_to_keep = ['fiscalDateEnding', 'reportedEPS', 'estimatedEPS', 'surprise', 'surprisePercentage']

        return df[columns_to_keep]
    
    def get_income_statement(self, stock_symbol: str) -> pd.DataFrame:
        df = self.call_api(stock_symbol, "INCOME_STATEMENT")

        # filter columns to keep 
        columns_to_keep = ['fiscalDateEnding', 'netIncome']
        return df[columns_to_keep]
    
    def get_balance_sheet(self, stock_symbol: str) -> pd.DataFrame:
        df = self.call_api(stock_symbol, "BALANCE_SHEET")

        #filter columns to keep 
        columns_to_keep = ['fiscalDateEnding', 'totalAssets', 'totalShareholderEquity', 'commonStockSharesOutstanding', 'totalLiabilities', 'totalCurrentAssets', 'totalCurrentLiabilities', 'inventory']
        return df[columns_to_keep]
    
    def get_cash_flow(self, stock_symbol: str) -> pd.DataFrame:
        df = self.call_api(stock_symbol, "CASH_FLOW")
        # filter columns to keep
        columns_to_keep= ['fiscalDateEnding', 'operatingCashflow', 'capitalExpenditures']
        return df[columns_to_keep]
    
    def get_financial_data(self, stock_symbol: str) -> pd.DataFrame:    
        try:
            self.logger.info(f"Starting financial data gathering for {stock_symbol}")
            earnings_df = self.get_earnings(stock_symbol)
            income_statement_df = self.get_income_statement(stock_symbol)
            balance_sheet_df = self.get_balance_sheet(stock_symbol)
            cash_flow_df = self.get_cash_flow(stock_symbol)
            
            # merge all the dataframes on the fiscalDateEnding column
            df = pd.merge(earnings_df, income_statement_df, on='fiscalDateEnding', how='left')
            df = pd.merge(df, balance_sheet_df, on='fiscalDateEnding', how='left')
            df = pd.merge(df, cash_flow_df, on='fiscalDateEnding', how='left')
            # Convert all columns except 'fiscalDateEnding' to numeric
            df[df.columns.difference(['fiscalDateEnding'])] = df[df.columns.difference(['fiscalDateEnding'])].apply(pd.to_numeric)

            self.logger.info(f"Successfully compiled financial data for {stock_symbol}")
            return df
        except Exception as e:
            self.logger.error(f"Error gathering financial data for {stock_symbol}: {str(e)}")
            raise
    
    def calculate_changes(self, df): 
        try:
            self.logger.info("Calculating percentage changes and free cash flow")
            df = df.sort_values('fiscalDateEnding', ascending=True)
            df['EPS_pct_change'] = df['reportedEPS'].pct_change() * 100  # Multiply by 100 to get percentage
            df['netIncome_pct_change'] = df['netIncome'].pct_change() * 100
            df['freeCashflow'] = df['operatingCashflow']- df['capitalExpenditures']
            self.logger.info("Successfully calculated changes and free cash flow")
            return df
        except Exception as e:
            self.logger.error(f"Error calculating changes: {str(e)}")
            raise
    
    def calculate_ratios(self, df: pd.DataFrame): 
        try:
            self.logger.info("Calculating financial ratios")
            df['bookValuePerShare'] = df['totalShareholderEquity']/df['commonStockSharesOutstanding']
            df['returnOnEquity'] = df['netIncome']/df['totalShareholderEquity']
            df['debtToEquityRatio'] = df['totalLiabilities']/df['totalShareholderEquity']
            df['currentRatio'] = df['totalCurrentAssets']/df['totalCurrentLiabilities']
            df['quickRatio'] = (df['totalCurrentAssets']-df['inventory'])/df['totalCurrentLiabilities']
            df['leverageRatio'] = df['totalLiabilities']/df['totalAssets']
            self.logger.info("Successfully calculated financial ratios")
            return df
        except Exception as e:
            self.logger.error(f"Error calculating ratios: {str(e)}")
            raise
    
    def initialise_units(self, df:pd.DataFrame): 
        units_dict= {
    # Earnings & Revenue-related
    'reportedEPS': 'USD/share',
    'estimatedEPS': 'USD/share',
    'surprise': 'USD/share',
    'surprisePercentage': '%',
    'netIncome': 'USD',
    
    # Performance Metrics
    'EPS_pct_change': '%',
    'netIncome_pct_change': '%',
    'bookValuePerShare': 'USD/share',
    'returnOnEquity': '%',
    
    # Balance Sheet Metrics
    'totalAssets': 'USD',
    'totalLiabilities': 'USD',
    'totalCurrentAssets': 'USD',
    'totalCurrentLiabilities': 'USD',
    'inventory': 'USD',
    'totalShareholderEquity': 'USD',
    'commonStockSharesOutstanding': 'shares',
    
    # Cash Flow-related
    'operatingCashflow': 'USD',
    'freeCashflow': 'USD',
    
    # Financial Ratios
    'debtToEquityRatio': 'None',
    'currentRatio': 'None',
    'quickRatio': 'None',
    'leverageRatio': 'None',

}
    
        ## tranpose the dataframe 
        df.set_index('fiscalDateEnding', inplace=True)
        transposed_df = df.T

        transposed_df['Unit'] = transposed_df.index.map(units_dict)
        ordered_metrics = list(units_dict.keys())
        transposed_df = transposed_df.loc[ordered_metrics]
        # 3. Identify numeric columns
        numeric_cols = transposed_df.columns.difference(["Unit"])
        usd_mask = transposed_df["Unit"] == "USD"
        transposed_df.loc[usd_mask, numeric_cols] = transposed_df.loc[usd_mask, numeric_cols] / 1_000_000

        return transposed_df
    def convert_df_to_html(self, df: pd.DataFrame) -> str:
        """Convert the dataframe to an html table."""
        self.logger.info("Converting DataFrame to HTML format")
        try:
            html_table = df.to_html(index=False)
            self.logger.info(f"Successfully converted DataFrame to HTML. Length: {len(html_table)} characters")
            return html_table
        except Exception as e:
            self.logger.error(f"Error converting DataFrame to HTML: {e}", exc_info=True)
            raise
    
    
    def from_stock_to_dataframe(self, ticker: str): 
        try:
            self.logger.info(f"Processing complete financial analysis for {ticker}")
            df = self.get_financial_data(ticker)
            df = self.calculate_changes(df)
            df = self.calculate_ratios(df)
            df = self.filter_latest(df)
            df = self.initialise_units(df)
            df = self.convert_df_to_html(df)

            self.logger.info(f"Successfully completed financial analysis for {ticker}")
            return df
        except Exception as e:
            self.logger.error(f"Error in complete financial analysis for {ticker}: {str(e)}")
            raise 

    def _setup_logging(self):
        """Setup logging configuration to save logs to file"""
        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Configure logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplication
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler
        log_filename = os.path.join(logs_dir, f"alphavantage_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    



    
    
    


