"""
Tests for main.py Click commands

This module contains comprehensive tests for the stock analysis pipeline CLI commands.
"""

import pytest
import click
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from contextlib import contextmanager
from typing import List, Tuple

# Import the CLI functions
from main import cli, analyze, batch, info, list_examples


@contextmanager
def capture_output():
    """Capture stdout and stderr for testing."""
    old_out, old_err = sys.stdout, sys.stderr
    try:
        out = StringIO()
        err = StringIO()
        sys.stdout, sys.stderr = out, err
        yield out, err
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestAnalyzeCommand:
    """Test the analyze command functionality."""
    
    @patch('main.StockAnalysisPipeline')
    def test_analyze_success(self, mock_pipeline_class):
        """Test successful stock analysis."""
        # Mock the pipeline and result
        mock_pipeline = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.stock_symbol = "AAPL"
        mock_result.rating_result.rating.value = "Buy"
        mock_result.rating_result.confidence = 0.85
        mock_result.processing_time_seconds = 12.5
        mock_result.analysis_date = "2024-01-01T10:00:00"
        mock_result.financial_data_html = "<table>...</table>"
        mock_result.company_sentiment = "Positive sentiment"
        mock_result.sector_sentiment = "Sector sentiment"
        
        mock_pipeline.analyze_stock.return_value = mock_result
        mock_pipeline.get_analysis_summary.return_value = "Analysis summary"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command
        with capture_output() as (out, err):
            try:
                analyze.callback("AAPL", False, None)
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify output contains expected content
        assert "🔍 Analyzing stock: AAPL" in output
        assert "✅ Analysis completed successfully!" in output
        assert "📊 Rating: Buy" in output
        assert "🎯 Confidence: 85.0%" in output
        assert "⏱️  Processing time: 12.50 seconds" in output
    
    @patch('main.StockAnalysisPipeline')
    def test_analyze_failure(self, mock_pipeline_class):
        """Test failed stock analysis."""
        # Mock the pipeline and result
        mock_pipeline = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "API key not found"
        
        mock_pipeline.analyze_stock.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command
        with capture_output() as (out, err):
            with pytest.raises(SystemExit):
                analyze.callback("INVALID", False, None)
        
        output = out.getvalue()
        
        # Verify output contains expected content
        assert "🔍 Analyzing stock: INVALID" in output
        assert "❌ Analysis failed!" in output
        assert "Error: API key not found" in output
    
    @patch('main.StockAnalysisPipeline')
    def test_analyze_with_export(self, mock_pipeline_class):
        """Test stock analysis with export functionality."""
        # Mock the pipeline and result
        mock_pipeline = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.stock_symbol = "MSFT"
        mock_result.rating_result.rating.value = "Hold"
        mock_result.rating_result.confidence = 0.75
        mock_result.processing_time_seconds = 8.2
        mock_result.analysis_date = "2024-01-01T10:00:00"
        
        mock_pipeline.analyze_stock.return_value = mock_result
        mock_pipeline.get_analysis_summary.return_value = "Analysis summary"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command with export
        with capture_output() as (out, err):
            try:
                analyze.callback("MSFT", True, None)
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify export functionality was called
        assert "📄 Analysis exported to:" in output
        mock_pipeline.export_analysis_to_file.assert_called_once()
    
    @patch('main.StockAnalysisPipeline')
    def test_analyze_with_custom_output(self, mock_pipeline_class):
        """Test stock analysis with custom output file."""
        # Mock the pipeline and result
        mock_pipeline = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.stock_symbol = "GOOGL"
        mock_result.rating_result.rating.value = "Strong Buy"
        mock_result.rating_result.confidence = 0.95
        mock_result.processing_time_seconds = 15.0
        mock_result.analysis_date = "2024-01-01T10:00:00"
        
        mock_pipeline.analyze_stock.return_value = mock_result
        mock_pipeline.get_analysis_summary.return_value = "Analysis summary"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command with custom output
        with capture_output() as (out, err):
            try:
                analyze.callback("GOOGL", False, "custom_analysis.txt")
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify custom output file was used
        assert "📄 Analysis exported to: custom_analysis.txt" in output
        mock_pipeline.export_analysis_to_file.assert_called_with(mock_result, "custom_analysis.txt")


