"""
Stock Rating Module

This module provides a comprehensive class for rating stocks based on financial fundamentals
and sentiment analysis using OpenAI's ChatOpenAI.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from utils.config import env

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Rating(Enum):
    """Enum for stock ratings"""
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"
    STRONG_SELL = "Strong Sell"


@dataclass
class RatingResult:
    """Data class to store rating results"""
    rating: Rating
    confidence: float
    reasoning: str
    key_factors: List[str]
    risk_factors: List[str]
    recommendation_summary: str


class StockRater:
    """
    A class for rating stocks based on financial fundamentals and sentiment analysis.
    
    This class combines:
    - Financial fundamentals (HTML dataframe)
    - Company-specific sentiment analysis
    - Sector-specific sentiment analysis
    
    To provide comprehensive stock ratings using OpenAI's ChatOpenAI.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the StockRater.
        
        Args:
            openai_api_key: OpenAI API key (defaults to LLM_API_KEY env var)
        """
        self.openai_api_key = openai_api_key or env.LLM_API_KEY
        self.llm_name = env.LLM_NAME
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set LLM_API_KEY environment variable or pass openai_api_key parameter.")
        
        # Initialize ChatOpenAI
        self.chat_model = ChatOpenAI(
            model_name=self.llm_name,
            temperature=0.1,
            api_key=self.openai_api_key
        )
        
        logger.info("StockRater initialized successfully")
    
    def _create_rating_prompt(self, 
                             financial_data_html: str,
                             company_sentiment: str,
                             sector_sentiment: str,
                             company_name: str) -> str:
        """
        Create a comprehensive prompt for stock rating analysis.
        
        Args:
            financial_data_html: HTML table of financial fundamentals
            company_sentiment: Sentiment analysis for the company
            sector_sentiment: Sentiment analysis for the sector
            company_name: Name of the company being rated
            
        Returns:
            Formatted prompt string
        """
        # Read the prompt template from the external file
        prompt_template = open("prompts/stock_rating.md", "r").read()
        
        # Format the prompt with the provided data
        prompt = prompt_template.format(
            company_name=company_name,
            financial_data_html=financial_data_html,
            company_sentiment=company_sentiment,
            sector_sentiment=sector_sentiment
        )
        
        return prompt
    
    def rate_stock(self, 
                   financial_data_html: str,
                   company_sentiment: str,
                   sector_sentiment: str,
                   company_name: str) -> RatingResult:
        """
        Rate a stock based on financial fundamentals and sentiment analysis.
        
        Args:
            financial_data_html: HTML table of financial fundamentals
            company_sentiment: Sentiment analysis for the company
            sector_sentiment: Sentiment analysis for the sector
            company_name: Name of the company being rated
            
        Returns:
            RatingResult object with comprehensive rating analysis
        """
        try:
            logger.info(f"Starting stock rating analysis for {company_name}")
            
            # Create the analysis prompt
            prompt = self._create_rating_prompt(
                financial_data_html=financial_data_html,
                company_sentiment=company_sentiment,
                sector_sentiment=sector_sentiment,
                company_name=company_name
            )
            
            # Get response from ChatOpenAI
            response = self.chat_model([
                HumanMessage(content=prompt)
            ])
            
            # Parse the response
            response_text = response.content.strip()
            logger.info(f"Received rating response for {company_name}")
            
            # Parse JSON response
            import json
            try:
                rating_data = json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response for {company_name}")
                # Fallback to manual parsing or return error
                return self._create_fallback_rating(company_name, response_text)
            
            # Create RatingResult object
            rating_result = RatingResult(
                rating=Rating(rating_data["rating"]),
                confidence=float(rating_data["confidence"]),
                reasoning=rating_data["reasoning"],
                key_factors=rating_data["key_factors"],
                risk_factors=rating_data["risk_factors"],
                recommendation_summary=rating_data["recommendation_summary"]
            )
            
            logger.info(f"Successfully rated {company_name} as {rating_result.rating.value}")
            return rating_result
            
        except Exception as e:
            logger.error(f"Error rating stock {company_name}: {e}")
            return self._create_error_rating(company_name, str(e))
    
    def _create_fallback_rating(self, company_name: str, response_text: str) -> RatingResult:
        """Create a fallback rating when JSON parsing fails."""
        return RatingResult(
            rating=Rating.HOLD,
            confidence=0.5,
            reasoning=f"Unable to parse AI response. Raw response: {response_text[:200]}...",
            key_factors=["Analysis incomplete due to parsing error"],
            risk_factors=["Unable to complete full analysis"],
            recommendation_summary="Hold recommendation due to analysis limitations."
        )
    
    def _create_error_rating(self, company_name: str, error_message: str) -> RatingResult:
        """Create an error rating when analysis fails."""
        return RatingResult(
            rating=Rating.HOLD,
            confidence=0.0,
            reasoning=f"Analysis failed with error: {error_message}",
            key_factors=["Analysis could not be completed"],
            risk_factors=["Unable to assess risks due to analysis failure"],
            recommendation_summary="Unable to provide recommendation due to analysis error."
        )
    
    def get_rating_summary(self, rating_result: RatingResult) -> str:
        """
        Create a formatted summary of the rating result.
        
        Args:
            rating_result: RatingResult object
            
        Returns:
            Formatted summary string
        """
        summary = f"""
STOCK RATING SUMMARY
===================

Rating: {rating_result.rating.value}
Confidence: {rating_result.confidence:.1%}

REASONING:
{rating_result.reasoning}

KEY POSITIVE FACTORS:
{chr(10).join(f"• {factor}" for factor in rating_result.key_factors)}

RISK FACTORS:
{chr(10).join(f"• {factor}" for factor in rating_result.risk_factors)}

RECOMMENDATION:
{rating_result.recommendation_summary}
"""
        return summary
    
    def batch_rate_stocks(self, 
                         stock_data: List[Dict[str, Any]]) -> List[RatingResult]:
        """
        Rate multiple stocks in batch.
        
        Args:
            stock_data: List of dictionaries containing stock data with keys:
                       - financial_data_html: HTML table of financial data
                       - company_sentiment: Company sentiment analysis
                       - sector_sentiment: Sector sentiment analysis
                       - company_name: Company name
                       
        Returns:
            List of RatingResult objects
        """
        results = []
        for stock in stock_data:
            result = self.rate_stock(
                financial_data_html=stock["financial_data_html"],
                company_sentiment=stock["company_sentiment"],
                sector_sentiment=stock["sector_sentiment"],
                company_name=stock["company_name"]
            )
            results.append(result)
        
        return results


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    rater = StockRater()
    
    # Example data (replace with actual data)
    sample_financial_data = """
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>EPS</td><td>2.50</td></tr>
        <tr><td>ROE</td><td>15.2%</td></tr>
    </table>
    """
    
    sample_company_sentiment = "Positive sentiment with strong earnings growth and market expansion."
    sample_sector_sentiment = "Sector showing strong growth with favorable regulatory environment."
    
    # Rate a stock
    result = rater.rate_stock(
        financial_data_html=sample_financial_data,
        company_sentiment=sample_company_sentiment,
        sector_sentiment=sample_sector_sentiment,
        company_name="AAPL"
    )
    
    # Print summary
    print(rater.get_rating_summary(result))
