"""
Financial Data Gathering Module

This module provides a comprehensive class for gathering financial data about companies
using the finagg library. It collects various financial metrics including earnings,
balance sheet items, and financial ratios.
"""

import pandas as pd
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

from financetoolkit import Toolkit
from utils.config import env
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
        
    def get_values(self, stock:str):
        """Get the values of the financial data."""
        toolkit = Toolkit([stock], quarterly=True, api_key=env.FINANCIAL_API_KEY)  # You can also use ["AAPL", "MSFT", "GOOGL"]
        eps = toolkit.ratios.get_earnings_per_share()
        eps.index = ['Earnings Per Share']
        income_statement = toolkit.get_income_statement()
        income_statement= income_statement.loc[['Net Income']]
        cash_state= toolkit.get_cash_flow_statement()
        cash_state= cash_state.loc[['Operating Cash Flow', 'Free Cash Flow']]
        bal_sheet = toolkit.get_balance_sheet_statement()
        # Total Current Assets, Total Current Liabilities, Total Shareholder Equity
        rows_to_find = ['Total Current Assets', 'Total Current Liabilities', 'Total Shareholder Equity']
        bal_sheet= bal_sheet.loc[rows_to_find]
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
        all_data = pd.concat([eps, income_statement, cash_state, bal_sheet, roe, roa, bvps, debt_service_coverage, cash_flow_ratio, debt_to_equity, current_ratio], axis=0)
        return all_data
    
    def standardize_units(self, df: pd.DataFrame) -> pd.DataFrame:


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
        eps_change = df.loc["Earnings Per Share", numeric_cols].pct_change(axis=0) * 100
        net_income_change = df.loc["Net Income", numeric_cols].pct_change(axis=0) * 100


        # 4. Apply scaling based on units
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
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").round(2)
        return df


    def convert_df_to_html(self, df: pd.DataFrame) -> str:
        """Convert the dataframe to an html table."""
        return df.to_html(index=False)
    
    def from_stock_to_dataframe(self, stock: str) -> pd.DataFrame:
        df = self.get_values(stock)
        df = self.standardize_units(df)
        df = self.convert_df_to_html(df)
        return df






        
    




