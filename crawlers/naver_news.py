"""
Naver News Crawler for Financial News
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NaverNewsCrawler:
    """Crawler for Naver Finance News"""
    
    def __init__(self, user_agent: str, time_window_hours: int = 24,
                 client_id: str = '', client_secret: str = ''):
        self.user_agent = user_agent
        self.time_window_hours = time_window_hours
        self.client_id = client_id
        self.client_secret = client_secret
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_finance_news(self, max_pages: int = 5) -> List[Dict]:
        """
        Get general finance news from Naver
        
        Args:
            max_pages: Maximum number of pages to crawl
        
        Returns:
            List of news articles
        """
        news_list = []
        cutoff_time = datetime.now() - timedelta(hours=self.time_window_hours)
        
        try:
            for page in range(1, max_pages + 1):
                url = f'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258&page={page}'
                
                logger.info(f"Fetching Naver finance news page {page}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find news items in dl structure
                news_items = soup.select('dd.articleSubject')
                
                for item in news_items:
                    try:
                        # Extract title and link
                        link_tag = item.find('a')
                        if not link_tag:
                            continue
                        
                        title = link_tag.get_text(strip=True)
                        article_url_path = link_tag.get('href', '')
                        
                        if not article_url_path:
                            continue
                        
                        article_url = f'https://finance.naver.com{article_url_path}'
                        
                        # Get date from previous dt tag
                        dt_tag = item.find_previous_sibling('dt')
                        date_str = ''
                        if dt_tag:
                            dt_text = dt_tag.get_text(strip=True)
                            # Format: "02.24" or similar
                            try:
                                # Assume current year and month
                                now = datetime.now()
                                date_obj = datetime.strptime(f"{now.year}.{dt_text}", "%Y.%m.%d")
                                date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                            except:
                                date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
                        
                        if not date_str:
                            date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
                        
                        # Check time filter
                        try:
                            article_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
                            if article_date < cutoff_time:
                                logger.info(f"Reached articles older than {self.time_window_hours} hours")
                                return news_list
                        except:
                            pass
                        
                        # Get full article content
                        article_data = self._get_article_details(article_url)
                        content = article_data.get('content', '') if article_data else ''
                        
                        news_list.append({
                            'date': date_str,
                            'title': title,
                            'content': content,
                            'source': 'Naver Finance',
                            'url': article_url
                        })
                        
                        time.sleep(0.3)  # Polite crawling
                        
                    except Exception as e:
                        logger.warning(f"Error parsing news item: {str(e)}")
                        continue
                
                time.sleep(1)  # Delay between pages
            
            logger.info(f"Found {len(news_list)} Naver finance news articles")
            return news_list
            
        except Exception as e:
            logger.error(f"Error fetching Naver finance news: {str(e)}")
            return news_list
    
    def get_stock_news(self, stock_code: str, max_pages: int = 3) -> List[Dict]:
        """
        Get news for a specific stock
        
        Args:
            stock_code: Naver stock code (e.g., '005930' for Samsung)
            max_pages: Maximum number of pages to crawl
        
        Returns:
            List of news articles
        """
        news_list = []
        cutoff_time = datetime.now() - timedelta(hours=self.time_window_hours)
        
        try:
            for page in range(1, max_pages + 1):
                url = f'https://finance.naver.com/item/news_news.naver?code={stock_code}&page={page}'
                
                logger.info(f"Fetching news for stock {stock_code} page {page}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find news items in the table
                news_table = soup.find('table', class_='type5')
                if not news_table:
                    break
                
                news_items = news_table.select('tr')
                
                for item in news_items:
                    try:
                        # Skip header rows
                        if item.find('th'):
                            continue
                        
                        # Extract title and link
                        title_tag = item.find('a', class_='tit')
                        if not title_tag:
                            continue
                        
                        title = title_tag.get_text(strip=True)
                        article_href = title_tag.get('href', '')
                        
                        if not article_href:
                            continue
                        
                        article_url = f'https://finance.naver.com{article_href}'
                        
                        # Get article details
                        article_data = self._get_article_details(article_url)
                        
                        if not article_data:
                            continue
                        
                        # Add stock code to source
                        article_data['source'] = f"Naver Finance - Stock {stock_code}"
                        
                        # Check time filter
                        try:
                            article_date = datetime.strptime(article_data['date'], '%Y-%m-%d %H:%M')
                            if article_date < cutoff_time:
                                logger.info(f"Reached articles older than {self.time_window_hours} hours for {stock_code}")
                                return news_list
                        except:
                            continue
                        
                        news_list.append(article_data)
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing stock news item: {str(e)}")
                        continue
                
                time.sleep(1)
            
            logger.info(f"Found {len(news_list)} articles for stock {stock_code}")
            return news_list
            
        except Exception as e:
            logger.error(f"Error fetching news for stock {stock_code}: {str(e)}")
            return news_list
    
    def _get_article_details(self, url: str) -> Dict:
        """
        Get detailed article content
        
        Args:
            url: Article URL
        
        Returns:
            Dictionary with article details
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_tag = soup.select_one('strong.c.p15') or soup.select_one('strong.headlin')
            title = title_tag.get_text(strip=True) if title_tag else 'No Title'
            
            # Extract date
            date_tag = soup.select_one('span.article_date') or soup.select_one('span.tah')
            date_str = ''
            if date_tag:
                date_text = date_tag.get_text(strip=True)
                # Parse date (format: "2026.02.24 10:30")
                try:
                    date_obj = datetime.strptime(date_text, '%Y.%m.%d %H:%M')
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    # Try alternative format
                    try:
                        date_obj = datetime.strptime(date_text.split()[0], '%Y.%m.%d')
                        date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                    except:
                        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            if not date_str:
                date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # Extract content
            content_div = soup.select_one('#news_read') or soup.select_one('div.scr01')
            content = ''
            
            if content_div:
                # Remove scripts and styles
                for script in content_div(['script', 'style', 'iframe']):
                    script.decompose()
                
                # Get text from paragraphs or divs
                paragraphs = content_div.find_all(['p', 'div'])
                if paragraphs:
                    content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                else:
                    content = content_div.get_text(strip=True)
                
                # Clean up content
                content = re.sub(r'\s+', ' ', content)
                content = re.sub(r'(\n\s*)+', '\n\n', content)
            
            return {
                'date': date_str,
                'title': title,
                'content': content,
                'source': 'Naver Finance',
                'url': url
            }
            
        except Exception as e:
            logger.debug(f"Error getting article details from {url}: {str(e)}")
            return {}
    
    def search_news_api(self, query: str, max_results: int = 100) -> List[Dict]:
        """
        Search news using Naver Search API (requires API credentials)
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of news articles
        """
        if not self.client_id or not self.client_secret:
            logger.warning("Naver API credentials not provided, skipping API search")
            return []
        
        try:
            url = 'https://openapi.naver.com/v1/search/news.json'
            headers = {
                'X-Naver-Client-Id': self.client_id,
                'X-Naver-Client-Secret': self.client_secret
            }
            
            params = {
                'query': query,
                'display': min(max_results, 100),  # Max 100 per request
                'sort': 'date'
            }
            
            logger.info(f"Searching Naver News API for: {query}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            news_list = []
            cutoff_time = datetime.now() - timedelta(hours=self.time_window_hours)
            
            for item in data.get('items', []):
                try:
                    # Parse date (format: "Mon, 24 Feb 2026 10:30:00 +0900")
                    pub_date_str = item.get('pubDate', '')
                    if pub_date_str:
                        pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                        pub_date = pub_date.replace(tzinfo=None)  # Remove timezone
                    else:
                        continue
                    
                    if pub_date < cutoff_time:
                        continue
                    
                    # Clean HTML tags from title and description
                    title = re.sub(r'<[^>]+>', '', item.get('title', ''))
                    description = re.sub(r'<[^>]+>', '', item.get('description', ''))
                    
                    news_list.append({
                        'date': pub_date.strftime('%Y-%m-%d %H:%M'),
                        'title': title,
                        'content': description,
                        'source': f"Naver News API - {query}",
                        'url': item.get('link', '')
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing API result: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_list)} articles via API for query: {query}")
            return news_list
            
        except Exception as e:
            logger.error(f"Error searching Naver News API: {str(e)}")
            return []
