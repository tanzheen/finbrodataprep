#!/usr/bin/env python3
"""
Main script for the Stock Analysis Pipeline

This script provides a simple interface to analyze stocks using the comprehensive pipeline.
"""

import click
import sys
import os
import logging
from typing import List
from datetime import datetime

from pipelines.pipelines import StockAnalysisPipeline

# Setup logging
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Stock Analysis Pipeline - Comprehensive stock analysis with sentiment and fundamentals.
    
    Analyze stocks using financial data, news sentiment, and AI-powered ratings.
    """
    logger.info("Stock Analysis Pipeline CLI started")
    pass


@cli.command()
@click.argument('stock_symbol', type=str)
@click.option('--no-export', is_flag=True, help='Skip exporting analysis to file')
@click.option('--output', '-o', type=click.Path(), help='Output file path for export')
@click.option('--format', type=click.Choice(['txt', 'json', 'csv']), default='txt', help='Export format (txt, json, csv)')
def analyze(stock_symbol: str, no_export: bool, output: str, format: str):
    """
    Analyze a single stock and display results.
    
    STOCK_SYMBOL: Stock symbol to analyze (e.g., AAPL, MSFT, GOOGL)
    """
    logger.info(f"Starting single stock analysis for: {stock_symbol}")
    click.echo(f"🔍 Analyzing stock: {stock_symbol}")
    click.echo("=" * 50)
    
    try:
        # Initialize pipeline
        logger.info("Initializing Stock Analysis Pipeline")
        pipeline = StockAnalysisPipeline()
        
        # Perform analysis
        logger.info(f"Starting analysis pipeline for {stock_symbol}")
        result = pipeline.analyze_stock(stock_symbol)
        
        if result.success:
            logger.info(f"Analysis completed successfully for {stock_symbol}")
            click.echo("✅ Analysis completed successfully!")
            click.echo(f"📊 Rating: {result.rating_result.rating.value}")
            click.echo(f"🎯 Confidence: {result.rating_result.confidence:.1%}")
            click.echo(f"⏱️  Processing time: {result.processing_time_seconds:.2f} seconds")
            
            # Display detailed summary
            click.echo("\n" + "=" * 50)
            click.echo(pipeline.get_analysis_summary(result))
            
            # Export to file (default behavior unless --no-export is specified)
            if not no_export:
                if output:
                    filename = output
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"analysis_{result.stock_symbol}_{timestamp}.{format}"
                
                logger.info(f"Exporting analysis to file: {filename} in {format} format")
                pipeline.export_analysis_to_file(result, filename, format)
                click.echo(f"\n📄 Analysis exported to: {filename}")
            else:
                logger.info("Skipping export as requested with --no-export flag")
        else:
            logger.error(f"Analysis failed for {stock_symbol}: {result.error_message}")
            click.echo("❌ Analysis failed!")
            click.echo(f"Error: {result.error_message}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error during analysis of {stock_symbol}: {e}", exc_info=True)
        click.echo(f"❌ Error during analysis: {e}")
        sys.exit(1)


@cli.command()
@click.argument('stock_symbols', nargs=-1, required=True)
@click.option('--export-dir', type=click.Path(), default='analysis_results', help='Directory to export analysis files')
@click.option('--no-export', is_flag=True, help='Skip exporting analysis files')
@click.option('--summary-only', is_flag=True, help='Show only summary, not detailed results')
@click.option('--format', type=click.Choice(['txt', 'json', 'csv']), default='txt', help='Export format (txt, json, csv)')
@click.option('--report', is_flag=True, help='Generate comprehensive analysis report')
def batch(stock_symbols: tuple, export_dir: str, no_export: bool, summary_only: bool, format: str, report: bool):
    """
    Analyze multiple stocks and display summary results.
    
    STOCK_SYMBOLS: One or more stock symbols to analyze (e.g., AAPL MSFT GOOGL)
    """
    symbols = list(stock_symbols)
    logger.info(f"Starting batch analysis for {len(symbols)} stocks: {symbols}")
    click.echo(f"🔍 Analyzing {len(symbols)} stocks: {', '.join(symbols)}")
    click.echo("=" * 50)
    
    try:
        # Initialize pipeline
        logger.info("Initializing Stock Analysis Pipeline for batch processing")
        pipeline = StockAnalysisPipeline()
        
        # Perform batch analysis
        logger.info(f"Starting batch analysis pipeline for {len(symbols)} stocks")
        results = pipeline.batch_analyze_stocks(symbols)
        
        # Display summary
        click.echo("\n📊 ANALYSIS SUMMARY")
        click.echo("=" * 50)
        
        successful_analyses = [r for r in results if r.success]
        failed_analyses = [r for r in results if not r.success]
        
        logger.info(f"Batch analysis completed. Successful: {len(successful_analyses)}, Failed: {len(failed_analyses)}")
        click.echo(f"✅ Successful analyses: {len(successful_analyses)}")
        click.echo(f"❌ Failed analyses: {len(failed_analyses)}")
        
        if successful_analyses:
            click.echo("\n📈 RATINGS SUMMARY:")
            click.echo("-" * 30)
            for result in successful_analyses:
                logger.info(f"Stock {result.stock_symbol}: {result.rating_result.rating.value} (Confidence: {result.rating_result.confidence:.1%})")
                click.echo(f"{result.stock_symbol}: {result.rating_result.rating.value} "
                          f"(Confidence: {result.rating_result.confidence:.1%})")
        
        if failed_analyses:
            click.echo("\n❌ FAILED ANALYSES:")
            click.echo("-" * 30)
            for result in failed_analyses:
                logger.error(f"Failed analysis for {result.stock_symbol}: {result.error_message}")
                click.echo(f"{result.stock_symbol}: {result.error_message}")
        
        # Export files (default behavior unless --no-export is specified)
        if not no_export:
            logger.info(f"Exporting analysis files to directory: {export_dir} in {format} format")
            pipeline.export_batch_results(results, export_dir, format)
            click.echo(f"\n📄 Analysis files exported to: {export_dir}")
        else:
            logger.info("Skipping export as requested with --no-export flag")
        
        # Generate comprehensive report if requested
        if report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"analysis_report_{timestamp}.txt"
            logger.info(f"Generating comprehensive analysis report: {report_filename}")
            report_content = pipeline.create_analysis_report(results, report_filename)
            click.echo(f"\n📋 Comprehensive report generated: {report_filename}")
        
        # Display detailed results if not summary-only
        if not summary_only:
            for result in successful_analyses:
                click.echo(f"\n" + "=" * 50)
                click.echo(f"DETAILED ANALYSIS: {result.stock_symbol}")
                click.echo("=" * 50)
                click.echo(pipeline.get_analysis_summary(result))
            
    except Exception as e:
        logger.error(f"Unexpected error during batch analysis: {e}", exc_info=True)
        click.echo(f"❌ Error during batch analysis: {e}")
        sys.exit(1)


@cli.command()
@click.argument('stock_symbol', type=str)
def info(stock_symbol: str):
    """
    Get quick information about a stock without full analysis.
    
    STOCK_SYMBOL: Stock symbol to get info for (e.g., AAPL)
    """
    logger.info(f"Getting quick info for stock: {stock_symbol}")
    click.echo(f"ℹ️  Getting quick info for: {stock_symbol}")
    click.echo("=" * 50)
    
    try:
        # Initialize pipeline
        logger.info("Initializing Stock Analysis Pipeline for quick info")
        pipeline = StockAnalysisPipeline()
        
        # Get just financial data for quick info
        logger.info(f"Retrieving financial data for {stock_symbol}")
        financial_data = pipeline.financial_gatherer.from_stock_to_dataframe(stock_symbol)
        
        logger.info(f"Successfully retrieved financial data for {stock_symbol}")
        click.echo("✅ Financial data retrieved successfully!")
        click.echo(f"📊 Financial data size: {len(financial_data)} characters")
        click.echo("\nFinancial data preview:")
        click.echo("-" * 30)
        click.echo(financial_data[:500] + "..." if len(financial_data) > 500 else financial_data)
        
    except Exception as e:
        logger.error(f"Error getting stock info for {stock_symbol}: {e}", exc_info=True)
        click.echo(f"❌ Error getting stock info: {e}")
        sys.exit(1)


@cli.command()
def list_examples():
    """Show example commands and usage."""
    logger.info("Displaying example commands")
    click.echo("📚 EXAMPLE COMMANDS")
    click.echo("=" * 50)
    click.echo("\n🔍 Single Stock Analysis:")
    click.echo("  python main.py analyze AAPL")
    click.echo("  python main.py analyze AAPL --no-export")
    click.echo("  python main.py analyze AAPL -o my_analysis.txt")
    click.echo("  python main.py analyze AAPL --format json")
    click.echo("  python main.py analyze AAPL --format csv")
    
    click.echo("\n📊 Batch Analysis:")
    click.echo("  python main.py batch AAPL MSFT GOOGL")
    click.echo("  python main.py batch AAPL MSFT --no-export")
    click.echo("  python main.py batch AAPL MSFT --export-dir ./analyses")
    click.echo("  python main.py batch AAPL MSFT --summary-only")
    click.echo("  python main.py batch AAPL MSFT --format json")
    click.echo("  python main.py batch AAPL MSFT --format csv")
    click.echo("  python main.py batch AAPL MSFT --report")
    
    click.echo("\nℹ️  Quick Info:")
    click.echo("  python main.py info AAPL")
    
    click.echo("\n📚 Help:")
    click.echo("  python main.py --help")
    click.echo("  python main.py analyze --help")
    click.echo("  python main.py batch --help")
    
    click.echo("\n📁 Export Formats:")
    click.echo("  txt  - Human-readable text format (default)")
    click.echo("  json - Structured JSON data for programmatic use")
    click.echo("  csv  - Summary data in CSV format for spreadsheets")
    
    click.echo("\n💡 Default Behavior:")
    click.echo("  • Single analysis: Automatically exports to timestamped file")
    click.echo("  • Batch analysis: Automatically exports to 'analysis_results' directory")
    click.echo("  • Use --no-export to skip file export")


if __name__ == "__main__":
    logger.info("Stock Analysis Pipeline CLI started")
    cli()
