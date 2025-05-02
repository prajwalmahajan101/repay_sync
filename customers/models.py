from django.db import models
from django.conf import settings
from users.models import User
from logger.user_logger import log_user_action
import logging

class Customer(models.Model):
    # Basic customer information
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    
    # Customer assignment
    collection_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_customers',
        limit_choices_to={'role': User.UserRole.COLLECTION_OFFICER}
    )
    
    # Latest interaction reference
    latest_interaction = models.ForeignKey(
        settings.INTERACTION_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Reference to the most recent interaction with this customer'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.phone_number}"

    def save(self, *args, **kwargs):
        """Override save to log customer changes"""
        is_new = self._state.adding
        
        # Get the old instance if this is an update
        if not is_new:
            old_instance = Customer.objects.get(pk=self.pk)
            old_officer = old_instance.collection_officer
            new_officer = self.collection_officer
            
            # Log officer reassignment
            if old_officer != new_officer:
                log_user_action(
                    getattr(self, '_current_user', 'System'),
                    f"Reassigned customer {self.name} from {old_officer or 'None'} to {new_officer or 'None'}"
                )
        
        super().save(*args, **kwargs)
        
        if is_new:
            log_user_action(
                getattr(self, '_current_user', 'System'),
                f"Created new customer: {self.name}"
            )
        else:
            log_user_action(
                getattr(self, '_current_user', 'System'),
                f"Updated customer: {self.name}"
            )

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['collection_officer']),
            models.Index(fields=['latest_interaction']),
        ]
