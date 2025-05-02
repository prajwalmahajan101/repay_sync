from django.db import models

# Create your models here.
class UserLog(models.Model):
    """Model for storing user action logs in the database"""
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.IntegerField(null=True, blank=True)
    user = models.CharField(max_length=255)
    action = models.TextField()
    level = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['user_id']),
            models.Index(fields=['timestamp']),
        ]
        
    def __str__(self):
        return f"{self.timestamp} - {self.user}: {self.action[:50]}"


class APILog(models.Model):
    """Model for storing API request/response logs in the database"""
    request_id = models.CharField(max_length=36, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    user = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    query_params = models.JSONField(null=True, blank=True)
    request_data = models.JSONField(null=True, blank=True)
    status_code = models.IntegerField(null=True)
    execution_time = models.FloatField(null=True)
    response_data = models.JSONField(null=True, blank=True)
    is_error = models.BooleanField(default=False)
    error_type = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['request_id']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
        ]
        
    def __str__(self):
        return f"{self.timestamp} - {self.method} {self.path} ({self.status_code})" 