import random
import string
import secrets
from django.core.cache import cache
from datetime import datetime, timedelta

def generate_random_password(length=12):
    """Generate a secure random password"""
    # Ensure at least one of each required character type
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*"
    
    # Get one character from each category
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Fill the rest with random characters from all categories
    all_characters = lowercase + uppercase + digits + special_chars
    password.extend(secrets.choice(all_characters) for _ in range(length - 4))
    
    # Shuffle the password
    random.shuffle(password)
    return ''.join(password)

def store_user_credentials(user_id, username, password, created_by_id):
    """
    Store user credentials temporarily in cache
    Returns a one-time access token
    """
    access_token = secrets.token_urlsafe(32)
    credentials = {
        'username': username,
        'password': password,
        'created_at': datetime.now().isoformat(),
        'created_by': created_by_id
    }
    
    # Store in cache for 24 hours
    cache_key = f'user_credentials_{access_token}'
    cache.set(cache_key, credentials, timeout=86400)  # 24 hours in seconds
    
    return access_token

def get_user_credentials(access_token):
    """
    Retrieve and delete user credentials from cache
    Returns None if not found or already accessed
    """
    cache_key = f'user_credentials_{access_token}'
    credentials = cache.get(cache_key)
    
    if credentials:
        # Delete from cache after retrieval (one-time access)
        cache.delete(cache_key)
        
    return credentials 