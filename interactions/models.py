from django.db import models
from django.conf import settings
from customers.models import Customer

class Interaction(models.Model):
    class DispositionChoices(models.TextChoices):
        PROMISE_TO_PAY = 'PROMISE_TO_PAY', 'Promise to Pay'
        NOT_REACHABLE = 'NOT_REACHABLE', 'Not Reachable'
        WRONG_NUMBER = 'WRONG_NUMBER', 'Wrong Number'
        REFUSED_TO_PAY = 'REFUSED_TO_PAY', 'Refused to Pay'
        PARTIAL_PAYMENT = 'PARTIAL_PAYMENT', 'Partial Payment'
        FULL_PAYMENT = 'FULL_PAYMENT', 'Full Payment'
        CALL_BACK = 'CALL_BACK', 'Call Back Later'
        OTHER = 'OTHER', 'Other'

    class InteractionTypeChoices(models.TextChoices):
        CALL = 'CALL', 'Phone Call'
        FIELD = 'FIELD', 'Field Visit'
        

    # Relationships
    customer = models.ForeignKey(
        settings.CUSTOMER_MODEL,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_interactions'
    )

    # Interaction details
    comment = models.TextField()
    disposition = models.CharField(
        max_length=20,
        choices=DispositionChoices.choices
    )
    next_call_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    interaction_type = models.CharField(
        max_length=20,
         choices=InteractionTypeChoices.choices
    )

    def save(self, *args, **kwargs):
        """Override save to update customer's latest interaction"""
        super().save(*args, **kwargs)
        
        # Update customer's latest interaction if this is the most recent
        latest_interaction = self.customer.interactions.order_by('-created_at').first()
        if latest_interaction == self:
            self.customer.latest_interaction = self
            self.customer.save(update_fields=['latest_interaction'])

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['disposition']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.customer} - {self.disposition} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
