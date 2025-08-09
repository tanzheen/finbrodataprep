"""
Tests for the AlphavantageFinancialDataGatherer class.

This module contains comprehensive tests for the Alpha Vantage API integration,
with a specific focus on the get_fundamental_table method.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from fundamentals.alphavantage import AlphavantageFinancialDataGatherer


class TestAlphavantageFinancialDataGatherer:
    """Test the AlphavantageFinancialDataGatherer class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        with patch('fundamentals.alphavantage.env') as mock_env:
            mock_env.get_value.return_value = "test_api_key"
            self.gatherer = AlphavantageFinancialDataGatherer()
    
    def test_init(self):
        """Test that the class initializes correctly."""
        assert self.gatherer.api_key == "test_api_key"
        assert self.gatherer.base_url == "https://www.alphavantage.co/query"
    
    @patch('fundamentals.alphavantage.requests.get')
    def test_call_api_success(self, mock_get):
        """Test successful API call."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'quarterlyEarnings': [
                {
                    'fiscalDateEnding': '2024-01-01',
                    'reportedEPS': '1.50',
                    'estimatedEPS': '1.45',
                    'surprise': '0.05',
                    'surprisePercentage': '3.45'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test the call
        result = self.gatherer.call_api("AAPL", "EARNINGS")
        
        # Verify the call
        mock_get.assert_called_once()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['fiscalDateEnding'] == '2024-01-01'
    
    @patch('fundamentals.alphavantage.requests.get')
    def test_call_api_failure(self, mock_get):
        """Test API call failure."""
        mock_get.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            self.gatherer.call_api("AAPL", "EARNINGS")
    
    def test_filter_timeframe_year(self):
        """Test filtering by year timeframe."""
        # Create test data
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='Q')
        df = pd.DataFrame({
            'fiscalDateEnding': dates,
            'reportedEPS': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7]
        })
        
        result = self.gatherer.filter_timeframe(df, "year")
        
        # Should filter to last 365 days
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=365)
        expected_count = len(df[df['fiscalDateEnding'] > cutoff_date])
        assert len(result) == expected_count
    
    def test_filter_timeframe_month(self):
        """Test filtering by month timeframe."""
        # Create test data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
        df = pd.DataFrame({
            'fiscalDateEnding': dates,
            'reportedEPS': [1.0] * len(dates)
        })
        
        result = self.gatherer.filter_timeframe(df, "month")
        
        # Should filter to last 30 days
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=30)
        expected_count = len(df[df['fiscalDateEnding'] > cutoff_date])
        assert len(result) == expected_count
    
    def test_filter_latest(self):
        """Test getting the latest 4 quarters of data."""
        # Create test data with more than 4 quarters
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='Q')
        df = pd.DataFrame({
            'fiscalDateEnding': dates,
            'reportedEPS': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7]
        })
        
        result = self.gatherer.filter_latest(df)
        
        # Should return exactly 4 rows
        assert len(result) == 4
        # Should be sorted in descending order (latest first)
        assert result.iloc[0]['fiscalDateEnding'] > result.iloc[1]['fiscalDateEnding']
    
    @patch.object(AlphavantageFinancialDataGatherer, 'call_api')
    def test_get_earnings(self, mock_call_api):
        """Test getting earnings data."""
        # Mock API response
        mock_data = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2023-10-01', '2023-07-01'],
            'reportedEPS': ['1.50', 'None', '1.30'],
            'estimatedEPS': ['1.45', '1.40', '1.25'],
            'surprise': ['0.05', '0.10', '0.05'],
            'surprisePercentage': ['3.45', '7.14', '4.00'],
            'other_column': ['value1', 'value2', 'value3']  # Should be filtered out
        })
        mock_call_api.return_value = mock_data
        
        result = self.gatherer.get_earnings("AAPL")
        
        # Verify API was called correctly
        mock_call_api.assert_called_once_with("AAPL", "EARNINGS")
        
        # Verify filtering and column selection
        assert len(result) == 2  # One row with 'None' should be filtered out
        expected_columns = ['fiscalDateEnding', 'reportedEPS', 'estimatedEPS', 'surprise', 'surprisePercentage']
        assert list(result.columns) == expected_columns
    
    @patch.object(AlphavantageFinancialDataGatherer, 'call_api')
    def test_get_income_statement(self, mock_call_api):
        """Test getting income statement data."""
        # Mock API response
        mock_data = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2023-10-01'],
            'netIncome': ['1000000', '900000']
        })
        mock_call_api.return_value = mock_data
        
        result = self.gatherer.get_income_statement("AAPL")
        
        # Verify API was called correctly
        mock_call_api.assert_called_once_with("AAPL", "INCOME_STATEMENT")
        
        # Verify column selection
        expected_columns = ['fiscalDateEnding', 'netIncome']
        assert list(result.columns) == expected_columns
    
    @patch.object(AlphavantageFinancialDataGatherer, 'call_api')
    def test_get_balance_sheet(self, mock_call_api):
        """Test getting balance sheet data."""
        # Mock API response
        mock_data = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2023-10-01'],
            'totalAssets': ['10000000', '9500000'],
            'totalShareholderEquity': ['5000000', '4800000'],
            'commonStockSharesOutstanding': ['1000000', '1000000'],
            'totalLiabilities': ['5000000', '4700000'],
            'totalCurrentAssets': ['3000000', '2900000'],
            'totalCurrentLiabilities': ['2000000', '1900000'],
            'inventory': ['500000', '480000'],
            'other_column': ['value1', 'value2']  # Should be filtered out
        })
        mock_call_api.return_value = mock_data
        
        result = self.gatherer.get_balance_sheet("AAPL")
        
        # Verify API was called correctly
        mock_call_api.assert_called_once_with("AAPL", "BALANCE_SHEET")
        
        # Verify column selection
        expected_columns = ['fiscalDateEnding', 'totalAssets', 'totalShareholderEquity', 
                          'commonStockSharesOutstanding', 'totalLiabilities', 'totalCurrentAssets', 
                          'totalCurrentLiabilities', 'inventory']
        assert list(result.columns) == expected_columns
    
    @patch.object(AlphavantageFinancialDataGatherer, 'call_api')
    def test_get_cash_flow(self, mock_call_api):
        """Test getting cash flow data."""
        # Mock API response
        mock_data = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2023-10-01'],
            'operatingCashflow': ['800000', '750000'],
            'capitalExpenditures': ['-200000', '-180000'],
            'other_column': ['value1', 'value2']  # Should be filtered out
        })
        mock_call_api.return_value = mock_data
        
        result = self.gatherer.get_cash_flow("AAPL")
        
        # Verify API was called correctly
        mock_call_api.assert_called_once_with("AAPL", "CASH_FLOW")
        
        # Verify column selection
        expected_columns = ['fiscalDateEnding', 'operatingCashflow', 'capitalExpenditures']
        assert list(result.columns) == expected_columns
    
    @patch.object(AlphavantageFinancialDataGatherer, 'get_earnings')
    @patch.object(AlphavantageFinancialDataGatherer, 'get_income_statement')
    @patch.object(AlphavantageFinancialDataGatherer, 'get_balance_sheet')
    @patch.object(AlphavantageFinancialDataGatherer, 'get_cash_flow')
    def test_get_financial_data(self, mock_cash_flow, mock_balance_sheet, 
                               mock_income_statement, mock_earnings):
        """Test merging all financial data."""
        # Mock individual dataframes
        earnings_df = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2023-10-01'],
            'reportedEPS': [1.50, 1.30],
            'estimatedEPS': [1.45, 1.25],
            'surprise': [0.05, 0.05],
            'surprisePercentage': [3.45, 4.00]
        })
        
        income_df = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2023-10-01'],
            'netIncome': [1000000, 900000]
            # Removed non-numeric columns to avoid conversion issues
        })
        
        balance_df = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2023-10-01'],
            'totalAssets': [10000000, 9500000],
            'totalShareholderEquity': [5000000, 4800000],
            'commonStockSharesOutstanding': [1000000, 1000000],
            'totalLiabilities': [5000000, 4700000],
            'totalCurrentAssets': [3000000, 2900000],
            'totalCurrentLiabilities': [2000000, 1900000],
            'inventory': [500000, 480000]
        })
        
        cash_flow_df = pd.DataFrame({
            'fiscalDateEnding': ['2024-01-01', '2023-10-01'],
            'operatingCashflow': [800000, 750000],
            'capitalExpenditures': [-200000, -180000]
        })
        
        mock_earnings.return_value = earnings_df
        mock_income_statement.return_value = income_df
        mock_balance_sheet.return_value = balance_df
        mock_cash_flow.return_value = cash_flow_df
        
        result = self.gatherer.get_financial_data("AAPL")
        
        # Verify all methods were called
        mock_earnings.assert_called_once_with("AAPL")
        mock_income_statement.assert_called_once_with("AAPL")
        mock_balance_sheet.assert_called_once_with("AAPL")
        mock_cash_flow.assert_called_once_with("AAPL")
        
        # Verify merged result
        assert len(result) == 2
        assert 'fiscalDateEnding' in result.columns
        assert 'reportedEPS' in result.columns
        assert 'netIncome' in result.columns
        assert 'totalAssets' in result.columns
        assert 'operatingCashflow' in result.columns
        
        # Verify numeric conversion for numeric columns
        assert result['reportedEPS'].dtype in ['float64', 'int64']
        assert result['netIncome'].dtype in ['float64', 'int64']
        # Note: reportedCurrency and empty string column will remain as object dtype
    
    def test_calculate_changes(self):
        """Test calculating percentage changes."""
        # Create test data
        df = pd.DataFrame({
            'fiscalDateEnding': ['2023-01-01', '2023-04-01', '2023-07-01', '2023-10-01'],
            'reportedEPS': [1.00, 1.10, 1.20, 1.30],
            'netIncome': [1000000, 1100000, 1200000, 1300000]
        })
        
        result = self.gatherer.calculate_changes(df)
        
        # Verify sorting (ascending by date)
        assert result.iloc[0]['fiscalDateEnding'] < result.iloc[1]['fiscalDateEnding']
        
        # Verify percentage changes
        assert 'EPS_pct_change' in result.columns
        assert 'netIncome_pct_change' in result.columns
        
        # First row should have NaN for percentage changes (no previous value)
        assert pd.isna(result.iloc[0]['EPS_pct_change'])
        assert pd.isna(result.iloc[0]['netIncome_pct_change'])
        
        # Second row should have calculated percentage changes
        expected_eps_change = ((1.10 - 1.00) / 1.00) * 100
        expected_income_change = ((1100000 - 1000000) / 1000000) * 100
        assert abs(result.iloc[1]['EPS_pct_change'] - expected_eps_change) < 0.01
        assert abs(result.iloc[1]['netIncome_pct_change'] - expected_income_change) < 0.01
    
    def test_calculate_ratios(self):
        """Test calculating financial ratios."""
        # Create test data
        df = pd.DataFrame({
            'totalShareholderEquity': [5000000, 4800000],
            'commonStockSharesOutstanding': [1000000, 1000000],
            'netIncome': [1000000, 900000],
            'totalLiabilities': [5000000, 4700000],
            'totalCurrentAssets': [3000000, 2900000],
            'totalCurrentLiabilities': [2000000, 1900000],
            'inventory': [500000, 480000],
            'totalAssets': [10000000, 9500000]
        })
        
        result = self.gatherer.calculate_ratios(df)
        
        # Verify all ratios are calculated
        expected_ratios = ['bookValuePerShare', 'returnOnEquity', 'debtToEquityRatio', 
                          'currentRatio', 'quickRatio', 'leverageRatio']
        
        for ratio in expected_ratios:
            assert ratio in result.columns
        
        # Verify calculations for first row
        expected_book_value = 5000000 / 1000000  # 5.0
        expected_roe = 1000000 / 5000000  # 0.2
        expected_debt_equity = 5000000 / 5000000  # 1.0
        expected_current = 3000000 / 2000000  # 1.5
        expected_quick = (3000000 - 500000) / 2000000  # 1.25
        expected_leverage = 5000000 / 10000000  # 0.5
        
        assert abs(result.iloc[0]['bookValuePerShare'] - expected_book_value) < 0.01
        assert abs(result.iloc[0]['returnOnEquity'] - expected_roe) < 0.01
        assert abs(result.iloc[0]['debtToEquityRatio'] - expected_debt_equity) < 0.01
        assert abs(result.iloc[0]['currentRatio'] - expected_current) < 0.01
        assert abs(result.iloc[0]['quickRatio'] - expected_quick) < 0.01
        assert abs(result.iloc[0]['leverageRatio'] - expected_leverage) < 0.01
    
    @patch.object(AlphavantageFinancialDataGatherer, 'get_financial_data')
    @patch.object(AlphavantageFinancialDataGatherer, 'calculate_changes')
    @patch.object(AlphavantageFinancialDataGatherer, 'calculate_ratios')
    @patch.object(AlphavantageFinancialDataGatherer, 'filter_latest')
    def test_from_stock_to_dataframe_success(self, mock_filter_latest, mock_calculate_ratios, 
                                          mock_calculate_changes, mock_get_financial_data):
        """Test successful execution of from_stock_to_dataframe."""
        # Mock the financial data
        mock_financial_data = pd.DataFrame({
            'fiscalDateEnding': ['2023-01-01', '2023-04-01', '2023-07-01', '2023-10-01'],
            'reportedEPS': [1.00, 1.10, 1.20, 1.30],
            'netIncome': [1000000, 1100000, 1200000, 1300000],
            'totalShareholderEquity': [5000000, 4800000, 4600000, 4400000],
            'commonStockSharesOutstanding': [1000000, 1000000, 1000000, 1000000],
            'totalLiabilities': [5000000, 4700000, 4500000, 4300000],
            'totalCurrentAssets': [3000000, 2900000, 2800000, 2700000],
            'totalCurrentLiabilities': [2000000, 1900000, 1800000, 1700000],
            'inventory': [500000, 480000, 460000, 440000],
            'totalAssets': [10000000, 9500000, 9000000, 8500000],
            'operatingCashflow': [800000, 750000, 700000, 650000]
        })
        
        # Mock the processed data with changes and ratios
        mock_processed_data = mock_financial_data.copy()
        mock_processed_data['EPS_pct_change'] = [np.nan, 10.0, 9.09, 8.33]
        mock_processed_data['netIncome_pct_change'] = [np.nan, 10.0, 9.09, 8.33]
        mock_processed_data['bookValuePerShare'] = [5.0, 4.8, 4.6, 4.4]
        mock_processed_data['returnOnEquity'] = [0.2, 0.229, 0.261, 0.295]
        mock_processed_data['debtToEquityRatio'] = [1.0, 0.979, 0.978, 0.977]
        mock_processed_data['currentRatio'] = [1.5, 1.526, 1.556, 1.588]
        mock_processed_data['quickRatio'] = [1.25, 1.273, 1.3, 1.329]
        mock_processed_data['leverageRatio'] = [0.5, 0.495, 0.5, 0.506]
        
        mock_get_financial_data.return_value = mock_financial_data
        mock_calculate_changes.return_value = mock_processed_data
        mock_calculate_ratios.return_value = mock_processed_data
        mock_filter_latest.return_value = mock_processed_data
        
        # Test the method
        result = self.gatherer.from_stock_to_dataframe("AAPL")
        
        # Verify all methods were called in the correct order
        mock_get_financial_data.assert_called_once_with("AAPL")
        mock_calculate_changes.assert_called_once_with(mock_financial_data)
        mock_calculate_ratios.assert_called_once_with(mock_processed_data)
        mock_filter_latest.assert_called_once_with(mock_processed_data)
        
        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        
        # Verify all expected columns are present
        expected_columns = [
            'fiscalDateEnding', 'reportedEPS', 'netIncome', 'totalShareholderEquity',
            'commonStockSharesOutstanding', 'totalLiabilities', 'totalCurrentAssets',
            'totalCurrentLiabilities', 'inventory', 'totalAssets', 'operatingCashflow', 'EPS_pct_change', 'netIncome_pct_change',
            'bookValuePerShare', 'returnOnEquity', 'debtToEquityRatio', 'currentRatio',
            'quickRatio', 'leverageRatio'
        ]
        
        for col in expected_columns:
            assert col in result.columns
    
    @patch.object(AlphavantageFinancialDataGatherer, 'get_financial_data')
    def test_from_stock_to_dataframe_api_failure(self, mock_get_financial_data):
        """Test from_stock_to_dataframe when API call fails."""
        # Mock API failure
        mock_get_financial_data.side_effect = Exception("API Error")
        
        # Test that the exception is propagated
        with pytest.raises(Exception, match="API Error"):
            self.gatherer.from_stock_to_dataframe("AAPL")
    
    @patch.object(AlphavantageFinancialDataGatherer, 'get_financial_data')
    @patch.object(AlphavantageFinancialDataGatherer, 'calculate_changes')
    @patch.object(AlphavantageFinancialDataGatherer, 'calculate_ratios')
    @patch.object(AlphavantageFinancialDataGatherer, 'filter_latest')
    def test_from_stock_to_dataframe_empty_data(self, mock_filter_latest, mock_calculate_ratios, 
                                               mock_calculate_changes, mock_get_financial_data):
        """Test from_stock_to_dataframe with empty financial data."""
        # Mock empty dataframe
        mock_get_financial_data.return_value = pd.DataFrame()
        mock_calculate_changes.return_value = pd.DataFrame()
        mock_calculate_ratios.return_value = pd.DataFrame()
        mock_filter_latest.return_value = pd.DataFrame()
        
        result = self.gatherer.from_stock_to_dataframe("AAPL")
        
        # Should return empty dataframe
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    def test_initialise_units_not_implemented(self):
        """Test that initialise_units raises NotImplementedError."""
        df = pd.DataFrame({'test': [1, 2, 3]})
        
        with pytest.raises(NotImplementedError):
            self.gatherer.initialise_units(df)

    def test_real_ticker(self): 
        df = self.gatherer.from_stock_to_dataframe('LLY')
        print(df.columns)
        df.to_csv('test_alphavantage.csv')


if __name__ == "__main__":
    pytest.main([__file__]) 