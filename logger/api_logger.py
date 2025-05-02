import functools
import json
import time
import uuid
from datetime import datetime
from typing import Callable
from django.http import HttpRequest
from .config import api_logger, DB_LOGGING_ENABLED
from .models import APILog

def log_api_call(func: Callable = None, *, db_log: bool = None) -> Callable:
    """
    A decorator that logs API request and response details with both file and database logging.
    Specifically designed to work with Django view functions.
    
    Args:
        func: The Django view function to be decorated
        db_log: Whether to log to database (default: None, uses global setting)
        
    Returns:
        wrapper: The wrapped function with logging capabilities
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Determine if database logging is enabled
            use_db_log = DB_LOGGING_ENABLED if db_log is None else db_log
            
            # Generate or get request ID
            request_id = getattr(request, 'request_id', None)
            if not request_id:
                request_id = str(uuid.uuid4())
                setattr(request, 'request_id', request_id)
                
            # Get current timestamp and endpoint name
            start_time = time.time()
            request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            endpoint = f.__name__
            
            # Prepare extra context for logging
            extra = {
                'endpoint': endpoint,
                'request_id': request_id
            }
            
            # Database log object (will be saved later)
            api_db_log = None
            if use_db_log:
                api_db_log = APILog(
                    request_id=request_id,
                    endpoint=endpoint
                )
            
            # Extract request details safely
            try:
                # Get request body for POST/PUT/PATCH
                if request.method in ['POST', 'PUT', 'PATCH']:
                    request_data = request.data if hasattr(request, 'data') else request.POST
                else:
                    request_data = request.GET

                # Get user information
                user = request.user if hasattr(request, 'user') else 'Anonymous'
                
                # Prepare request log
                request_log = {
                    'timestamp': request_time,
                    'request_id': request_id,
                    'method': request.method,
                    'user': str(user),
                    'path': request.path,
                    'query_params': dict(request.GET),
                    'data': request_data
                }
                
                # Update database log object
                if use_db_log and api_db_log:
                    api_db_log.method = request.method
                    api_db_log.user = str(user)
                    api_db_log.path = request.path
                    api_db_log.query_params = dict(request.GET)
                    api_db_log.request_data = request_data
            except Exception as e:
                request_log = {
                    'timestamp': request_time,
                    'request_id': request_id,
                    'error': f"Error extracting request details: {str(e)}"
                }

            # Log request
            api_logger.info(
                f"Request: {json.dumps(request_log, indent=2)}",
                extra=extra
            )
            
            try:
                # Execute the view function
                response = f(request, *args, **kwargs)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Prepare response log
                try:
                    response_data = response.data if hasattr(response, 'data') else str(response)
                    status_code = response.status_code if hasattr(response, 'status_code') else 'Unknown'
                except Exception:
                    response_data = str(response)
                    status_code = 'Unknown'
                
                response_log = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'request_id': request_id,
                    'status': 'success',
                    'status_code': status_code,
                    'execution_time': f"{execution_time:.2f} seconds",
                    'response': response_data
                }
                
                # Update database log
                if use_db_log and api_db_log:
                    api_db_log.status_code = status_code if isinstance(status_code, int) else None
                    api_db_log.execution_time = execution_time
                    try:
                        api_db_log.response_data = response_data
                    except TypeError:
                        # Handle case where response data is not JSON serializable
                        api_db_log.response_data = {'data': str(response_data)}
                    api_db_log.is_error = False
                    
                    try:
                        api_db_log.save()
                    except Exception as e:
                        api_logger.error(f"Failed to save API log to database: {str(e)}", extra=extra)
                
                # Log response
                api_logger.info(
                    f"Response: {json.dumps(response_log, indent=2)}",
                    extra=extra
                )
                return response
                
            except Exception as e:
                # Log error if any exception occurs
                error_log = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'request_id': request_id,
                    'status': 'error',
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
                
                # Update database log for errors
                if use_db_log and api_db_log:
                    api_db_log.is_error = True
                    api_db_log.error_type = type(e).__name__
                    api_db_log.error_message = str(e)
                    
                    try:
                        api_db_log.save()
                    except Exception as db_err:
                        api_logger.error(f"Failed to save API error log to database: {str(db_err)}", extra=extra)
                
                api_logger.error(
                    f"Error: {json.dumps(error_log, indent=2)}",
                    extra=extra
                )
                raise
        
        return wrapper
    
    # Handle both decorator with and without arguments
    if func is not None:
        return decorator(func)
    return decorator 