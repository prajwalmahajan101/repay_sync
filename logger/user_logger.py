import logging
from typing import Any
from logger.config import user_logger, DB_LOGGING_ENABLED
from .models import UserLog

def log_user_action(user: Any, action: str, level: int = logging.INFO, db_log: bool = None) -> None:
    """
    Log user actions with user context to both file and database
    
    Args:
        user: User object or user identifier
        action: Description of the action
        level: Logging level (default: INFO)
        db_log: Whether to log to database (default: None, uses global setting)
    """
    # Extract user ID if available
    user_id_val = getattr(user, 'id', None)
    extra = {'user': str(user), 'user_id': user_id_val}
    
    # Log to file using existing logger
    user_logger.log(level, action, extra=extra)
    
    # Check if db_log parameter is specified, otherwise use global setting
    if db_log is None:
        db_log = DB_LOGGING_ENABLED
    
    # Also log to database if enabled
    if db_log:
        try:
            UserLog.objects.create(
                user_id=user_id_val,
                user=str(user),
                action=action,
                level=level
            )
        except Exception as e:
            # If database logging fails, log the error to file but don't interrupt the application
            user_logger.error(f"Failed to log to database: {str(e)}", extra=extra) 