class TestBatchCommand:
    """Test the batch command functionality."""
    
    @patch('main.StockAnalysisPipeline')
    def test_batch_success(self, mock_pipeline_class):
        """Test successful batch analysis."""
        # Mock the pipeline and results
        mock_pipeline = Mock()
        mock_result1 = Mock()
        mock_result1.success = True
        mock_result1.stock_symbol = "AAPL"
        mock_result1.rating_result.rating.value = "Buy"
        mock_result1.rating_result.confidence = 0.85
        
        mock_result2 = Mock()
        mock_result2.success = True
        mock_result2.stock_symbol = "MSFT"
        mock_result2.rating_result.rating.value = "Hold"
        mock_result2.rating_result.confidence = 0.75
        
        mock_pipeline.batch_analyze_stocks.return_value = [mock_result1, mock_result2]
        mock_pipeline.get_analysis_summary.return_value = "Analysis summary"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command
        with capture_output() as (out, err):
            try:
                batch.callback(("AAPL", "MSFT"), None, False)
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify output contains expected content
        assert "🔍 Analyzing 2 stocks: AAPL, MSFT" in output
        assert "✅ Successful analyses: 2" in output
        assert "❌ Failed analyses: 0" in output
        assert "AAPL: Buy (Confidence: 85.0%)" in output
        assert "MSFT: Hold (Confidence: 75.0%)" in output
    
    @patch('main.StockAnalysisPipeline')
    def test_batch_with_failures(self, mock_pipeline_class):
        """Test batch analysis with some failures."""
        # Mock the pipeline and results
        mock_pipeline = Mock()
        mock_result1 = Mock()
        mock_result1.success = True
        mock_result1.stock_symbol = "AAPL"
        mock_result1.rating_result.rating.value = "Buy"
        mock_result1.rating_result.confidence = 0.85
        
        mock_result2 = Mock()
        mock_result2.success = False
        mock_result2.stock_symbol = "INVALID"
        mock_result2.error_message = "Stock not found"
        
        mock_pipeline.batch_analyze_stocks.return_value = [mock_result1, mock_result2]
        mock_pipeline.get_analysis_summary.return_value = "Analysis summary"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command
        with capture_output() as (out, err):
            try:
                batch.callback(("AAPL", "INVALID"), None, False)
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify output contains expected content
        assert "✅ Successful analyses: 1" in output
        assert "❌ Failed analyses: 1" in output
        assert "INVALID: Stock not found" in output
    
    @patch('main.StockAnalysisPipeline')
    @patch('os.makedirs')
    def test_batch_with_export_dir(self, mock_makedirs, mock_pipeline_class):
        """Test batch analysis with export directory."""
        # Mock the pipeline and results
        mock_pipeline = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.stock_symbol = "AAPL"
        mock_result.rating_result.rating.value = "Buy"
        mock_result.rating_result.confidence = 0.85
        mock_result.analysis_date = "2024-01-01T10:00:00"
        
        mock_pipeline.batch_analyze_stocks.return_value = [mock_result]
        mock_pipeline.get_analysis_summary.return_value = "Analysis summary"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command with export directory
        with capture_output() as (out, err):
            try:
                batch.callback(("AAPL",), "./exports", False)
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify export directory functionality
        assert "📄 Exported:" in output
        mock_makedirs.assert_called_once_with("./exports", exist_ok=True)
        mock_pipeline.export_analysis_to_file.assert_called_once()
    
    @patch('main.StockAnalysisPipeline')
    def test_batch_summary_only(self, mock_pipeline_class):
        """Test batch analysis with summary-only option."""
        # Mock the pipeline and results
        mock_pipeline = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.stock_symbol = "AAPL"
        mock_result.rating_result.rating.value = "Buy"
        mock_result.rating_result.confidence = 0.85
        
        mock_pipeline.batch_analyze_stocks.return_value = [mock_result]
        mock_pipeline.get_analysis_summary.return_value = "Analysis summary"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command with summary-only
        with capture_output() as (out, err):
            try:
                batch.callback(("AAPL",), None, True)
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify summary-only functionality (should not call get_analysis_summary)
        assert "AAPL: Buy (Confidence: 85.0%)" in output
        mock_pipeline.get_analysis_summary.assert_not_called()


