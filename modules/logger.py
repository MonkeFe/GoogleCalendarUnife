import logging
from logging.handlers import TimedRotatingFileHandler
import os
from dotenv import load_dotenv

load_dotenv()

log_dir = os.path.join(os.getenv("ABSOLUTEPATH"), 'logs')

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

def setup_logger(log_file_path):
    logger = logging.getLogger('MyLogger')
    logger.setLevel(logging.INFO)
    handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=14)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(handler)
    return logger

logger = setup_logger(os.path.join(log_dir, 'log.log'))