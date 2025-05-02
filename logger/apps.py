from django.apps import AppConfig
from .config import setup_logging

class LoggerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logger'

    def ready(self):
        """
        Initialize application services when Django starts
        """
        # Setup logging
        setup_logging() 