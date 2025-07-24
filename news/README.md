# News Collator Module

This module provides a comprehensive news collection and analysis system using Exa AI for news search and OpenAI for summarization and sentiment analysis.

## Features

- **News Search**: Search for news articles about specific stocks using Exa AI
- **Article Summarization**: Generate concise summaries of news articles using OpenAI
- **Sentiment Analysis**: Analyze the sentiment of news summaries
- **Data Storage**: Save results in JSON and CSV formats
- **Flexible Configuration**: Customize search parameters, time periods, and domain filters

## Setup

### 1. Install Dependencies

First, install the required dependencies:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install exa-py openai pandas python-dotenv
```

### 2. Set Up API Keys

You'll need API keys for both Exa AI and OpenAI:

#### Exa AI API Key
1. Sign up at [Exa AI](https://exa.ai)
2. Get your API key from the dashboard
3. Set the environment variable:
```bash
export EXA_API_KEY='your_exa_api_key_here'
```

#### OpenAI API Key
1. Sign up at [OpenAI](https://platform.openai.com)
2. Get your API key from the dashboard
3. Set the environment variable:
```bash
export OPENAI_API_KEY='your_openai_api_key_here'
```

### 3. Environment Variables

Create a `.env` file in your project root (optional):

```env
EXA_API_KEY=your_exa_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Basic Usage

```python
from news_collator import NewsCollator

# Initialize the collator
collator = NewsCollator()

# Collect and process news for a stock
articles = collator.collect_and_process_news(
    stock_symbol="AAPL",
    num_results=10,
    time_period="7d"
)

# Print results
for article in articles:
    print(f"Title: {article.title}")
    print(f"Sentiment: {article.sentiment} (score: {article.sentiment_score})")
    print(f"Summary: {article.summary}")
    print("-" * 50)
```

### Advanced Usage

```python
from news_collator import NewsCollator

# Initialize with custom API keys
collator = NewsCollator(
    exa_api_key="your_exa_key",
    openai_api_key="your_openai_key"
)

# Search with specific parameters
articles = collator.search_news(
    query="AAPL stock news",
    num_results=15,
    time_period="30d",
    include_domains=["reuters.com", "bloomberg.com"],
    exclude_domains=["twitter.com", "facebook.com"]
)

# Process articles (summarize and analyze sentiment)
processed_articles = collator.process_articles(articles)

# Save results
collator.save_to_json("apple_news.json")
collator.save_to_csv("apple_news.csv")

# Get sentiment summary
summary = collator.get_sentiment_summary()
print(f"Average sentiment score: {summary['average_sentiment_score']}")
```

### Running the Example

```bash
# Make sure your API keys are set
export EXA_API_KEY='your_key_here'
export OPENAI_API_KEY='your_key_here'

# Run the example
python news/example_usage.py
```

## API Reference

### NewsCollator Class

#### Constructor
```python
NewsCollator(exa_api_key=None, openai_api_key=None)
```

#### Methods

##### `search_news(query, num_results=10, time_period="7d", include_domains=None, exclude_domains=None)`
Search for news articles using Exa AI.

**Parameters:**
- `query` (str): Search query
- `num_results` (int): Number of results to return
- `time_period` (str): Time period for search ("1d", "7d", "30d", etc.)
- `include_domains` (List[str]): Domains to include
- `exclude_domains` (List[str]): Domains to exclude

**Returns:** List of NewsArticle objects

##### `summarize_article(article)`
Generate a summary of an article using OpenAI.

**Parameters:**
- `article` (NewsArticle): Article to summarize

**Returns:** Summary text (str)

##### `analyze_sentiment(text)`
Analyze sentiment of text using OpenAI.

**Parameters:**
- `text` (str): Text to analyze

**Returns:** Tuple of (sentiment_label, sentiment_score)

##### `collect_and_process_news(stock_symbol, num_results=10, time_period="7d", include_domains=None, exclude_domains=None)`
Complete workflow: search, summarize, and analyze sentiment.

**Parameters:**
- `stock_symbol` (str): Stock symbol to search for
- `num_results` (int): Number of articles to collect
- `time_period` (str): Time period for search
- `include_domains` (List[str]): Domains to include
- `exclude_domains` (List[str]): Domains to exclude

**Returns:** List of processed NewsArticle objects

##### `save_to_json(filename)`
Save collected articles to a JSON file.

##### `save_to_csv(filename)`
Save collected articles to a CSV file.

##### `get_sentiment_summary()`
Get a summary of sentiment analysis results.

**Returns:** Dictionary with sentiment statistics

### NewsArticle Data Class

```python
@dataclass
class NewsArticle:
    title: str
    url: str
    published_date: Optional[str]
    content: str
    source: str
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    search_query: Optional[str] = None
    collected_at: Optional[str] = None
```

## Configuration Options

### Time Periods
- `"1d"`: Last 24 hours
- `"7d"`: Last 7 days
- `"30d"`: Last 30 days
- `"90d"`: Last 90 days

### Domain Filtering
You can include or exclude specific domains:

```python
# Include only specific news sources
include_domains=["reuters.com", "bloomberg.com", "cnbc.com"]

# Exclude social media
exclude_domains=["twitter.com", "facebook.com", "instagram.com"]
```

### Sentiment Analysis
The sentiment analysis returns:
- **Sentiment Label**: "positive", "negative", or "neutral"
- **Sentiment Score**: Float between 0.0 (very negative) and 1.0 (very positive)

## Error Handling

The NewsCollator includes comprehensive error handling:

- API key validation
- Network error handling
- Content extraction fallbacks
- Graceful degradation when articles can't be processed

## Cost Considerations

### Exa AI Costs
- Search API: ~$0.01 per search
- Content extraction: ~$0.01 per article

### OpenAI Costs
- GPT-3.5-turbo: ~$0.002 per 1K tokens
- Typical cost per article: $0.01-0.03

**Estimated total cost per 10 articles: $0.20-0.50**

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure both API keys are set correctly
   - Check that the keys are valid and have sufficient credits

2. **No Articles Found**
   - Try a different stock symbol
   - Adjust the time period
   - Remove domain restrictions

3. **Rate Limiting**
   - The class includes automatic retry logic
   - Consider reducing the number of articles if hitting limits

4. **Content Extraction Failures**
   - Some articles may not have extractable content
   - The class will still save basic article information

## Example Output

```json
{
  "title": "Apple Reports Strong Q4 Earnings",
  "url": "https://example.com/apple-earnings",
  "published_date": "2024-01-15",
  "content": "Apple Inc. reported strong fourth-quarter earnings...",
  "source": "Reuters",
  "summary": "Apple reported Q4 earnings that exceeded analyst expectations...",
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "search_query": "AAPL stock news",
  "collected_at": "2024-01-15T10:30:00"
}
```

## Contributing

Feel free to submit issues and enhancement requests! 