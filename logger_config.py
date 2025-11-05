"""
Logger Configuration - Sets up logging for the scheduler
"""

import logging
import os
from datetime import datetime


def setup_logging():
    """Configures logging to console and file."""
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    log_filename = os.path.join(logs_dir, f'scheduler_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filename, encoding='utf-8')
        ]
    )
    
    return logging.getLogger(__name__)
