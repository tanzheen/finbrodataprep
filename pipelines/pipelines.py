"""
Stock Analysis Pipeline

This module provides a comprehensive pipeline for analyzing stocks by combining:
1. News sentiment analysis (company and sector level)
2. Financial fundamentals analysis
3. Final stock rating based on all data

The pipeline takes a stock symbol and returns a complete analysis with rating.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

# Import our custom modules
from fundamentals.fmp import FMPFinancialDataGatherer
from fundamentals.alphavantage import AlphavantageFinancialDataGatherer
from news_sentiment.news_collator import SentimentCollator
from ratings.rater import StockRater, RatingResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StockAnalysisResult:
    """Data class to store complete stock analysis results"""
    stock_symbol: str
    analysis_date: str
    financial_data_html: str
    company_sentiment: str
    sector_sentiment: str
    rating_result: RatingResult
    processing_time_seconds: float
    success: bool
    error_message: Optional[str] = None


class StockAnalysisPipeline:
    """
    A comprehensive pipeline for stock analysis that combines:
    - News sentiment analysis (company and sector level)
    - Financial fundamentals analysis
    - Final stock rating based on all data
    """
    
    def __init__(self):
        """Initialize the pipeline with all required components."""
        try:
            logger.info("Initializing Stock Analysis Pipeline...")
            
            # Initialize all components
            logger.info("Initializing FinancialDataGatherer")
            self.financial_gatherer = AlphavantageFinancialDataGatherer()
            
            logger.info("Initializing SentimentCollator")
            self.sentiment_collator = SentimentCollator()
            
            logger.info("Initializing StockRater")
            self.stock_rater = StockRater()
            
            logger.info("Stock Analysis Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
            raise
    
    def analyze_stock(self, stock_symbol: str) -> StockAnalysisResult:
        """
        Perform complete stock analysis including sentiment, fundamentals, and rating.
        
        Args:
            stock_symbol: Stock symbol (e.g., "AAPL", "MSFT")
            
        Returns:
            StockAnalysisResult with complete analysis
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting analysis for stock: {stock_symbol}")
            
            # Step 1: Get financial fundamentals
            logger.info(f"Step 1/3: Gathering financial data for {stock_symbol}")
            financial_data_html = self._get_financial_data(stock_symbol)
            logger.info(f"Financial data retrieved for {stock_symbol}. Length: {len(financial_data_html)} characters")
            
            # Step 2: Get news sentiment analysis
            logger.info(f"Step 2/3: Analyzing news sentiment for {stock_symbol}")
            company_sentiment, sector_sentiment = self._get_sentiment_analysis(stock_symbol)
            logger.info(f"Sentiment analysis completed for {stock_symbol}. Company sentiment length: {len(company_sentiment)}, Sector sentiment length: {len(sector_sentiment)}")
            
            # Step 3: Generate final rating
            logger.info(f"Step 3/3: Generating rating for {stock_symbol}")
            rating_result = self._generate_rating(
                stock_symbol, 
                financial_data_html, 
                company_sentiment, 
                sector_sentiment
            )
            logger.info(f"Rating generated for {stock_symbol}: {rating_result.rating.value} (Confidence: {rating_result.confidence:.1%})")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Analysis completed for {stock_symbol}. Processing time: {processing_time:.2f} seconds")
            
            # Create result object
            result = StockAnalysisResult(
                stock_symbol=stock_symbol.upper(),
                analysis_date=datetime.now().isoformat(),
                financial_data_html=financial_data_html,
                company_sentiment=company_sentiment,
                sector_sentiment=sector_sentiment,
                rating_result=rating_result,
                processing_time_seconds=processing_time,
                success=True
            )
            
            logger.info(f"Successfully completed analysis for {stock_symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing stock {stock_symbol}: {e}", exc_info=True)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return StockAnalysisResult(
                stock_symbol=stock_symbol.upper(),
                analysis_date=datetime.now().isoformat(),
                financial_data_html="",
                company_sentiment="",
                sector_sentiment="",
                rating_result=self._create_error_rating_result(),
                processing_time_seconds=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _get_financial_data(self, stock_symbol: str) -> str:
        """Get financial fundamentals data for the stock."""
        try:
            logger.info(f"Retrieving financial data for {stock_symbol}")
            financial_data = self.financial_gatherer.from_stock_to_dataframe(stock_symbol)
            logger.info(f"Financial data retrieved successfully for {stock_symbol}")
            return financial_data
        except Exception as e:
            logger.error(f"Error getting financial data for {stock_symbol}: {e}", exc_info=True)
            raise
    
    def _get_sentiment_analysis(self, stock_symbol: str) -> Tuple[str, str]:
        """Get news sentiment analysis for company and sector."""
        try:
            logger.info(f"Retrieving sentiment analysis for {stock_symbol}")
            company_sentiment, sector_sentiment = self.sentiment_collator.get_stock_sentiment(stock_symbol)
            logger.info(f"Sentiment analysis retrieved successfully for {stock_symbol}")
            return company_sentiment, sector_sentiment
        except Exception as e:
            logger.error(f"Error getting sentiment analysis for {stock_symbol}: {e}", exc_info=True)
            raise
    
    def _generate_rating(self, 
                        stock_symbol: str, 
                        financial_data_html: str, 
                        company_sentiment: str, 
                        sector_sentiment: str) -> RatingResult:
        """Generate final stock rating based on all data."""
        try:
            logger.info(f"Generating rating for {stock_symbol}")
            rating_result = self.stock_rater.rate_stock(
                financial_data_html=financial_data_html,
                company_sentiment=company_sentiment,
                sector_sentiment=sector_sentiment,
                company_name=stock_symbol
            )
            logger.info(f"Rating generated successfully for {stock_symbol}")
            return rating_result
        except Exception as e:
            logger.error(f"Error generating rating for {stock_symbol}: {e}", exc_info=True)
            raise
    
    def _create_error_rating_result(self) -> RatingResult:
        """Create a default rating result for error cases."""
        logger.warning("Creating error rating result due to analysis failure")
        from ratings.rater import Rating
        return RatingResult(
            rating=Rating.HOLD,
            confidence=0.0,
            reasoning="Analysis failed - unable to complete rating",
            key_factors=["Analysis could not be completed"],
            risk_factors=["Unable to assess risks due to analysis failure"],
            recommendation_summary="Unable to provide recommendation due to analysis error."
        )
    
    def batch_analyze_stocks(self, stock_symbols: List[str]) -> List[StockAnalysisResult]:
        """
        Analyze multiple stocks in batch.
        
        Args:
            stock_symbols: List of stock symbols to analyze
            
        Returns:
            List of StockAnalysisResult objects
        """
        results = []
        total_stocks = len(stock_symbols)
        
        logger.info(f"Starting batch analysis of {total_stocks} stocks: {stock_symbols}")
        
        for i, symbol in enumerate(stock_symbols, 1):
            logger.info(f"Analyzing stock {i}/{total_stocks}: {symbol}")
            result = self.analyze_stock(symbol)
            results.append(result)
            
            # Log progress
            success_count = sum(1 for r in results if r.success)
            logger.info(f"Progress: {i}/{total_stocks} completed, {success_count} successful")
        
        logger.info(f"Batch analysis completed. {len([r for r in results if r.success])}/{total_stocks} successful")
        return results
    
    def get_analysis_summary(self, result: StockAnalysisResult) -> str:
        """
        Create a formatted summary of the complete analysis.
        
        Args:
            result: StockAnalysisResult object
            
        Returns:
            Formatted summary string
        """
        logger.info(f"Creating analysis summary for {result.stock_symbol}")
        
        if not result.success:
            logger.warning(f"Creating error summary for failed analysis of {result.stock_symbol}")
            return f"""
STOCK ANALYSIS FAILED
====================

Stock: {result.stock_symbol}
Error: {result.error_message}
Processing Time: {result.processing_time_seconds:.2f} seconds
"""
        
        # Get rating summary from the rater
        logger.info(f"Getting rating summary for {result.stock_symbol}")
        rating_summary = self.stock_rater.get_rating_summary(result.rating_result)
        
        # Create complete summary
        logger.info(f"Creating complete analysis summary for {result.stock_symbol}")
        summary = f"""
COMPLETE STOCK ANALYSIS
======================

Stock Symbol: {result.stock_symbol}
Analysis Date: {result.analysis_date}
Processing Time: {result.processing_time_seconds:.2f} seconds

{rating_summary}

SENTIMENT ANALYSIS
=================

Company Sentiment:
{result.company_sentiment}

Sector Sentiment:
{result.sector_sentiment}

FINANCIAL DATA
==============
{result.financial_data_html}
"""
        logger.info(f"Analysis summary created for {result.stock_symbol}. Length: {len(summary)} characters")
        return summary
    
    def export_analysis_to_file(self, result: StockAnalysisResult, filename: str, format: str = "txt") -> None:
        """
        Export the complete analysis to a file.
        
        Args:
            result: StockAnalysisResult object
            filename: Output filename
            format: Export format ("txt", "json", "csv")
        """
        try:
            logger.info(f"Exporting analysis for {result.stock_symbol} to {filename} in {format} format")
            
            if format.lower() == "json":
                self._export_to_json(result, filename)
            elif format.lower() == "csv":
                self._export_to_csv(result, filename)
            else:  # Default to txt
                self._export_to_txt(result, filename)
            
            logger.info(f"Analysis exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting analysis to {filename}: {e}", exc_info=True)
            raise
    
    def _export_to_txt(self, result: StockAnalysisResult, filename: str) -> None:
        """Export analysis to text format."""
        logger.info(f"Exporting {result.stock_symbol} analysis to text file: {filename}")
        summary = self.get_analysis_summary(result)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(summary)
    
    def _export_to_json(self, result: StockAnalysisResult, filename: str) -> None:
        """Export analysis to JSON format."""
        logger.info(f"Exporting {result.stock_symbol} analysis to JSON file: {filename}")
        
        import json
        from datetime import datetime
        
        # Create structured JSON data
        export_data = {
            "stock_symbol": result.stock_symbol,
            "analysis_date": result.analysis_date,
            "processing_time_seconds": result.processing_time_seconds,
            "success": result.success,
            "error_message": result.error_message,
            "rating": {
                "value": result.rating_result.rating.value,
                "confidence": result.rating_result.confidence,
                "reasoning": result.rating_result.reasoning,
                "key_factors": result.rating_result.key_factors,
                "risk_factors": result.rating_result.risk_factors,
                "recommendation_summary": result.rating_result.recommendation_summary
            },
            "sentiment": {
                "company_sentiment": result.company_sentiment,
                "sector_sentiment": result.sector_sentiment
            },
            "financial_data_html": result.financial_data_html,
            "export_timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _export_to_csv(self, result: StockAnalysisResult, filename: str) -> None:
        """Export analysis to CSV format (summary only)."""
        logger.info(f"Exporting {result.stock_symbol} analysis to CSV file: {filename}")
        
        import csv
        
        # Create CSV with key metrics
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "Stock Symbol", "Analysis Date", "Rating", "Confidence", 
                "Processing Time (s)", "Success", "Key Factors Count", "Risk Factors Count"
            ])
            
            # Write data row
            writer.writerow([
                result.stock_symbol,
                result.analysis_date,
                result.rating_result.rating.value,
                f"{result.rating_result.confidence:.3f}",
                f"{result.processing_time_seconds:.2f}",
                result.success,
                len(result.rating_result.key_factors),
                len(result.rating_result.risk_factors)
            ])
    
    def export_batch_results(self, results: List[StockAnalysisResult], output_dir: str = "analysis_results", format: str = "txt") -> None:
        """
        Export multiple analysis results to files.
        
        Args:
            results: List of StockAnalysisResult objects
            output_dir: Directory to save files
            format: Export format ("txt", "json", "csv")
        """
        try:
            import os
            from datetime import datetime
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created/verified output directory: {output_dir}")
            
            # Create timestamp for this batch
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            successful_exports = 0
            failed_exports = 0
            
            for i, result in enumerate(results, 1):
                try:
                    # Create filename with timestamp
                    if format.lower() == "csv":
                        filename = os.path.join(output_dir, f"batch_{timestamp}.csv")
                        # For CSV, we'll append all results to one file
                        if i == 1:  # First result, create new file
                            self._export_to_csv(result, filename)
                        else:  # Append to existing file
                            self._append_to_csv(result, filename)
                    else:
                        # Individual files for txt and json
                        filename = os.path.join(output_dir, f"{result.stock_symbol}_{timestamp}.{format}")
                        self.export_analysis_to_file(result, filename, format)
                    
                    successful_exports += 1
                    logger.info(f"Exported {result.stock_symbol} ({i}/{len(results)})")
                    
                except Exception as e:
                    failed_exports += 1
                    logger.error(f"Failed to export {result.stock_symbol}: {e}")
            
            logger.info(f"Batch export completed. Successful: {successful_exports}, Failed: {failed_exports}")
            
        except Exception as e:
            logger.error(f"Error in batch export: {e}", exc_info=True)
            raise
    
    def _append_to_csv(self, result: StockAnalysisResult, filename: str) -> None:
        """Append a single result to existing CSV file."""
        import csv
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                result.stock_symbol,
                result.analysis_date,
                result.rating_result.rating.value,
                f"{result.rating_result.confidence:.3f}",
                f"{result.processing_time_seconds:.2f}",
                result.success,
                len(result.rating_result.key_factors),
                len(result.rating_result.risk_factors)
            ])
    
    def create_analysis_report(self, results: List[StockAnalysisResult], output_file: str = None) -> str:
        """
        Create a comprehensive analysis report for multiple stocks.
        
        Args:
            results: List of StockAnalysisResult objects
            output_file: Optional file to save the report
            
        Returns:
            Report content as string
        """
        try:
            logger.info(f"Creating comprehensive analysis report for {len(results)} stocks")
            
            successful_results = [r for r in results if r.success]
            failed_results = [r for r in results if not r.success]
            
            # Calculate summary statistics
            total_processing_time = sum(r.processing_time_seconds for r in results)
            avg_confidence = sum(r.rating_result.confidence for r in successful_results) / len(successful_results) if successful_results else 0
            
            # Create rating distribution
            rating_counts = {}
            for result in successful_results:
                rating = result.rating_result.rating.value
                rating_counts[rating] = rating_counts.get(rating, 0) + 1
            
            # Generate report
            report = f"""
COMPREHENSIVE STOCK ANALYSIS REPORT
===================================

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total Stocks Analyzed: {len(results)}
Successful Analyses: {len(successful_results)}
Failed Analyses: {len(failed_results)}
Total Processing Time: {total_processing_time:.2f} seconds
Average Processing Time: {total_processing_time/len(results):.2f} seconds per stock

RATING DISTRIBUTION
==================
"""
            for rating, count in rating_counts.items():
                percentage = (count / len(successful_results)) * 100
                report += f"{rating}: {count} stocks ({percentage:.1f}%)\n"
            
            report += f"""
AVERAGE CONFIDENCE: {avg_confidence:.1%}

DETAILED RESULTS
===============
"""
            
            # Add individual results
            for result in results:
                report += f"""
{result.stock_symbol.upper()}
{'=' * len(result.stock_symbol)}
Rating: {result.rating_result.rating.value}
Confidence: {result.rating_result.confidence:.1%}
Processing Time: {result.processing_time_seconds:.2f}s
Success: {result.success}
"""
                if not result.success:
                    report += f"Error: {result.error_message}\n"
                else:
                    report += f"Key Factors: {', '.join(result.rating_result.key_factors[:3])}\n"
                    report += f"Risk Factors: {', '.join(result.rating_result.risk_factors[:3])}\n"
            
            # Save to file if specified
            if output_file:
                logger.info(f"Saving analysis report to {output_file}")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
            
            logger.info(f"Analysis report created. Length: {len(report)} characters")
            return report
            
        except Exception as e:
            logger.error(f"Error creating analysis report: {e}", exc_info=True)
            raise


# Example usage and testing
if __name__ == "__main__":
    logger.info("Running Stock Analysis Pipeline example")
    
    # Example usage
    pipeline = StockAnalysisPipeline()
    
    # Analyze a single stock
    logger.info("Running single stock analysis example")
    result = pipeline.analyze_stock("AAPL")
    
    # Print summary
    logger.info("Printing analysis summary")
    print(pipeline.get_analysis_summary(result))
    
    # Export to file
    logger.info("Exporting analysis to file")
    pipeline.export_analysis_to_file(result, f"analysis_{result.stock_symbol}_{result.analysis_date[:10]}.txt")
    
    # Example batch analysis
    logger.info("Running batch analysis example")
    stocks_to_analyze = ["AAPL", "MSFT", "GOOGL"]
    batch_results = pipeline.batch_analyze_stocks(stocks_to_analyze)
    
    # Print batch summary
    logger.info("Printing batch analysis summary")
    for result in batch_results:
        print(f"\n{result.stock_symbol}: {result.rating_result.rating.value} (Confidence: {result.rating_result.confidence:.1%})")
