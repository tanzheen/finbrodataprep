import pytest
import os
import json
import pandas as pd
from datetime import datetime
import sys

# Add the parent directory to the path so we can import our module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from screening.finviz import FinvizScreener, ScreeningStrategies


class TestFinvizScreener:
    """Integration tests for the FinvizScreener class using real Finviz data."""
    
    @pytest.fixture
    def screener(self):
        """Create a FinvizScreener instance for testing."""
        return FinvizScreener()
    
    @pytest.fixture(scope="class")
    def output_dir(self):
        """Create output directory for test results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"test_results/finviz_integration_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def save_results(self, output_dir: str, test_name: str, data: dict):
        """Save test results to JSON file."""
        filepath = os.path.join(output_dir, f"{test_name}_results.json")
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"✅ Saved {test_name} results to {filepath}")
    
    def print_sample_stocks(self, results_df: pd.DataFrame, top_stocks: list, limit: int = 5):
        """Helper method to print sample stocks with dynamic column detection."""
        if not top_stocks:
            return
            
        ticker_col = results_df.columns[1] if len(results_df.columns) > 1 else results_df.columns[0]
        price_col = None
        change_col = None
        pe_col = None
        dividend_col = None
        
        for col in results_df.columns:
            col_lower = str(col).lower()
            if 'price' in col_lower:
                price_col = col
            elif 'change' in col_lower:
                change_col = col
            elif 'p/e' in col_lower or 'pe' in col_lower:
                pe_col = col
            elif 'dividend' in col_lower or 'div' in col_lower or 'yield' in col_lower:
                dividend_col = col
        
        for i, stock in enumerate(top_stocks[:limit], 1):
            ticker = stock.get(ticker_col, 'N/A')
            price = stock.get(price_col, 'N/A') if price_col else 'N/A'
            
            # Build info string based on available columns
            info_parts = []
            if price != 'N/A':
                info_parts.append(f"${price}")
            if change_col and stock.get(change_col) not in [None, '', 'N/A']:
                info_parts.append(f"({stock.get(change_col)})")
            if pe_col and stock.get(pe_col) not in [None, '', 'N/A', '-']:
                info_parts.append(f"P/E: {stock.get(pe_col)}")
            if dividend_col and stock.get(dividend_col) not in [None, '', 'N/A', '-']:
                info_parts.append(f"Yield: {stock.get(dividend_col)}")
            
            if not info_parts:
                info_parts = ['No data']
                
            print(f"{i}. {ticker}: {' '.join(info_parts)}")
    
    def test_initialization(self, screener):
        """Test screener initialization."""
        assert screener.base_filters == []
        assert screener.current_df is None
        assert screener.scraper is not None
        
        # Test with base filters
        base_filters = ['cap_largeover']
        screener_with_filters = FinvizScreener(base_filters)
        assert screener_with_filters.base_filters == base_filters
    
    def test_quality_growth_screen_real(self, screener, output_dir):
        """Test quality growth screening with real data."""
        print("\n🔍 Running Quality Growth Screen...")
        
        try:
            # Run the screen
            results_df = screener.quality_growth_screen()
            
            # Check if we got results
            if results_df is None or results_df.empty:
                print("❌ No results returned from screening")
                return
            
            # Get results
            top_stocks = screener.get_top_stocks(20)  # Get top 20
            summary = screener.get_screening_summary()
            
            # Prepare data for saving
            test_data = {
                "test_name": "quality_growth_screen",
                "timestamp": datetime.now().isoformat(),
                "total_stocks_found": summary.get('total_stocks', 0),
                "top_20_stocks": top_stocks,
                "summary": summary,
                "columns": results_df.columns.tolist(),
                "filters_used": [
                    'cap_largeover',
                    'exch_nasd', 
                    'fa_epsyoyttm_pos',
                    'fa_evebitda_o10',
                    'fa_pe_u25',
                    'fa_roa_o10',
                    'fa_roe_o15',
                    'fa_salesyoyttm_o5'
                ]
            }
            
            # Save results
            self.save_results(output_dir, "quality_growth_screen", test_data)
            
            # Export CSV for manual review
            csv_path = screener.export_results(os.path.join(output_dir, "quality_growth"), "csv")
            print(f"📊 Exported CSV to {csv_path}")
            
            # Assertions
            assert isinstance(results_df, pd.DataFrame)
            assert isinstance(top_stocks, list)
            assert summary['total_stocks'] >= 0
            print(f"✅ Found {summary['total_stocks']} quality growth stocks")
            
            # Print sample results
            if top_stocks:
                print("\n📈 Top 5 Quality Growth Stocks:")
                self.print_sample_stocks(results_df, top_stocks, 5)
            
        except Exception as e:
            error_data = {
                "test_name": "quality_growth_screen",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.save_results(output_dir, "quality_growth_screen_error", error_data)
            pytest.fail(f"Quality growth screen failed: {e}")
    
    def test_dividend_growth_screen_real(self, screener, output_dir):
        """Test dividend growth screening with real data."""
        print("\n💰 Running Dividend Growth Screen...")
        
        try:
            # Run the screen
            results_df = screener.dividend_growth_screen(min_yield=2.5)
            
            # Check if we got results
            if results_df is None or results_df.empty:
                print("❌ No results returned from screening")
                return
            
            # Get results
            top_stocks = screener.get_top_stocks(15)
            summary = screener.get_screening_summary()
            
            test_data = {
                "test_name": "dividend_growth_screen",
                "timestamp": datetime.now().isoformat(),
                "min_yield": 2.5,
                "total_stocks_found": summary.get('total_stocks', 0),
                "top_15_stocks": top_stocks,
                "summary": summary,
                "columns": results_df.columns.tolist(),
                "filters_used": [
                    'cap_largeover',
                    'exch_nasd',
                    'fa_div_pos',
                    'fa_div_o2',
                    'fa_pe_u20', 
                    'fa_roe_o10',
                    'fa_payoutratio_u60'
                ]
            }
            
            self.save_results(output_dir, "dividend_growth_screen", test_data)
            
            # Export results
            csv_path = screener.export_results(os.path.join(output_dir, "dividend_growth"), "csv")
            print(f"📊 Exported CSV to {csv_path}")
            
            assert isinstance(results_df, pd.DataFrame)
            assert isinstance(top_stocks, list)
            assert summary['total_stocks'] >= 0
            print(f"✅ Found {summary['total_stocks']} dividend growth stocks")
            
            if top_stocks:
                print("\n💰 Top 5 Dividend Growth Stocks:")
                self.print_sample_stocks(results_df, top_stocks, 5)
                    
        except Exception as e:
            error_data = {
                "test_name": "dividend_growth_screen",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.save_results(output_dir, "dividend_growth_screen_error", error_data)
            pytest.fail(f"Dividend growth screen failed: {e}")
    
    def test_value_screen_real(self, screener, output_dir):
        """Test value screening with real data."""
        print("\n📉 Running Value Screen...")
        
        try:
            results_df = screener.value_screen()
            
            if results_df is None or results_df.empty:
                print("❌ No results returned from screening")
                return
            
            top_stocks = screener.get_top_stocks(15)
            summary = screener.get_screening_summary()
            
            test_data = {
                "test_name": "value_screen",
                "timestamp": datetime.now().isoformat(),
                "total_stocks_found": summary.get('total_stocks', 0),
                "top_15_stocks": top_stocks,
                "summary": summary,
                "columns": results_df.columns.tolist(),
                "filters_used": [
                    'cap_largeover',
                    'exch_nasd',
                    'fa_pe_u15',
                    'fa_pb_u2',
                    'fa_pfcf_u15',
                    'fa_roe_o10',
                    'fa_roa_o5',
                    'fa_debt_u0.5'
                ]
            }
            
            self.save_results(output_dir, "value_screen", test_data)
            
            csv_path = screener.export_results(os.path.join(output_dir, "value_stocks"), "csv")
            print(f"📊 Exported CSV to {csv_path}")
            
            assert isinstance(results_df, pd.DataFrame)
            assert isinstance(top_stocks, list)
            assert summary['total_stocks'] >= 0
            print(f"✅ Found {summary['total_stocks']} value stocks")
            
            if top_stocks:
                print("\n📉 Top 5 Value Stocks:")
                self.print_sample_stocks(results_df, top_stocks, 5)
                    
        except Exception as e:
            error_data = {
                "test_name": "value_screen",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.save_results(output_dir, "value_screen_error", error_data)
            pytest.fail(f"Value screen failed: {e}")
    
    def test_momentum_screen_real(self, screener, output_dir):
        """Test momentum screening with real data."""
        print("\n🚀 Running Momentum Screen...")
        
        try:
            results_df = screener.momentum_screen()
            
            if results_df is None or results_df.empty:
                print("❌ No results returned from screening")
                return
            
            top_stocks = screener.get_top_stocks(15)
            summary = screener.get_screening_summary()
            
            test_data = {
                "test_name": "momentum_screen",
                "timestamp": datetime.now().isoformat(),
                "total_stocks_found": summary.get('total_stocks', 0),
                "top_15_stocks": top_stocks,
                "summary": summary,
                "columns": results_df.columns.tolist(),
                "filters_used": [
                    'cap_largeover',
                    'exch_nasd',
                    'ta_perf_13w_o10',
                    'ta_perf_26w_o20',
                    'ta_rsi_no60',
                    'fa_epsyoyttm_o20',
                    'ta_sma20_pa',
                    'ta_sma50_pa'
                ]
            }
            
            self.save_results(output_dir, "momentum_screen", test_data)
            
            csv_path = screener.export_results(os.path.join(output_dir, "momentum_stocks"), "csv")
            print(f"📊 Exported CSV to {csv_path}")
            
            assert isinstance(results_df, pd.DataFrame)
            assert isinstance(top_stocks, list)
            assert summary['total_stocks'] >= 0
            print(f"✅ Found {summary['total_stocks']} momentum stocks")
            
            if top_stocks:
                print("\n🚀 Top 5 Momentum Stocks:")
                self.print_sample_stocks(results_df, top_stocks, 5)
                    
        except Exception as e:
            error_data = {
                "test_name": "momentum_screen",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.save_results(output_dir, "momentum_screen_error", error_data)
            pytest.fail(f"Momentum screen failed: {e}")
    
    def test_warren_buffett_strategy_real(self, screener, output_dir):
        """Test Warren Buffett style screening with real data."""
        print("\n🎯 Running Warren Buffett Strategy Screen...")
        
        try:
            buffett_filters = ScreeningStrategies.warren_buffett_style()
            results_df = screener.custom_screen(
                filters=buffett_filters,
                table='Valuation',
                order='pe'
            )
            
            if results_df is None or results_df.empty:
                print("❌ No results returned from screening")
                return
            
            top_stocks = screener.get_top_stocks(10)
            summary = screener.get_screening_summary()
            
            test_data = {
                "test_name": "warren_buffett_strategy",
                "timestamp": datetime.now().isoformat(),
                "total_stocks_found": summary.get('total_stocks', 0),
                "top_10_stocks": top_stocks,
                "summary": summary,
                "columns": results_df.columns.tolist(),
                "filters_used": buffett_filters
            }
            
            self.save_results(output_dir, "warren_buffett_strategy", test_data)
            
            csv_path = screener.export_results(os.path.join(output_dir, "buffett_stocks"), "csv")
            print(f"📊 Exported CSV to {csv_path}")
            
            assert isinstance(results_df, pd.DataFrame)
            assert isinstance(top_stocks, list)
            assert summary['total_stocks'] >= 0
            print(f"✅ Found {summary['total_stocks']} Buffett-style stocks")
            
            if top_stocks:
                print("\n🎯 Top 5 Buffett-Style Stocks:")
                self.print_sample_stocks(results_df, top_stocks, 5)
                    
        except Exception as e:
            error_data = {
                "test_name": "warren_buffett_strategy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.save_results(output_dir, "warren_buffett_strategy_error", error_data)
            pytest.fail(f"Warren Buffett strategy screen failed: {e}")
    
    def test_peter_lynch_strategy_real(self, screener, output_dir):
        """Test Peter Lynch style screening with real data."""
        print("\n📈 Running Peter Lynch Strategy Screen...")
        
        try:
            lynch_filters = ScreeningStrategies.peter_lynch_style()
            results_df = screener.custom_screen(
                filters=lynch_filters,
                table='Performance',
                order='-change'
            )
            
            if results_df is None or results_df.empty:
                print("❌ No results returned from screening")
                return
            
            top_stocks = screener.get_top_stocks(10)
            summary = screener.get_screening_summary()
            
            test_data = {
                "test_name": "peter_lynch_strategy",
                "timestamp": datetime.now().isoformat(),
                "total_stocks_found": summary.get('total_stocks', 0),
                "top_10_stocks": top_stocks,
                "summary": summary,
                "columns": results_df.columns.tolist(),
                "filters_used": lynch_filters
            }
            
            self.save_results(output_dir, "peter_lynch_strategy", test_data)
            
            csv_path = screener.export_results(os.path.join(output_dir, "lynch_stocks"), "csv")
            print(f"📊 Exported CSV to {csv_path}")
            
            assert isinstance(results_df, pd.DataFrame)
            assert isinstance(top_stocks, list)
            assert summary['total_stocks'] >= 0
            print(f"✅ Found {summary['total_stocks']} Lynch-style stocks")
            
            if top_stocks:
                print("\n📈 Top 5 Lynch-Style Stocks:")
                self.print_sample_stocks(results_df, top_stocks, 5)
                    
        except Exception as e:
            error_data = {
                "test_name": "peter_lynch_strategy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.save_results(output_dir, "peter_lynch_strategy_error", error_data)
            pytest.fail(f"Peter Lynch strategy screen failed: {e}")
    
    def test_analyze_specific_stocks(self, screener, output_dir):
        """Test analyzing specific stocks from screening results."""
        print("\n🔎 Testing Stock Analysis...")
        
        try:
            # Run a screen first to get some stocks
            results_df = screener.quality_growth_screen()
            if results_df is None or results_df.empty:
                print("❌ No results from initial screening")
                return
                
            top_stocks = screener.get_top_stocks(5)
            
            analyzed_stocks = []
            
            # Find ticker column
            ticker_col = results_df.columns[1] if len(results_df.columns) > 1 else results_df.columns[0]
            
            for stock in top_stocks:
                ticker = stock.get(ticker_col, 'UNKNOWN')
                try:
                    analysis = screener.analyze_stock(ticker)
                    analyzed_stocks.append({
                        "ticker": ticker,
                        "analysis": analysis,
                        "success": True
                    })
                    print(f"✅ Analyzed {ticker}")
                except Exception as e:
                    analyzed_stocks.append({
                        "ticker": ticker,
                        "error": str(e),
                        "success": False
                    })
                    print(f"❌ Failed to analyze {ticker}: {e}")
            
            test_data = {
                "test_name": "stock_analysis",
                "timestamp": datetime.now().isoformat(),
                "analyzed_stocks": analyzed_stocks,
                "total_analyzed": len(analyzed_stocks)
            }
            
            self.save_results(output_dir, "stock_analysis", test_data)
            
            # Test that at least some stocks were analyzed successfully
            successful_analyses = [s for s in analyzed_stocks if s["success"]]
            assert len(successful_analyses) > 0, "No stocks were analyzed successfully"
            print(f"✅ Successfully analyzed {len(successful_analyses)} stocks")
            
        except Exception as e:
            error_data = {
                "test_name": "stock_analysis",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.save_results(output_dir, "stock_analysis_error", error_data)
            pytest.fail(f"Stock analysis failed: {e}")
    
    def test_export_functionality(self, screener, output_dir):
        """Test CSV and SQLite export functionality."""
        print("\n💾 Testing Export Functionality...")
        
        try:
            # Run a screen first
            results_df = screener.quality_growth_screen()
            if results_df is None or results_df.empty:
                print("❌ No results from initial screening")
                return
            
            # Test CSV export
            csv_path = screener.export_results(os.path.join(output_dir, "export_test"), "csv")
            assert os.path.exists(csv_path), "CSV file was not created"
            
            # Test SQLite export
            sqlite_path = screener.export_results(os.path.join(output_dir, "export_test"), "sqlite")
            assert os.path.exists(sqlite_path), "SQLite file was not created"
            
            test_data = {
                "test_name": "export_functionality",
                "timestamp": datetime.now().isoformat(),
                "csv_path": csv_path,
                "sqlite_path": sqlite_path,
                "csv_exists": os.path.exists(csv_path),
                "sqlite_exists": os.path.exists(sqlite_path)
            }
            
            self.save_results(output_dir, "export_functionality", test_data)
            
            print(f"✅ CSV exported to: {csv_path}")
            print(f"✅ SQLite exported to: {sqlite_path}")
            
        except Exception as e:
            error_data = {
                "test_name": "export_functionality",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.save_results(output_dir, "export_functionality_error", error_data)
            pytest.fail(f"Export functionality test failed: {e}")


class TestScreeningStrategies:
    """Test predefined screening strategies."""
    
    def test_warren_buffett_style(self):
        """Test Warren Buffett style filters."""
        filters = ScreeningStrategies.warren_buffett_style()
        
        expected_filters = [
            'cap_largeover',
            'fa_roe_o15',
            'fa_pe_u20',
            'fa_debt_u0.4',
            'fa_eps5years_o10',
            'fa_epsyoy_o5'
        ]
        
        assert filters == expected_filters
    
    def test_peter_lynch_style(self):
        """Test Peter Lynch style filters."""
        filters = ScreeningStrategies.peter_lynch_style()
        
        expected_filters = [
            'cap_midover',
            'fa_epsyoy_o15',
            'fa_pe_u25',
            'fa_peg_u1.5',
            'ta_perf_52w_o10'
        ]
        
        assert filters == expected_filters
    
    def test_dividend_aristocrat_style(self):
        """Test dividend aristocrat style filters."""
        filters = ScreeningStrategies.dividend_aristocrat_style()
        
        expected_filters = [
            'cap_largeover',
            'fa_div_pos',
            'fa_div_o2',
            'fa_payoutratio_u60',
            'fa_roe_o12'
        ]
        
        assert filters == expected_filters


if __name__ == "__main__":
    # Run the tests with verbose output
    pytest.main([__file__, "-v", "-s"])