#!/usr/bin/env python3
"""
Real integration test for SentimentCollator from news_collator.py

This test performs actual API calls (not mocked) and saves results for inspection.
Results are saved in a timestamped directory under test_results/
"""

import os
import json
import pytest
from datetime import datetime
from pathlib import Path
import sys

# Add the parent directory to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from news_sentiment.news_collator import SentimentCollator, NewsArticle


class TestSentimentCollatorReal:
    """Real integration tests for SentimentCollator (no mocks)"""
    
    @classmethod
    def setup_class(cls):
        """Set up test class - create results directory"""
        cls.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cls.results_dir = Path(__file__).parent.parent / "test_results" / f"sentiment_collator_{cls.timestamp}"
        cls.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize the collator
        try:
            cls.collator = SentimentCollator()
        except Exception as e:
            pytest.fail(f"Failed to initialize SentimentCollator: {e}")
    
    def save_result(self, filename: str, data, description: str = ""):
        """Helper method to save test results"""
        filepath = self.results_dir / filename
        
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], NewsArticle):
            # Convert NewsArticle objects to dictionaries for JSON serialization
            data_dict = {
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "count": len(data),
                "articles": [
                    {
                        "title": article.title,
                        "url": article.url,
                        "published_date": article.published_date,
                        "content_preview": article.content,
                        "content_length": len(article.content),
                        "summary": article.summary,
                        "sentiment": article.sentiment,
                        "sentiment_score": article.sentiment_score,
                        "search_query": article.search_query,
                        "collected_at": article.collected_at
                    }
                    for article in data
                ]
            }
        else:
            data_dict = {
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Results saved to: {filepath}")
        return filepath

    def test_search_news_real(self):
        """Test search_news method with real API calls"""
        test_company = "AAPL"  # Apple Inc - reliable for news
        
        print(f"\n🔍 Testing search_news for company: {test_company}")
        
        try:
            # Perform the actual search
            articles = self.collator.search_news(test_company)
            
            # Basic assertions
            assert isinstance(articles, list), "search_news should return a list"
            assert len(articles) > 0, "Should find at least some articles"
            
            # Check article structure
            for article in articles[:3]:  # Check first 3 articles
                assert isinstance(article, NewsArticle), "Each item should be a NewsArticle"
                assert article.title, "Article should have a title"
                assert article.url, "Article should have a URL"
                assert article.search_query, "Article should have search_query set"
                assert article.collected_at, "Article should have collected_at timestamp"
            
            # Save results for inspection
            self.save_result(
                "search_news_results.json",
                articles,
                f"Results from search_news() for company '{test_company}'. Found {len(articles)} articles."
            )
            
            # Save a detailed report
            report = {
                "test": "search_news",
                "company": test_company,
                "total_articles": len(articles),
                "articles_with_content": sum(1 for a in articles if a.content),
                "articles_without_content": sum(1 for a in articles if not a.content),
                "average_content_length": sum(len(a.content) for a in articles) / len(articles) if articles else 0,
                "unique_urls": len(set(a.url for a in articles)),
                "unique_titles": len(set(a.title for a in articles)),
                "sample_titles": [a.title for a in articles[:5]]
            }
            
            self.save_result(
                "search_news_report.json",
                report,
                f"Detailed analysis report for search_news() test"
            )
            
            print(f"✓ Found {len(articles)} articles for {test_company}")
            print(f"✓ {report['articles_with_content']} articles have content")
            print(f"✓ Average content length: {report['average_content_length']:.0f} characters")
            
            # Store articles for next test
            self.test_articles = articles
            
        except Exception as e:
            pytest.fail(f"search_news failed: {e}")

    def test_summarize_all_articles_real(self):
        """Test summarize_all_articles method with real API calls"""
        
        # Use articles from previous test, or get new ones
        if not hasattr(self, 'test_articles'):
            print("🔍 No articles from previous test, getting new ones...")
            self.test_articles = self.collator.search_news("MSFT")  # Microsoft as backup
        
        articles = self.test_articles[:3]  # Limit to first 3 to save API costs
        print(f"\n📝 Testing summarize_all_articles with {len(articles)} articles")
        
        try:
            # Test the summarize_all_articles method
            summarized_articles = self.collator.summarize_all_articles(articles)
            
            # The method now returns a list of NewsArticle objects with summaries
            assert isinstance(summarized_articles, list), "summarize_all_articles should return a list"
            assert len(summarized_articles) > 0, "Should return some summarized articles"
            
            # Extract summaries text for inspection
            summaries_text = []
            for article in summarized_articles:
                if isinstance(article, NewsArticle) and article.summary:
                    summaries_text.append(f"Title: {article.title}\nSummary: {article.summary}\n")
                elif isinstance(article, str):  # Handle error case
                    summaries_text.append(f"Error: {article}\n")
            
            combined_summaries = "\n".join(summaries_text)
            
            # Save the summaries
            summary_data = {
                "input_articles": [
                    {
                        "title": orig_article.title,
                        "url": orig_article.url,
                        "content_length": len(orig_article.content)
                    }
                    for orig_article in articles
                ],
                "summarized_articles": [
                    {
                        "title": article.title if hasattr(article, 'title') else "Unknown",
                        "summary": article.summary if hasattr(article, 'summary') else str(article),
                        "summary_length": len(article.summary) if hasattr(article, 'summary') and article.summary else 0
                    }
                    for article in summarized_articles
                ],
                "combined_summaries_length": len(combined_summaries),
                "combined_summaries_word_count": len(combined_summaries.split())
            }
            
            self.save_result(
                "summarize_all_articles_results.json",
                summary_data,
                f"Results from summarize_all_articles() for {len(articles)} articles"
            )
            
            # Also save just the text for easy reading
            with open(self.results_dir / "summaries_text.txt", 'w', encoding='utf-8') as f:
                f.write(f"Summaries for {len(articles)} articles\n")
                f.write("=" * 50 + "\n\n")
                f.write(combined_summaries)
            
            print(f"✓ Generated summaries with {len(combined_summaries.split())} words")
            print(f"✓ Total summary length: {len(combined_summaries)} characters")
            
            # Store summaries for potential sentiment analysis test
            self.test_summaries = combined_summaries
            
        except Exception as e:
            pytest.fail(f"summarize_all_articles failed: {e}")

    def test_full_workflow_real(self):
        """Test the complete workflow: search -> summarize -> analyze sentiment"""
        
        test_company = "NVDA"  # NVIDIA - often has news
        print(f"\n🔄 Testing full workflow for company: {test_company}")
        
        try:
            # Step 1: Search for news
            print("  Step 1: Searching for news...")
            articles = self.collator.search_news(test_company)
            
            # Limit articles to save API costs
            limited_articles = articles[:2]
            
            # Step 2: Summarize articles
            print("  Step 2: Summarizing articles...")
            summarized_articles = self.collator.summarize_all_articles(limited_articles)
            
            # Extract summaries text
            summaries_text = []
            for article in summarized_articles:
                if isinstance(article, NewsArticle) and article.summary:
                    summaries_text.append(article.summary)
                elif isinstance(article, str):
                    summaries_text.append(article)
            
            summaries = "\n\n".join(summaries_text)
            
            # Step 3: Analyze sentiment
            print("  Step 3: Analyzing sentiment...")
            company_sentiment, _ = self.collator.analyze_sentiment(summaries, mode="company", target_name=test_company)
            sector_sentiment, _ = self.collator.analyze_sentiment(summaries, mode="sector", target_name="Technology")
            
            # Create comprehensive workflow report
            workflow_results = {
                "company": test_company,
                "workflow_steps": {
                    "1_search": {
                        "total_articles_found": len(articles),
                        "articles_used": len(limited_articles),
                        "sample_titles": [a.title for a in limited_articles]
                    },
                    "2_summarize": {
                        "summaries_length": len(summaries),
                        "summaries_preview": summaries[:300] + "..." if len(summaries) > 300 else summaries
                    },
                    "3_sentiment": {
                        "company_sentiment": company_sentiment,
                        "sector_sentiment": sector_sentiment
                    }
                },
                "full_summaries": summaries
            }
            
            self.save_result(
                "full_workflow_results.json",
                workflow_results,
                f"Complete workflow test results for {test_company}"
            )
            
            print(f"✓ Complete workflow test successful")
            print(f"  - Found {len(articles)} articles")
            print(f"  - Used {len(limited_articles)} for processing")
            print(f"  - Generated {len(summaries)} characters of summaries")
            print(f"  - Company sentiment: {str(company_sentiment)[:100]}...")
            print(f"  - Sector sentiment: {str(sector_sentiment)[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Full workflow test failed: {e}")

    def test_generate_queries_real(self):
        """Test the generate_queries method with better error handling"""
        
        test_company = "TSLA"  # Tesla
        print(f"\n🔍 Testing generate_queries for company: {test_company}")
        
        try:
            # Test context search first
            print("  Testing context search...")
            context = self.collator.context_search(test_company + " company")
            print(f"  ✓ Context search returned {len(context)} characters")
            
            # Now test query generation
            print("  Testing query generation...")
            queries = self.collator.generate_queries(test_company)
            
            # Basic assertions
            assert isinstance(queries, list), "generate_queries should return a list"
            assert len(queries) > 0, "Should generate at least one query"
            
            # Save the generated queries
            query_data = {
                "company": test_company,
                "context_preview": context[:500] + "..." if len(context) > 500 else context,
                "generated_queries": queries,
                "query_count": len(queries)
            }
            
            self.save_result(
                "generate_queries_results.json",
                query_data,
                f"Generated queries for {test_company}"
            )
            
            print(f"✓ Generated {len(queries)} queries for {test_company}")
            for i, query in enumerate(queries, 1):
                print(f"  {i}. {query}")
                
        except json.JSONDecodeError as e:
            # Capture the actual response that failed to parse
            error_data = {
                "company": test_company,
                "error": "JSON decode error",
                "error_message": str(e),
                "possible_causes": [
                    "OpenAI API rate limiting",
                    "LLM returned non-JSON response",
                    "API authentication issues"
                ]
            }
            
            self.save_result(
                "generate_queries_error.json",
                error_data,
                f"JSON parsing error for {test_company}"
            )
            
            print(f"❌ JSON parsing failed: {e}")
            print("This could be due to:")
            print("  - API rate limiting")
            print("  - LLM not returning valid JSON")
            print("  - API authentication issues")
            
            pytest.fail(f"generate_queries failed with JSON decode error: {e}")
                
        except Exception as e:
            # General error handling
            error_data = {
                "company": test_company,
                "error": "General exception",
                "error_message": str(e),
                "error_type": type(e).__name__
            }
            
            self.save_result(
                "generate_queries_error.json",
                error_data,
                f"General error for {test_company}"
            )
            
            pytest.fail(f"generate_queries failed: {e}")

    @classmethod
    def teardown_class(cls):
        """Print final summary"""
        print(f"\n📊 Test Results Summary")
        print("=" * 50)
        print(f"All results saved in: {cls.results_dir}")
        print("\nGenerated files:")
        
        if cls.results_dir.exists():
            for file in sorted(cls.results_dir.glob("*.json")):
                print(f"  - {file.name}")
            for file in sorted(cls.results_dir.glob("*.txt")):
                print(f"  - {file.name}")
        
        print(f"\nTo inspect results, check the files in:")
        print(f"  {cls.results_dir}")


if __name__ == "__main__":
    # Run the tests directly
    pytest.main([__file__, "-v", "-s"])