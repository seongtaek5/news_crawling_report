"""
Configuration file for News Crawling Report
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID', '')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET', '')

# Crawling Settings
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Time Settings
TIME_WINDOW_HOURS = 24  # Collect news from last 24 hours

# Yahoo Finance Settings
YAHOO_TICKERS = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']  # Example tickers
YAHOO_BASE_URL = 'https://finance.yahoo.com/quote/{}/news'

# Naver News Settings
NAVER_NEWS_BASE_URL = 'https://finance.naver.com/news/news_list.naver'
NAVER_STOCK_NEWS_URL = 'https://finance.naver.com/item/news.naver?code={}'

# Output Settings
OUTPUT_DIR = 'output'
LOG_FILE_PREFIX = 'news_log'
PROCESSED_FILE_PREFIX = 'processed_news'

# OpenAI Settings
OPENAI_MODEL = 'gpt-4o'
OPENAI_MAX_TOKENS = 4000
OPENAI_TEMPERATURE = 0.1  # Low temperature for consistent output
