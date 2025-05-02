import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from django.conf import settings

# Add filter to ensure user and user_id are always present on log records
class UserContextFilter(logging.Filter):
    """Ensure user and user_id attributes exist on log records."""
    def filter(self, record):
        # Default to 'Anonymous User' when no user is set
        user_val = getattr(record, 'user', None)
        record.user = user_val or 'Anonymous User'
        # Default user_id to empty string when not provided
        user_id_val = getattr(record, 'user_id', None)
        record.user_id = user_id_val if user_id_val is not None else ''
        return True

# Create loggers
user_logger = logging.getLogger('user_actions')
api_logger = logging.getLogger('api_actions')
user_logger.addFilter(UserContextFilter())

# Get database logging setting from Django settings or use default
DB_LOGGING_ENABLED = getattr(settings, 'LOGGING_DB_ENABLED')

def setup_logging(logs_dir: str = 'logs') -> None:
    """
    Set up logging configuration for both user and API loggers
    
    Args:
        logs_dir: Directory where log files will be stored
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Set log levels
    user_logger.setLevel(logging.INFO)
    api_logger.setLevel(logging.INFO)

    # Size based rotation - 5MB per file, keep 5 backup files
    user_file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'users_actions.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )

    api_file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'api_actions.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )

    # Time based rotation - rotate daily at midnight
    user_time_handler = TimedRotatingFileHandler(
        os.path.join(logs_dir, 'users_actions_daily.log'),
        when='midnight',
        interval=1,
        backupCount=30  # Keep 30 days of logs
    )

    api_time_handler = TimedRotatingFileHandler(
        os.path.join(logs_dir, 'api_actions_daily.log'),
        when='midnight',
        interval=1,
        backupCount=30  # Keep 30 days of logs
    )

    # Console handlers for immediate feedback
    user_console_handler = logging.StreamHandler()
    api_console_handler = logging.StreamHandler()

    # Create formatters
    user_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - User: %(user)s (ID: %(user_id)s) - Action: %(message)s'
    )

    api_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - Endpoint: %(endpoint)s - %(message)s'
    )

    # Set formatters for handlers
    user_file_handler.setFormatter(user_formatter)
    user_time_handler.setFormatter(user_formatter)
    user_console_handler.setFormatter(user_formatter)

    api_file_handler.setFormatter(api_formatter)
    api_time_handler.setFormatter(api_formatter)
    api_console_handler.setFormatter(api_formatter)

    # Add handlers to loggers
    user_logger.addHandler(user_file_handler)
    user_logger.addHandler(user_time_handler)
    user_logger.addHandler(user_console_handler)

    api_logger.addHandler(api_file_handler)
    api_logger.addHandler(api_time_handler)
    api_logger.addHandler(api_console_handler) 