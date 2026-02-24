"""
Yahoo Finance News Crawler
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
from typing import List, Dict


class YahooFinanceCrawler:
    """Crawler for Yahoo Finance news"""
    
    def __init__(self, user_agent: str, time_window_hours: int = 24):
        self.user_agent = user_agent
        self.time_window_hours = time_window_hours
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_news_for_ticker(self, ticker: str) -> List[Dict]:
        """
        Get news articles for a specific ticker
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        
        Returns:
            List of news articles with date, title, and content
        """
        try:
            # Yahoo Finance RSS feed for ticker news
            rss_url = f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US'
            
            logger.info(f"Fetching news for ticker: {ticker}")
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            news_list = []
            cutoff_time = datetime.now() - timedelta(hours=self.time_window_hours)
            
            for item in items:
                try:
                    # Extract basic info
                    title = item.find('title').text if item.find('title') else 'No Title'
                    link = item.find('link').text if item.find('link') else ''
                    pub_date_str = item.find('pubDate').text if item.find('pubDate') else ''
                    description = item.find('description').text if item.find('description') else ''
                    
                    # Parse publication date
                    if pub_date_str:
                        # Format: 'Thu, 24 Feb 2026 10:30:00 +0000' or 'GMT'
                        try:
                            # Try with timezone offset like +0000
                            pub_date = datetime.strptime(pub_date_str[:-6], '%a, %d %b %Y %H:%M:%S')
                        except:
                            # Fallback for other formats
                            try:
                                pub_date = datetime.strptime(pub_date_str.replace('GMT', '').strip(), '%a, %d %b %Y %H:%M:%S')
                            except:
                                continue
                    else:
                        continue
                    
                    # Filter by time window
                    if pub_date < cutoff_time:
                        continue
                    
                    # Try to get full article content
                    full_content = self._get_article_content(link)
                    if not full_content:
                        full_content = description
                    
                    news_list.append({
                        'date': pub_date.strftime('%Y-%m-%d %H:%M'),
                        'title': title,
                        'content': full_content,
                        'source': f'Yahoo Finance - {ticker}',
                        'url': link
                    })
                    
                    time.sleep(0.5)  # Polite crawling
                    
                except Exception as e:
                    logger.warning(f"Error parsing item for {ticker}: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_list)} articles for {ticker}")
            return news_list
            
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {str(e)}")
            return []
    
    def _get_article_content(self, url: str) -> str:
        """
        Fetch full article content from URL
        
        Args:
            url: Article URL
        
        Returns:
            Article content text
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Yahoo Finance article structure
            # Try multiple selectors
            article_body = None
            
            # Method 1: Look for article body
            article_body = soup.find('div', class_='caas-body')
            if not article_body:
                article_body = soup.find('div', {'class': re.compile('article.*body', re.I)})
            
            if not article_body:
                # Method 2: Look for paragraphs in article
                article_container = soup.find('article')
                if article_container:
                    article_body = article_container
            
            if article_body:
                # Extract text from paragraphs
                paragraphs = article_body.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                return content
            
            return ''
            
        except Exception as e:
            logger.debug(f"Could not fetch article content from {url}: {str(e)}")
            return ''
    
    def get_market_news(self) -> List[Dict]:
        """
        Get general market news
        
        Returns:
            List of news articles
        """
        try:
            # Yahoo Finance general news RSS
            rss_url = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US'
            
            logger.info("Fetching general market news")
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            news_list = []
            cutoff_time = datetime.now() - timedelta(hours=self.time_window_hours)
            
            for item in items:
                try:
                    title = item.find('title').text if item.find('title') else 'No Title'
                    link = item.find('link').text if item.find('link') else ''
                    pub_date_str = item.find('pubDate').text if item.find('pubDate') else ''
                    description = item.find('description').text if item.find('description') else ''
                    
                    if pub_date_str:
                        try:
                            # Try with timezone offset like +0000
                            pub_date = datetime.strptime(pub_date_str[:-6], '%a, %d %b %Y %H:%M:%S')
                        except:
                            # Fallback for other formats
                            try:
                                pub_date = datetime.strptime(pub_date_str.replace('GMT', '').strip(), '%a, %d %b %Y %H:%M:%S')
                            except:
                                continue
                    else:
                        continue
                    
                    if pub_date < cutoff_time:
                        continue
                    
                    full_content = self._get_article_content(link)
                    if not full_content:
                        full_content = description
                    
                    news_list.append({
                        'date': pub_date.strftime('%Y-%m-%d %H:%M'),
                        'title': title,
                        'content': full_content,
                        'source': 'Yahoo Finance - Market',
                        'url': link
                    })
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error parsing market news item: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_list)} market news articles")
            return news_list
            
        except Exception as e:
            logger.error(f"Error fetching market news: {str(e)}")
            return []
