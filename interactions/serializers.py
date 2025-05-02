from rest_framework import serializers
from .models import Interaction
from customers.models import Customer
from django.utils import timezone
from users.models import User

class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = [
            'id',
            'customer',
            'created_by',
            'comment',
            'disposition',
            'next_call_date',
            'created_at',
            'updated_at',
            'interaction_type'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'interaction_type']

    def validate_customer(self, value):
        """
        Validate that the customer exists and is accessible to the user.
        """
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("No request found in context")
        
        user = request.user
        if user.role != User.UserRole.CALLING_AGENT:
            has_access, error_message = user.can_access_customer(value)
            if not has_access:
                raise serializers.ValidationError(error_message)
        
        return value

    def validate_next_call_date(self, value):
        """
        Validate that next_call_date is in the future if provided.
        """
        if value and value < timezone.now():
            raise serializers.ValidationError("Next call date must be in the future")
        return value 