"""
Process collected news with OpenAI API
No interpretation - only clean organization and listing of information
"""
import os
from datetime import datetime
import logging
from typing import List, Dict
import requests
import json

import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsProcessor:
    """Process and organize news using OpenAI API"""
    
    def __init__(self, api_key: str):
        """
        Initialize the processor
        
        Args:
            api_key: OpenAI API key
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.api_key = api_key
        self.model = config.OPENAI_MODEL
        self.max_tokens = config.OPENAI_MAX_TOKENS
        self.temperature = config.OPENAI_TEMPERATURE
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def process_news_file(self, input_file: str, output_file: str = None) -> str:
        """
        Process news from input file and organize it
        
        Args:
            input_file: Path to input news file
            output_file: Path to output file (optional)
        
        Returns:
            Path to output file
        """
        try:
            # Read input file
            with open(input_file, 'r', encoding='utf-8') as f:
                news_content = f.read()
            
            logger.info(f"Processing news from {input_file}")
            logger.info(f"Content length: {len(news_content)} characters")
            
            # Process with OpenAI
            processed_content = self._organize_news(news_content)
            
            # Determine output filename
            if not output_file:
                today = datetime.now().strftime('%Y%m%d')
                output_file = os.path.join(
                    config.OUTPUT_DIR,
                    f"{config.PROCESSED_FILE_PREFIX}_{today}.txt"
                )
            
            # Save processed content
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Processed Financial News Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                f.write(processed_content)
            
            logger.info(f"Processed news saved to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error processing news file: {str(e)}")
            raise
    
    def _organize_news(self, news_content: str) -> str:
        """
        Organize news content using OpenAI API
        
        Args:
            news_content: Raw news content
        
        Returns:
            Organized news content
        """
        # System prompt - emphasizes NO INTERPRETATION
        system_prompt = """You are a financial news organizer. Your ONLY task is to organize and list information clearly.

CRITICAL RULES:
1. NO interpretation, analysis, or opinions
2. NO buy/sell recommendations
3. NO sentiment analysis
4. NO predictions or forecasts
5. ONLY clean organization and categorization of factual information

Your job:
- Remove HTML tags, ads, and irrelevant text
- Organize news by categories (Market Overview, Company News, Economic Indicators, etc.)
- List facts and information clearly
- Maintain all original dates, numbers, and direct quotes
- Format for easy readability

Output format:
## [Category Name]

### [Date] - [Title]
- [Fact/Information point 1]
- [Fact/Information point 2]
...

Do NOT add any commentary, interpretation, or advice."""

        user_prompt = f"""Organize the following financial news articles by category. 
Remove unnecessary formatting, ads, and HTML artifacts. 
List only the factual information from each article.

NEWS CONTENT:
{news_content[:50000]}  

Remember: NO interpretation, ONLY organize and list the facts."""

        try:
            logger.info("Sending request to OpenAI API...")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            organized_content = result['choices'][0]['message']['content']
            
            logger.info("Successfully organized news with OpenAI")
            return organized_content
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
    
    def process_news_batch(self, news_list: List[Dict], batch_size: int = 20) -> str:
        """
        Process a list of news articles in batches
        
        Args:
            news_list: List of news dictionaries
            batch_size: Number of articles to process at once
        
        Returns:
            Organized content
        """
        all_organized = []
        
        for i in range(0, len(news_list), batch_size):
            batch = news_list[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} articles)")
            
            # Convert batch to text
            batch_text = ""
            for news in batch:
                batch_text += f"[Date: {news['date']}]\n"
                batch_text += f"[Title: {news['title']}]\n"
                batch_text += f"[Source: {news['source']}]\n"
                batch_text += f"[Content: {news['content']}]\n"
                batch_text += "-" * 80 + "\n\n"
            
            # Organize batch
            organized = self._organize_news(batch_text)
            all_organized.append(organized)
        
        return "\n\n".join(all_organized)


def main():
    """
    Main function to process collected news with OpenAI
    """
    logger.info("=" * 80)
    logger.info("Starting News Processing with OpenAI")
    logger.info("=" * 80)
    
    # Check API key
    if not config.OPENAI_API_KEY:
        logger.error("OpenAI API key not found in environment variables!")
        logger.error("Please set OPENAI_API_KEY in .env file")
        return
    
    # Initialize processor
    processor = NewsProcessor(api_key=config.OPENAI_API_KEY)
    
    # Find the latest news log file
    try:
        output_files = [
            f for f in os.listdir(config.OUTPUT_DIR)
            if f.startswith(config.LOG_FILE_PREFIX) and f.endswith('.txt')
        ]
        
        if not output_files:
            logger.error(f"No news log files found in {config.OUTPUT_DIR}")
            logger.error("Please run main.py first to collect news")
            return
        
        # Get the most recent file
        latest_file = sorted(output_files)[-1]
        input_path = os.path.join(config.OUTPUT_DIR, latest_file)
        
        logger.info(f"Processing file: {input_path}")
        
        # Process the file
        output_path = processor.process_news_file(input_path)
        
        logger.info("=" * 80)
        logger.info("Processing completed successfully!")
        logger.info(f"Output file: {output_path}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == '__main__':
    main()
