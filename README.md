# FinBro Data Prep

A comprehensive financial data preparation and analysis system that combines financial fundamentals, news sentiment analysis, AI-powered stock rating, and advanced stock screening to provide actionable investment insights.

## 🎯 Overview

This system provides end-to-end financial analysis capabilities:
- **Financial Data Collection**: Gather comprehensive financial metrics and ratios
- **News Sentiment Analysis**: Analyze company and sector-specific sentiment from news sources
- **AI-Powered Stock Rating**: Generate stock ratings using OpenAI's ChatOpenAI
- **Advanced Stock Screening**: Find investment opportunities using proven strategies (Value, Growth, Dividend, Momentum)
- **Modular Architecture**: Clean, maintainable codebase with separate modules for each component

## 🏗️ Architecture

```
finbrodataprep/
├── fundamentals/          # Financial data collection
│   ├── __init__.py       # Module initialization
│   ├── alphavantage.py   # AlphavantageFinancialDataGatherer class
│   └── fmp.py           # FMPFinancialDataGatherer class
├── news_sentiment/       # News and sentiment analysis
│   └── news_collator.py  # SentimentCollator class
├── ratings/              # Stock rating system
│   └── rater.py         # StockRater class
├── screening/            # Stock screening system
│   └── finviz.py        # FinvizScreener class for live stock screening
├── pipelines/            # Complete analysis pipeline
│   └── pipelines.py     # StockAnalysisPipeline class
├── tests/                # Test suite
│   ├── test_alphavantage.py    # AlphaVantage tests
│   ├── test_basic.py           # Basic functionality tests
│   ├── test_finviz_screener.py # Finviz screener integration tests
│   └── main_tests.py           # Main application tests
├── prompts/              # AI prompt templates
│   ├── news_sentiment_company.md
│   ├── news_sentiment_sector.md
│   ├── news_summary.md
│   └── stock_rating.md
├── utils/                # Configuration and utilities
│   └── config.py        # Environment configuration
├── analysis_results/     # Exported analysis results
├── findata/              # Data storage (SQLite databases)
├── test_results/         # Test results and screening outputs
├── logs/                 # Application logs
├── main.py              # Main CLI entry point
├── run_tests.py         # Test runner script
└── pyproject.toml       # Dependencies and project config
```

## 🚀 Features

### 📊 Financial Data Collection
- **Multiple Data Sources**: Alpha Vantage and Financial Modeling Prep (FMP) integration
- **Comprehensive Metrics**: EPS, Net Income, ROE, ROA, Debt-to-Equity, Current Ratio
- **Cash Flow Analysis**: Operating Cash Flow, Free Cash Flow, Capital Expenditures
- **Balance Sheet Items**: Assets, Liabilities, Shareholder Equity, Inventory
- **Growth Trends**: Quarter-over-quarter and year-over-year percentage changes
- **Financial Ratios**: Book Value per Share, Quick Ratio, Leverage Ratio
- **Standardized Units**: Automatic unit conversion (millions for USD amounts)
- **Error Handling**: Comprehensive logging and exception handling
- **Data Filtering**: Latest 4 quarters of financial data

### 📰 News Sentiment Analysis
- **Multi-Source News**: Exa AI, Tavily, and DuckDuckGo integration
- **Company-Specific Analysis**: Targeted sentiment for individual companies
- **Sector-Wide Analysis**: Broader industry sentiment assessment
- **AI-Powered Summaries**: Automated article summarization
- **Sentiment Scoring**: -5 to +5 scale with detailed reasoning

### 🎯 AI Stock Rating System
- **Five Rating Levels**: Strong Buy, Buy, Hold, Sell, Strong Sell
- **Confidence Scoring**: 0.0 to 1.0 confidence for each rating
- **Comprehensive Analysis**: Detailed reasoning, key factors, and risk factors
- **Batch Processing**: Rate multiple stocks efficiently
- **Error Handling**: Robust fallback mechanisms

