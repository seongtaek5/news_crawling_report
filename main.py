"""
Main script for collecting financial news from Yahoo Finance and Naver News
"""
import os
from datetime import datetime
import logging
from typing import List, Dict

from crawlers import YahooFinanceCrawler, NaverNewsCrawler
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_news_to_file(news_list: List[Dict], filename: str):
    """
    Save collected news to a text file
    
    Args:
        news_list: List of news articles
        filename: Output filename
    """
    try:
        # Ensure output directory exists
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        filepath = os.path.join(config.OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Financial News Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Articles: {len(news_list)}\n")
            f.write("=" * 80 + "\n\n")
            
            for news in news_list:
                f.write(f"[Date: {news['date']}]\n")
                f.write(f"[Title: {news['title']}]\n")
                f.write(f"[Source: {news['source']}]\n")
                if news.get('url'):
                    f.write(f"[URL: {news['url']}]\n")
                f.write(f"[Content: {news['content']}]\n")
                f.write("-" * 80 + "\n\n")
        
        logger.info(f"Successfully saved {len(news_list)} articles to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error saving news to file: {str(e)}")
        return None


def collect_yahoo_news(crawler: YahooFinanceCrawler) -> List[Dict]:
    """
    Collect news from Yahoo Finance
    
    Args:
        crawler: YahooFinanceCrawler instance
    
    Returns:
        List of news articles
    """
    all_news = []
    
    # Get market news
    logger.info("Collecting Yahoo Finance market news...")
    market_news = crawler.get_market_news()
    all_news.extend(market_news)
    
    # Get ticker-specific news
    logger.info(f"Collecting news for tickers: {config.YAHOO_TICKERS}")
    for ticker in config.YAHOO_TICKERS:
        ticker_news = crawler.get_news_for_ticker(ticker)
        all_news.extend(ticker_news)
    
    logger.info(f"Total Yahoo Finance articles collected: {len(all_news)}")
    return all_news


def collect_naver_news(crawler: NaverNewsCrawler) -> List[Dict]:
    """
    Collect news from Naver Finance
    
    Args:
        crawler: NaverNewsCrawler instance
    
    Returns:
        List of news articles
    """
    all_news = []
    
    # Get general finance news
    logger.info("Collecting Naver finance news...")
    finance_news = crawler.get_finance_news(max_pages=5)
    all_news.extend(finance_news)
    
    # If API credentials are available, search for specific topics
    if config.NAVER_CLIENT_ID and config.NAVER_CLIENT_SECRET:
        logger.info("Using Naver API to search for additional news...")
        search_queries = ['주식 시장', '증권', '경제', '금융']
        for query in search_queries:
            api_news = crawler.search_news_api(query, max_results=50)
            all_news.extend(api_news)
    
    logger.info(f"Total Naver articles collected: {len(all_news)}")
    return all_news


def remove_duplicates(news_list: List[Dict]) -> List[Dict]:
    """
    Remove duplicate news articles based on title similarity
    
    Args:
        news_list: List of news articles
    
    Returns:
        Deduplicated list
    """
    seen_titles = set()
    unique_news = []
    
    for news in news_list:
        # Use lowercase title for comparison
        title_key = news['title'].lower().strip()
        
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(news)
    
    logger.info(f"Removed {len(news_list) - len(unique_news)} duplicate articles")
    return unique_news


def sort_news_by_date(news_list: List[Dict]) -> List[Dict]:
    """
    Sort news articles by date (newest first)
    
    Args:
        news_list: List of news articles
    
    Returns:
        Sorted list
    """
    try:
        return sorted(
            news_list,
            key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M'),
            reverse=True
        )
    except Exception as e:
        logger.warning(f"Error sorting news: {str(e)}")
        return news_list


def main():
    """
    Main function to collect and save financial news
    """
    logger.info("=" * 80)
    logger.info("Starting Financial News Collection")
    logger.info("=" * 80)
    
    # Initialize crawlers
    yahoo_crawler = YahooFinanceCrawler(
        user_agent=config.USER_AGENT,
        time_window_hours=config.TIME_WINDOW_HOURS
    )
    
    naver_crawler = NaverNewsCrawler(
        user_agent=config.USER_AGENT,
        time_window_hours=config.TIME_WINDOW_HOURS,
        client_id=config.NAVER_CLIENT_ID,
        client_secret=config.NAVER_CLIENT_SECRET
    )
    
    # Collect news
    all_news = []
    
    try:
        # Yahoo Finance
        yahoo_news = collect_yahoo_news(yahoo_crawler)
        all_news.extend(yahoo_news)
    except Exception as e:
        logger.error(f"Error collecting Yahoo news: {str(e)}")
    
    try:
        # Naver Finance
        naver_news = collect_naver_news(naver_crawler)
        all_news.extend(naver_news)
    except Exception as e:
        logger.error(f"Error collecting Naver news: {str(e)}")
    
    # Process collected news
    logger.info(f"Total articles collected: {len(all_news)}")
    
    if not all_news:
        logger.warning("No news articles collected!")
        return
    
    # Remove duplicates
    all_news = remove_duplicates(all_news)
    
    # Sort by date
    all_news = sort_news_by_date(all_news)
    
    # Save to file
    today = datetime.now().strftime('%Y%m%d')
    filename = f"{config.LOG_FILE_PREFIX}_{today}.txt"
    
    saved_path = save_news_to_file(all_news, filename)
    
    if saved_path:
        logger.info("=" * 80)
        logger.info(f"News collection completed successfully!")
        logger.info(f"Output file: {saved_path}")
        logger.info(f"Total unique articles: {len(all_news)}")
        logger.info("=" * 80)
    else:
        logger.error("Failed to save news to file")


if __name__ == '__main__':
    main()
