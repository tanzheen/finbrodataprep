#!/usr/bin/env python3
"""
Main script for the Stock Analysis Pipeline

This script provides a simple interface to analyze stocks using the comprehensive pipeline.
"""

import argparse
import sys
from typing import List

from pipelines.pipelines import StockAnalysisPipeline


def analyze_single_stock(stock_symbol: str, export_file: bool = False) -> None:
    """
    Analyze a single stock and display results.
    
    Args:
        stock_symbol: Stock symbol to analyze
        export_file: Whether to export results to file
    """
    print(f"🔍 Analyzing stock: {stock_symbol}")
    print("=" * 50)
    
    try:
        # Initialize pipeline
        pipeline = StockAnalysisPipeline()
        
        # Perform analysis
        result = pipeline.analyze_stock(stock_symbol)
        
        if result.success:
            print("✅ Analysis completed successfully!")
            print(f"📊 Rating: {result.rating_result.rating.value}")
            print(f"🎯 Confidence: {result.rating_result.confidence:.1%}")
            print(f"⏱️  Processing time: {result.processing_time_seconds:.2f} seconds")
            
            # Display detailed summary
            print("\n" + "=" * 50)
            print(pipeline.get_analysis_summary(result))
            
            # Export to file if requested
            if export_file:
                filename = f"analysis_{result.stock_symbol}_{result.analysis_date[:10]}.txt"
                pipeline.export_analysis_to_file(result, filename)
                print(f"\n📄 Analysis exported to: {filename}")
        else:
            print("❌ Analysis failed!")
            print(f"Error: {result.error_message}")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        sys.exit(1)


def analyze_multiple_stocks(stock_symbols: List[str]) -> None:
    """
    Analyze multiple stocks and display summary results.
    
    Args:
        stock_symbols: List of stock symbols to analyze
    """
    print(f"🔍 Analyzing {len(stock_symbols)} stocks: {', '.join(stock_symbols)}")
    print("=" * 50)
    
    try:
        # Initialize pipeline
        pipeline = StockAnalysisPipeline()
        
        # Perform batch analysis
        results = pipeline.batch_analyze_stocks(stock_symbols)
        
        # Display summary
        print("\n📊 ANALYSIS SUMMARY")
        print("=" * 50)
        
        successful_analyses = [r for r in results if r.success]
        failed_analyses = [r for r in results if not r.success]
        
        print(f"✅ Successful analyses: {len(successful_analyses)}")
        print(f"❌ Failed analyses: {len(failed_analyses)}")
        
        if successful_analyses:
            print("\n📈 RATINGS SUMMARY:")
            print("-" * 30)
            for result in successful_analyses:
                print(f"{result.stock_symbol}: {result.rating_result.rating.value} "
                      f"(Confidence: {result.rating_result.confidence:.1%})")
        
        if failed_analyses:
            print("\n❌ FAILED ANALYSES:")
            print("-" * 30)
            for result in failed_analyses:
                print(f"{result.stock_symbol}: {result.error_message}")
        
        # Display detailed results for successful analyses
        for result in successful_analyses:
            print(f"\n" + "=" * 50)
            print(f"DETAILED ANALYSIS: {result.stock_symbol}")
            print("=" * 50)
            print(pipeline.get_analysis_summary(result))
            
    except Exception as e:
        print(f"❌ Error during batch analysis: {e}")
        sys.exit(1)


def main():
    """Main function to handle command line arguments and execute analysis."""
    parser = argparse.ArgumentParser(
        description="Stock Analysis Pipeline - Comprehensive stock analysis with sentiment and fundamentals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py AAPL                    # Analyze Apple stock
  python main.py AAPL --export          # Analyze and export to file
  python main.py AAPL MSFT GOOGL        # Analyze multiple stocks
        """
    )
    
    parser.add_argument(
        "stocks",
        nargs="+",
        help="Stock symbol(s) to analyze (e.g., AAPL MSFT GOOGL)"
    )
    
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export detailed analysis to file"
    )
    
    args = parser.parse_args()
    
    # Validate stock symbols
    stock_symbols = [symbol.upper() for symbol in args.stocks]
    
    # Perform analysis
    if len(stock_symbols) == 1:
        analyze_single_stock(stock_symbols[0], args.export)
    else:
        analyze_multiple_stocks(stock_symbols)


if __name__ == "__main__":
    main()