### 📈 Advanced Stock Screening
- **Live Market Data**: Real-time screening from Finviz using web scraping
- **Multiple Strategies**: Value, Growth, Dividend, Momentum, and custom screens
- **Proven Investment Approaches**: Warren Buffett, Peter Lynch, and Dividend Aristocrat styles
- **Comprehensive Filtering**: P/E ratios, ROE, debt levels, growth rates, dividend yields
- **Export Capabilities**: CSV and SQLite exports for further analysis
- **Batch Processing**: Screen hundreds of stocks across multiple pages
- **Dynamic Column Detection**: Automatically handles different Finviz table formats

### 🔄 Complete Analysis Pipeline
- **End-to-End Workflow**: Single function call for complete analysis
- **Multi-Component Integration**: Combines financial data, sentiment, and rating
- **Batch Processing**: Analyze multiple stocks efficiently
- **Export Capabilities**: Save detailed analysis to files
- **Error Handling**: Graceful failure handling with detailed error reporting

## 📦 Installation

### Prerequisites
- Python 3.13+
- API keys for financial data, news sources, and OpenAI

### Setup
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd finbrodataprep
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Install test dependencies** (optional):
   ```bash
   uv sync --extra test
   ```

4. **Configure environment**:
   Create a `config` file with your API keys:
   ```bash
   # Alpha Vantage API (for financial data)
   ALPHAVANTAGE_API_KEY=your_alphavantage_api_key
   
   # Financial Modeling Prep API (alternative financial data source)
   FMP_API_KEY=your_fmp_api_key
   
   # News and search APIs
   EXA_API_KEY=your_exa_api_key
   TAVILY_API_KEY=your_tavily_api_key
   
   # OpenAI API
   LLM_API_KEY=your_openai_api_key
   LLM_NAME=gpt-4o
   ```

## 🔧 Usage

### Quick Start with Pipeline

The easiest way to use the system is through the comprehensive pipeline:

```bash
# Analyze a single stock
python main.py analyze AAPL

# Analyze and export to file
python main.py analyze AAPL --export

# Analyze with custom output file
python main.py analyze AAPL -o my_analysis.txt

# Analyze multiple stocks
python main.py batch AAPL MSFT GOOGL

# Analyze multiple stocks with export directory
python main.py batch AAPL MSFT --export-dir ./analyses

# Get quick financial info
python main.py info AAPL

# Show example commands
python main.py list-examples
```

### Stock Screening Usage

Find investment opportunities using proven screening strategies:

```python
from screening.finviz import FinvizScreener, ScreeningStrategies

# Initialize the screener
screener = FinvizScreener()

# Quality Growth Screen (based on your Finviz URL parameters)
results_df = screener.quality_growth_screen()
top_stocks = screener.get_top_stocks(10)

# Print results
for i, stock in enumerate(top_stocks, 1):
    ticker = stock['Ticker']
    price = stock['Price'] 
    change = stock['Change']
    print(f"{i}. {ticker}: ${price} ({change})")

# Export results
screener.export_results("quality_growth_stocks", "csv")

# Dividend Growth Screen
div_results = screener.dividend_growth_screen(min_yield=2.5)

# Value Screen
value_results = screener.value_screen()

# Momentum Screen  
momentum_results = screener.momentum_screen()

# Warren Buffett Style
buffett_filters = ScreeningStrategies.warren_buffett_style()
buffett_results = screener.custom_screen(buffett_filters, table='Valuation')

# Peter Lynch Style
lynch_filters = ScreeningStrategies.peter_lynch_style()  
lynch_results = screener.custom_screen(lynch_filters, table='Performance')

# Get screening summary
summary = screener.get_screening_summary()
print(f"Found {summary['total_stocks']} stocks")
```

### Programmatic Usage

```python
from pipelines.pipelines import StockAnalysisPipeline

# Initialize the pipeline
pipeline = StockAnalysisPipeline()

# Analyze a single stock
result = pipeline.analyze_stock("AAPL")

if result.success:
    print(f"Rating: {result.rating_result.rating.value}")
    print(f"Confidence: {result.rating_result.confidence:.1%}")
    
    # Get detailed summary
    summary = pipeline.get_analysis_summary(result)
    print(summary)
    
         # Export to file
     pipeline.export_analysis_to_file(result, "analysis.txt")
 ```

