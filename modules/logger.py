import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
from dotenv import load_dotenv

load_dotenv()

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.getenv("ABSOLUTEPATH")

if env_path and os.path.isdir(env_path):
    base_dir = env_path
else:
    base_dir = project_root

log_dir = os.path.join(base_dir, 'logs')

if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

def setup_logger(log_file_path):
    logger = logging.getLogger('MyLogger')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        file_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=14)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(console_handler)

    return logger

logger = setup_logger(os.path.join(log_dir, 'log.log'))