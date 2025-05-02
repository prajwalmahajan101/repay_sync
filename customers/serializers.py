from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Customer

User = get_user_model()

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone_number', 'email', 'address', 'collection_officer', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_collection_officer(self, value):
        if value and value.role != User.UserRole.COLLECTION_OFFICER:
            raise serializers.ValidationError("Assigned user must be a Collection Officer")
        return value

    def validate(self, data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")

        user = request.user
        # Allow collection officers to create customers with themselves as collection officer
        if user.role == User.UserRole.COLLECTION_OFFICER:
            if 'collection_officer' in data and data['collection_officer'] != user:
                raise serializers.ValidationError("Collection officers can only assign themselves as collection officer")
            data['collection_officer'] = user
            return data

        # Allow calling agents to view but not modify
        if user.role == User.UserRole.CALLING_AGENT:
            if self.instance is None:  # Creating new customer
                raise serializers.ValidationError("Calling agents cannot create customers")
            return data

        # Only allow super admin, super manager, and manager to create/update customers
        if not (user.is_superuser or 
                user.role in [User.UserRole.SUPER_MANAGER, User.UserRole.MANAGER]):
            raise serializers.ValidationError("You don't have permission to perform this action")

        # If collection_officer is assigned, validate that the requesting user can manage them
        collection_officer = data.get('collection_officer')
        if collection_officer:
            if user.is_superuser:
                return data
                
            if user.role == User.UserRole.SUPER_MANAGER:
                # Get all collection officers under the super manager's managers
                valid_officers = user.get_descendants().filter(role=User.UserRole.COLLECTION_OFFICER)
                if collection_officer not in valid_officers:
                    raise serializers.ValidationError(
                        "You can only assign collection officers under your managers"
                    )
            
            elif user.role == User.UserRole.MANAGER:
                # Get direct collection officer descendants
                valid_officers = user.get_descendants()
                if collection_officer not in valid_officers:
                    raise serializers.ValidationError(
                        "You can only assign your direct collection officers"
                    )

        return data 