### Testing

Run the test suite to ensure everything is working correctly:

```bash
# Run all tests
python run_tests.py

# Run tests with coverage
python run_tests.py --verbose

# Run specific test
python run_tests.py --test TestAnalyzeCommand::test_analyze_success

# List all tests
python run_tests.py --list

# Run tests without coverage
python run_tests.py --no-coverage
```

### Individual Components

#### Financial Data Collection
```python
# Using Alpha Vantage data source
from fundamentals.alphavantage import AlphavantageFinancialDataGatherer

gatherer = AlphavantageFinancialDataGatherer()
financial_data = gatherer.from_stock_to_dataframe("AAPL")
print(financial_data)  # Pandas DataFrame with financial metrics and units

# Using FMP data source (alternative)
from fundamentals.fmp import FMPFinancialDataGatherer

fmp_gatherer = FMPFinancialDataGatherer()
fmp_data = fmp_gatherer.from_stock_to_dataframe("AAPL")
```

#### News Sentiment Analysis
```python
from news_sentiment.news_collator import SentimentCollator

collator = SentimentCollator()
company_sentiment, sector_sentiment = collator.get_stock_sentiment("AAPL")
print(f"Company: {company_sentiment}")
print(f"Sector: {sector_sentiment}")
```

#### Stock Rating
```python
from ratings.rater import StockRater

rater = StockRater()
result = rater.rate_stock(
    financial_data_html=financial_data,
    company_sentiment=company_sentiment,
    sector_sentiment=sector_sentiment,
    company_name="AAPL"
)
print(result.rating.value)  # "Strong Buy", "Buy", etc.
```

## 📊 Data Sources

### Financial Data
- **Alpha Vantage**: Primary source for earnings, income statements, balance sheets, and cash flow data
- **Financial Modeling Prep (FMP)**: Alternative comprehensive financial data provider
- **financetoolkit**: Financial ratios and metrics calculation library
- **yfinance**: Real-time stock data and historical prices
- **financedatabase**: Company information and sector data

### News Sources
- **Exa AI**: High-quality news content extraction
- **Tavily**: Web search and content discovery
- **DuckDuckGo**: Additional search capabilities

### AI Analysis
- **OpenAI GPT-4o**: Advanced language model for analysis
- **LangChain**: Framework for LLM interactions

## 🎯 Rating Criteria

The system analyzes multiple factors to provide comprehensive stock ratings:

### Financial Health Indicators
- **Earnings Per Share (EPS)**: Growth trends and stability
- **Net Income**: Profitability and growth patterns
- **Return on Equity (ROE)**: Capital efficiency
- **Return on Assets (ROA)**: Asset utilization
- **Debt-to-Equity Ratio**: Financial leverage
- **Current Ratio**: Liquidity assessment
- **Cash Flow Metrics**: Operating and free cash flow
- **Book Value per Share**: Asset valuation

### Market Sentiment
- **Company-Specific News**: Recent developments and announcements
- **Sector Trends**: Industry-wide sentiment and outlook
- **Market Positioning**: Competitive landscape analysis

### Rating Scale
- **Strong Buy**: Exceptional fundamentals, strong positive sentiment
- **Buy**: Good fundamentals, positive sentiment, favorable outlook
- **Hold**: Mixed signals, neutral sentiment, wait for direction
- **Sell**: Concerning fundamentals, negative sentiment
- **Strong Sell**: Poor fundamentals, very negative sentiment

## 🔧 Configuration

### Environment Variables
```bash
# Required for financial data
ALPHAVANTAGE_API_KEY=your_alphavantage_api_key
FMP_API_KEY=your_fmp_api_key

# Required for news analysis
EXA_API_KEY=your_exa_api_key
TAVILY_API_KEY=your_tavily_api_key

# Required for AI analysis
LLM_API_KEY=your_openai_api_key
LLM_NAME=gpt-4o
```

