import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging

# Third-party imports
from exa_py import Exa
from openai import OpenAI
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from utils.config import env
from tavily import TavilyClient
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """Data class to store news article information"""
    title: str
    url: str
    published_date: Optional[str]
    content: str
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    search_query: Optional[str] = None
    collected_at: Optional[str] = None

class SentimentCollator:
    """
    A class to gather news from various sources using Exa AI,
    perform summaries using OpenAI, and conduct sentiment analysis.
    """
    
    def __init__(self, exa_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        """
        Initialize the NewsCollator with API keys.
        
        Args:
            exa_api_key: Exa AI API key (defaults to EXA_API_KEY env var)
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        # Initialize API keys
        self.exa_api_key = exa_api_key or os.getenv('EXA_API_KEY')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.exa_api_key:
            raise ValueError("Exa API key is required. Set EXA_API_KEY environment variable or pass exa_api_key parameter.")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        
        # Initialize API clients
        self.exa_client = Exa(api_key=self.exa_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
        # Storage for collected data
        self.articles: List[NewsArticle] = []
        
        logger.info("NewsCollator initialized successfully")

    def context_search(self, query: str, max_results: int = 5) -> str:
        """
        Search for context about the company using DuckDuckGo.
        """
        results = self.tavily_client.search(query = query)
        results = results['results']
        results = [result['content'] for result in results]
        results = "\n".join(results)
        return results
        
    def generate_queries(self, company_name: str) -> List[str]:
        """
        Generate queries for news search using llm 
        """

        context = self.context_search(company_name + " company")

        prompt = """
        You are a financial news analyst. 
        You are given a company and you need to generate a list of queries to search for news about the company stock.
        You should generate queries regarding the company and the sector that the company is in.
        The queries should be looking for news from reliable sources.
        The queries should be in the format of a list of strings.

        Strictly return the list of queries, no other text.
        
        Example:
        Input: AAPL
        Output: ["AAPL stock nasdaq news", "AAPL stock cnbc news", "tech sector news"]

        Input: NVDA
        Output: ["NVDA stock nasdaq news", "semiconductor sector news"]

        Use the following context about the company to generate the queries about the company and the sector.
        {context}
        
        """
        chat = ChatOpenAI(model_name=env.LLM_NAME, temperature=0)
        response = chat([
            HumanMessage(content=prompt.format(context=context))
        ])
        return response.content.strip()
    
    def search_news(self, 
                   query: str) -> List[NewsArticle]:
        """
        Search for news articles using Exa AI.
        
        Args:
            query: Search query (e.g., "AAPL stock news")
            num_results: Number of results to return
            time_period: Time period for search (e.g., "1d", "7d", "30d")
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude
            
        Returns:
            List of NewsArticle objects
        """
        try:

            logger.info(f"Searching for news with query: {query}")
            search_queries = self.generate_queries(query)
            combined_search_response = []
            articles = []
            for query in search_queries:    
                # Perform search
                search_response = self.exa_client.search( query, 
                                                        text = True, 
                                                        start_published_date=datetime.now() - timedelta(days=7),
                                                        end_published_date=datetime.now(),
                                                        context= True) 
                combined_search_response.extend(search_response.results)
            
            articles = []
            for result in combined_search_response:
                try:
                    # Get full content for each article
                    content_response = self.exa_client.get_contents([result.url])
                    content = content_response.contents[0] if content_response.contents else ""
                    
                    article = NewsArticle(
                        title=result.title,
                        url=result.url,
                        published_date=result.published_date,
                        content=content.text if content else "",
                        search_query=query,
                        collected_at=datetime.now().isoformat()
                    )
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Failed to get content for {result.url}: {e}")
                    # Still add the article with basic info
                    article = NewsArticle(
                        title=result.title,
                        url=result.url,
                        published_date=result.published_date,
                        content="",
                        search_query=query,
                        collected_at=datetime.now().isoformat()
                    )
                    articles.append(article)
            
            logger.info(f"Found {len(articles)} articles for query: {query}")
            return articles
            
        except Exception as e:
            logger.error(f"Error searching for news: {e}")
            raise
    
    
    def summarize_article(self, article: NewsArticle) -> str:
        """
        Generate a summary of an article using Langchain's ChatOpenAI.

        Args:
            article: NewsArticle object to summarize

        Returns:
            Summary text
        """
        try:
            if not article.content:
                return "No content available for summarization."

            # Truncate content if too long
            content_to_summarize = article.content

            # Prepare prompt
            prompt = open("prompts/news_summary.md", "r").read()

            # Use ChatOpenAI `from Langchain
            chat = ChatOpenAI(model_name=env.LLM_NAME, temperature=0)

            response = chat([
                HumanMessage(content=prompt.format(title=article.title, article_content=content_to_summarize))
            ])

            summary = response.content.strip()
            logger.info(f"Generated summary for article: {article.title[:50]}...")
            return summary

        except Exception as e:
            logger.error(f"Error summarizing article: {e}")
            return f"Error generating summary: {str(e)}"
        
    def summarize_all_articles(self, articles: List[NewsArticle]) -> List[str]:
        """
        Summarize all the articles.
        """
        summaries = [self.summarize_article(article) for article in articles]
        summaries = "\n\n".join(summaries)
        return summaries
    
    def analyze_sentiment(self, summaries: str, mode: str = "company", target_name: str = "Company") -> tuple[int, str]:
        """
        Analyze sentiment using ChatOpenAI (LangChain), based on company or sector mode.

        Args:
            text: all the summary text to analyze.
            mode: "company" or "sector" to determine the prompt template.
            target_name: Name of the company or sector.

        Returns:
            Tuple of (sentiment_score, source_type)
        """
        try:
            # Choose system prompt based on mode
            if mode == "company":
                system_prompt = open("prompts/news_sentiment_company.md", "r").read()
                user_prompt = f"Company Name: {target_name}\nSummary: {summaries}"

            elif mode == "sector":
                system_prompt = open("prompts/news_sentiment_sector.md", "r").read()
                user_prompt = f"Sector: {target_name}\nSummaries list: {summaries}"

            else:
                raise ValueError(f"Invalid mode '{mode}'. Use 'company' or 'sector'.")

            # Create ChatOpenAI instance (if not passed externally)
            chat = ChatOpenAI(model_name="gpt-4o", temperature=0.1)

            # Call the model
            response = chat([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            response_text = response.content.strip()
            logger.info(f"Raw sentiment response: {response_text}")


            return response_text, mode

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return "Error analyzing sentiment", mode
        
    def get_stock_sentiment(self, company_name: str) -> str:
        """
        Given the name of the company, get the articles, perform the summaries then get the 2 sentiment scores, one for the company and one for the sector.
        """

        # search for stock articles 
        articles = self.search_news(company_name)
        summaries = self.summarize_all_articles(articles)
        # perform sentiment analysis 
        company_sentiment, mode = self.analyze_sentiment(summaries, mode="company", target_name=company_name)
        sector_sentiment, mode = self.analyze_sentiment(summaries, mode="sector", target_name=company_name)
        return company_sentiment, sector_sentiment

