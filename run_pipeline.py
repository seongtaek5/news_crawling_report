#!/usr/bin/env python3
"""
Run the complete news collection and processing pipeline
"""
import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the complete pipeline"""
    logger.info("=" * 80)
    logger.info("Financial News Aggregator Pipeline")
    logger.info("=" * 80)
    logger.info("")
    
    # Step 1: Collect news
    logger.info("Step 1: Collecting news from Yahoo Finance and Naver News...")
    logger.info("-" * 80)
    
    try:
        import main as collector
        collector.main()
    except Exception as e:
        logger.error(f"Error during news collection: {str(e)}")
        sys.exit(1)
    
    logger.info("")
    logger.info("-" * 80)
    logger.info("Step 2: Processing news with OpenAI API...")
    logger.info("-" * 80)
    
    # Ask user if they want to process with AI
    try:
        response = input("\nDo you want to process the collected news with OpenAI? (y/n): ")
        if response.lower() in ['y', 'yes']:
            import process_with_ai as processor
            processor.main()
        else:
            logger.info("Skipping AI processing")
    except Exception as e:
        logger.error(f"Error during AI processing: {str(e)}")
        logger.info("Raw news file is still available")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("Pipeline completed!")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