### Prompt Customization
All AI prompts are stored in the `prompts/` directory and can be customized:
- `prompts/stock_rating.md`: Main stock rating analysis prompt
- `prompts/news_sentiment_company.md`: Company-specific sentiment analysis
- `prompts/news_sentiment_sector.md`: Sector-wide sentiment analysis
- `prompts/news_summary.md`: News article summarization

## 🧪 Testing

The project includes comprehensive tests for all components:

```bash
# Run all tests with coverage
python run_tests.py

# Run specific test class
python run_tests.py --test TestAlphavantageFinancialDataGatherer

# Run tests verbosely
python run_tests.py --verbose

# List all available tests
python run_tests.py --list

# Run without coverage report
python run_tests.py --no-coverage

# Test the Finviz screener with real data
uv run python -m pytest tests/test_finviz_screener.py -v -s
```

### Test Structure
- `tests/test_alphavantage.py`: Tests for Alpha Vantage financial data gatherer
- `tests/test_basic.py`: Basic functionality tests
- `tests/test_finviz_screener.py`: Integration tests for Finviz screener with real data
- `tests/main_tests.py`: Main application and CLI tests

## 📈 Example Output

### Stock Analysis Example
```
STOCK RATING SUMMARY
===================

Rating: Buy
Confidence: 85.0%

REASONING:
Apple demonstrates strong financial fundamentals with consistent EPS growth of 12% 
year-over-year, robust ROE of 15.2%, and healthy cash flow generation. The company 
benefits from strong brand loyalty and diversified revenue streams across hardware, 
services, and wearables. Recent sentiment analysis shows positive momentum in both 
company-specific news and broader technology sector trends.

KEY POSITIVE FACTORS:
• Strong EPS growth and profitability metrics
• Robust cash flow generation and financial health
• Positive sentiment in both company and sector news
• Diversified revenue streams and strong brand value

RISK FACTORS:
• Potential supply chain disruptions
• Regulatory scrutiny in key markets
• Intense competition in smartphone market
• Economic sensitivity to consumer spending

RECOMMENDATION:
Apple presents a favorable investment opportunity with strong fundamentals and positive 
market sentiment. The company's diversified business model and strong financial position 
support a Buy rating, though investors should monitor supply chain and regulatory risks.
```

### Stock Screening Example
```
🔍 Running Quality Growth Screen...
Successfully scraped 15 total stocks from 1 pages
✅ Found 15 quality growth stocks

📈 Top 5 Quality Growth Stocks:
1. ADBE: $341.05 (0.82%) P/E: 21.81
2. CHKP: $183.32 (-0.92%) P/E: 23.89
3. DOCU: $69.19 (-1.83%) P/E: 13.08
4. EXEL: $37.72 (0.88%) P/E: 18.09
5. FER: $52.50 (-0.30%) P/E: 10.41

📊 Exported CSV to: quality_growth_20250811_141539.csv

💰 Running Dividend Growth Screen...
✅ Found 19 dividend growth stocks

🎯 Running Warren Buffett Strategy Screen...
✅ Found 26 Buffett-style stocks

📈 Running Peter Lynch Strategy Screen...
✅ Found 211 Lynch-style stocks across 11 pages
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation in each module
2. Review the example usage files
3. Open an issue on GitHub

## 🔮 Roadmap

- [x] **Advanced Stock Screening**: Live market data screening with proven investment strategies ✅
- [ ] Real-time data streaming
- [ ] Portfolio optimization recommendations
- [ ] Risk assessment models
- [ ] Historical performance tracking
- [ ] API endpoints for web integration
- [ ] Mobile app support
- [ ] Additional screening sources integration (Yahoo Finance, Polygon.io)
- [ ] Enhanced logging and monitoring capabilities
- [ ] Data caching and performance optimization
- [ ] Automated screening schedules and alerts
- [ ] Portfolio backtesting with screening results