class TestInfoCommand:
    """Test the info command functionality."""
    
    @patch('main.StockAnalysisPipeline')
    def test_info_success(self, mock_pipeline_class):
        """Test successful stock info retrieval."""
        # Mock the pipeline
        mock_pipeline = Mock()
        mock_pipeline.financial_gatherer.from_stock_to_dataframe.return_value = "<table>Financial data</table>"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command
        with capture_output() as (out, err):
            try:
                info.callback("AAPL")
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify output contains expected content
        assert "ℹ️  Getting quick info for: AAPL" in output
        assert "✅ Financial data retrieved successfully!" in output
        assert "📊 Financial data size: 29 characters" in output
        assert "Financial data preview:" in output
    
    @patch('main.StockAnalysisPipeline')
    def test_info_failure(self, mock_pipeline_class):
        """Test failed stock info retrieval."""
        # Mock the pipeline to raise an exception
        mock_pipeline = Mock()
        mock_pipeline.financial_gatherer.from_stock_to_dataframe.side_effect = Exception("API error")
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the command
        with capture_output() as (out, err):
            with pytest.raises(SystemExit):
                info.callback("INVALID")
        
        output = out.getvalue()
        
        # Verify output contains expected content
        assert "ℹ️  Getting quick info for: INVALID" in output
        assert "❌ Error getting stock info: API error" in output


class TestListExamplesCommand:
    """Test the list_examples command functionality."""
    
    def test_list_examples(self):
        """Test the list_examples command."""
        with capture_output() as (out, err):
            list_examples.callback()
        
        output = out.getvalue()
        
        # Verify output contains expected content
        assert "📚 EXAMPLE COMMANDS" in output
        assert "🔍 Single Stock Analysis:" in output
        assert "📊 Batch Analysis:" in output
        assert "ℹ️  Quick Info:" in output
        assert "📚 Help:" in output
        assert "python main.py analyze AAPL" in output
        assert "python main.py batch AAPL MSFT GOOGL" in output
        assert "python main.py info AAPL" in output


class TestCLI:
    """Test the main CLI group."""
    
    def test_cli_help(self):
        """Test CLI help output."""
        with capture_output() as (out, err):
            try:
                cli.main(['--help'])
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify help output contains expected content
        assert "Stock Analysis Pipeline" in output
        assert "analyze" in output
        assert "batch" in output
        assert "info" in output
        assert "list-examples" in output
    
    def test_cli_version(self):
        """Test CLI version output."""
        with capture_output() as (out, err):
            try:
                cli.main(['--version'])
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify version output
        assert "1.0.0" in output


class TestIntegration:
    """Integration tests for the CLI commands."""
    
    @patch('main.StockAnalysisPipeline')
    def test_full_analyze_workflow(self, mock_pipeline_class):
        """Test the complete analyze workflow."""
        # Mock the pipeline
        mock_pipeline = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.stock_symbol = "TSLA"
        mock_result.rating_result.rating.value = "Strong Buy"
        mock_result.rating_result.confidence = 0.95
        mock_result.processing_time_seconds = 20.0
        mock_result.analysis_date = "2024-01-01T10:00:00"
        mock_result.financial_data_html = "<table>Financial data</table>"
        mock_result.company_sentiment = "Very positive sentiment"
        mock_result.sector_sentiment = "Sector is performing well"
        
        mock_pipeline.analyze_stock.return_value = mock_result
        mock_pipeline.get_analysis_summary.return_value = "Complete analysis summary"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Test the complete workflow
        with capture_output() as (out, err):
            try:
                analyze.callback("TSLA", True, "tesla_analysis.txt")
            except SystemExit:
                pass
        
        output = out.getvalue()
        
        # Verify the complete workflow
        assert "🔍 Analyzing stock: TSLA" in output
        assert "✅ Analysis completed successfully!" in output
        assert "📊 Rating: Strong Buy" in output
        assert "🎯 Confidence: 95.0%" in output
        assert "📄 Analysis exported to: tesla_analysis.txt" in output
        
        # Verify pipeline methods were called correctly
        mock_pipeline.analyze_stock.assert_called_once_with("TSLA")
        mock_pipeline.get_analysis_summary.assert_called_once_with(mock_result)
        mock_pipeline.export_analysis_to_file.assert_called_once_with(mock_result, "tesla_analysis.txt")


if __name__ == "__main__":
    pytest.main([__file__])
