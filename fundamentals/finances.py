"""
Financial Data Gathering Module

This module provides a comprehensive class for gathering financial data about companies
using the finagg library. It collects various financial metrics including earnings,
balance sheet items, and financial ratios.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

from financetoolkit import Toolkit
from utils.config import env

# Setup logging
logger = logging.getLogger(__name__)

# EARNINGS PER SHARE done 
# EARNIGNS PER SHARE CHANGE (i think need to calculate)
# SHARES OUTSTANDING done from compute 
# NET INCOME done (includes loss)
# NET INCOME CHANGE (i think need to calculate)
# CASH (need to find other ways)
# ASSETS done 
# LIABILITIES done 
# STOCK HOLDER EQUITY done
# RETURN ON ASSETS done from compute 
# RETURN ON EQUITY done from compute 
# ASSET COVERAGE RATIO done from compute  
# BOOK VALUE PER SHARE 
# DEBT TO EQUITY RATIO done from compute 
# QUICK RATIO done from compute 
# WORKING CAPITAL RATIO done from compute 


class FinancialDataGatherer:
    """
    A class for gathering comprehensive financial data about companies using finagg.
    
    This class provides methods to collect various financial metrics including:
    - Earnings per Share (EPS)
    - Net Income
    - Balance Sheet items (Cash, Assets, Liabilities, Equity)
    - Financial Ratios (ROA, ROE, D/E, Quick Ratio, etc.)
    - Working Capital metrics
    """
    
    def __init__(self):
        """Initialize the FinancialDataGatherer."""
        logger.info("FinancialDataGatherer initialized")
        
    def get_values(self, stock: str):
        """Get the values of the financial data."""
        logger.info(f"Retrieving financial data for stock: {stock}")
        
        try:
            logger.info(f"Initializing Toolkit for {stock}")
            toolkit = Toolkit([stock], quarterly=True, api_key=env.FINANCIAL_API_KEY)
            
            logger.info(f"Retrieving Earnings Per Share for {stock}")
            eps = toolkit.ratios.get_earnings_per_share()
            eps.index = ['Earnings Per Share']
            
            logger.info(f"Retrieving Income Statement for {stock}")
            income_statement = toolkit.get_income_statement()
            income_statement = income_statement.loc[['Net Income']]
            
            logger.info(f"Retrieving Cash Flow Statement for {stock}")
            cash_state = toolkit.get_cash_flow_statement()
            cash_state = cash_state.loc[['Operating Cash Flow', 'Free Cash Flow']]
            
            logger.info(f"Retrieving Balance Sheet for {stock}")
            bal_sheet = toolkit.get_balance_sheet_statement()
            # Total Current Assets, Total Current Liabilities, Total Shareholder Equity
            rows_to_find = ['Total Current Assets', 'Total Current Liabilities', 'Total Shareholder Equity']
            bal_sheet = bal_sheet.loc[rows_to_find]
            
            logger.info(f"Retrieving financial ratios for {stock}")
            roe = toolkit.ratios.get_return_on_equity()
            roe.index = ["Return on Equity"]
            roa = toolkit.ratios.get_return_on_assets()
            roa.index = ['Return on Assets']
            bvps = toolkit.ratios.get_book_value_per_share()
            bvps.index = ['Book Value per Share']
            debt_service_coverage = toolkit.ratios.get_debt_service_coverage_ratio()
            debt_service_coverage.index = ['Debt Service Coverage Ratio']
            cash_flow_ratio = toolkit.ratios.get_cash_flow_coverage_ratio()
            cash_flow_ratio.index = ['Cash Flow Coverage Ratio']
            debt_to_equity = toolkit.ratios.get_debt_to_equity_ratio()
            debt_to_equity.index = ['Debt to Equity Ratio']
            current_ratio = toolkit.ratios.get_current_ratio()
            current_ratio.index = ['Current Ratio']

            # concat all the dataframes
            logger.info(f"Combining all financial data for {stock}")
            all_data = pd.concat([eps, income_statement, cash_state, bal_sheet, roe, roa, bvps, debt_service_coverage, cash_flow_ratio, debt_to_equity, current_ratio], axis=0)
            
            logger.info(f"Successfully retrieved financial data for {stock}. Shape: {all_data.shape}")
            return all_data
            
        except Exception as e:
            logger.error(f"Error retrieving financial data for {stock}: {e}", exc_info=True)
            raise
    
    def standardize_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize units and add percentage changes for financial data."""
        logger.info("Standardizing units and calculating percentage changes")
        
        try:
            # Assume df is your existing DataFrame

            # 1. Define units mapping
            units = {
                "Earnings Per Share": "USD/share",
                "Net Income": "USD",
                "Operating Cash Flow": "USD",
                "Free Cash Flow": "USD",
                "Total Current Assets": "USD",
                "Total Current Liabilities": "USD",
                "Total Shareholder Equity": "USD",
                "Return on Equity": "%",
                "Return on Assets": "%",
                "Book Value per Share": "USD/share",
                "Debt Service Coverage Ratio": "x",
                "Cash Flow Coverage Ratio": "x",
                "Debt to Equity Ratio": "x",
                "Current Ratio": "x"
            }

            # 2. Add Unit column
            df["Unit"] = df.index.map(units)

            # 3. Identify numeric columns
            numeric_cols = df.columns.difference(["Unit"])

            # 5. Calculate % change for EPS and Net Income
            logger.info("Calculating percentage changes for EPS and Net Income")
            eps_change = df.loc["Earnings Per Share", numeric_cols].pct_change(axis=0) * 100
            net_income_change = df.loc["Net Income", numeric_cols].pct_change(axis=0) * 100

            # 4. Apply scaling based on units
            logger.info("Applying unit scaling")
            usd_mask = df["Unit"] == "USD"
            df.loc[usd_mask, numeric_cols] = df.loc[usd_mask, numeric_cols] / 1_000_000
            df.loc[usd_mask, "Unit"] = "USD (M)"

            pct_mask = df["Unit"] == "%"
            df.loc[pct_mask, numeric_cols] = df.loc[pct_mask, numeric_cols] * 100
            df.loc[pct_mask, "Unit"] = "% (points)"

            # 6. Create new rows for % change
            eps_row = pd.Series({**{col: val for col, val in eps_change.items()}, **{"Unit": "% (QoQ)"}})
            net_income_row = pd.Series({**{col: val for col, val in net_income_change.items()}, **{"Unit": "% (QoQ)"}})

            # 7. Insert new rows at correct positions
            logger.info("Inserting percentage change rows")
            df = pd.concat(
                [
                    df.loc[:"Earnings Per Share"],
                    eps_row.to_frame().T.rename(index={0: "EPS % Change"}),
                    df.loc["Net Income":],
                ]
            )

            # After Net Income, insert Net Income % Change
            df = pd.concat(
                [
                    df.loc[:"Net Income"],
                    net_income_row.to_frame().T.rename(index={0: "Net Income % Change"}),
                    df.loc["Operating Cash Flow":],
                ]
            )

            # 8. Move Unit column to first position
            df = df[["Unit"] + [col for col in numeric_cols]]

            # Identify numeric columns (exclude 'Unit')
            numeric_cols = df.columns.difference(["Unit"])

            # Convert to numeric and round
            logger.info("Converting to numeric and rounding values")
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").round(2)
            
            logger.info(f"Unit standardization completed. Final shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error standardizing units: {e}", exc_info=True)
            raise

    def convert_df_to_html(self, df: pd.DataFrame) -> str:
        """Convert the dataframe to an html table."""
        logger.info("Converting DataFrame to HTML format")
        try:
            html_table = df.to_html(index=False)
            logger.info(f"Successfully converted DataFrame to HTML. Length: {len(html_table)} characters")
            return html_table
        except Exception as e:
            logger.error(f"Error converting DataFrame to HTML: {e}", exc_info=True)
            raise
    
    def from_stock_to_dataframe(self, stock: str) -> str:
        """Complete pipeline from stock symbol to HTML financial data."""
        logger.info(f"Starting complete financial data pipeline for {stock}")
        
        try:
            logger.info(f"Step 1: Retrieving raw financial data for {stock}")
            df = self.get_values(stock)
            
            logger.info(f"Step 2: Standardizing units for {stock}")
            df = self.standardize_units(df)
            
            logger.info(f"Step 3: Converting to HTML for {stock}")
            df = self.convert_df_to_html(df)
            
            logger.info(f"Successfully completed financial data pipeline for {stock}")
            return df
            
        except Exception as e:
            logger.error(f"Error in financial data pipeline for {stock}: {e}", exc_info=True)
            raise






        
    




