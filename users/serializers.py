from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from .utils import generate_random_password, store_user_credentials
from logger.user_logger import log_user_action
import logging

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    access_token = serializers.CharField(read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'role', 'first_name', 'last_name', 'parent', 'access_token')
        read_only_fields = ('id', 'access_token')

    def validate(self, data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            log_user_action(
                'Anonymous',
                "Attempted to access user validation without authentication",
                level=logging.WARNING
            )
            raise PermissionDenied("Authentication required")

        creating_user = request.user
        new_role = data.get('role')
        parent = data.get('parent')

        # Validate role permissions
        if not creating_user.can_register_role(new_role):
            log_user_action(
                creating_user,
                f"Attempted to create user with unauthorized role {new_role}",
                level=logging.WARNING
            )
            raise serializers.ValidationError(
                f"You don't have permission to create users with role {new_role}"
            )

        # Mandatory no-parent rules for SUPER_MANAGER and CALLING_AGENT
        if new_role in [User.UserRole.SUPER_MANAGER, User.UserRole.CALLING_AGENT]:
            if parent:
                role_display = 'Super Managers' if new_role == User.UserRole.SUPER_MANAGER else 'Calling Agents'
                log_user_action(
                    creating_user,
                    f"Attempted to assign parent to {role_display.lower()} role",
                    level=logging.WARNING
                )
                raise serializers.ValidationError({
                    'parent': f'{role_display} cannot have a parent.'
                })
            data['parent'] = None
            return data

        # Parent assignment rules based on the creating user's role
        if creating_user.is_superuser and data.get('parent'):
            # For other roles, parent is optional for superadmin
            return data
            
        elif creating_user.role == User.UserRole.SUPER_MANAGER:
            # Super managers can only create managers and collection officers
            if new_role == User.UserRole.MANAGER:
                # Managers created by super manager must have the super manager as parent
                data['parent'] = creating_user
            elif new_role == User.UserRole.COLLECTION_OFFICER and parent:
                # If parent is specified for collection officer, validate it's a manager under super manager
                if parent.role != User.UserRole.MANAGER:
                    log_user_action(
                        creating_user,
                        f"Attempted to assign non-manager parent {parent.username} to collection officer",
                        level=logging.WARNING
                    )
                    raise serializers.ValidationError({
                        'parent': 'Collection officers can only have a Manager as their parent'
                    })
                # Verify the manager is a descendant of this super manager
                if not creating_user.can_manage_user(parent):
                    log_user_action(
                        creating_user,
                        f"Attempted to assign unauthorized manager {parent.username} as parent",
                        level=logging.WARNING
                    )
                    raise serializers.ValidationError({
                        'parent': f'The specified manager {parent.username} is not under your management'
                    })
                    
        elif creating_user.role == User.UserRole.MANAGER:
            # Managers can only create collection officers
            if new_role != User.UserRole.COLLECTION_OFFICER:
                log_user_action(
                    creating_user,
                    f"Manager attempted to create user with role {new_role}",
                    level=logging.WARNING
                )
                raise serializers.ValidationError(
                    f"Managers cannot create users with role: {new_role}"
                )
            # Collection officers created by manager automatically have the manager as parent
            data['parent'] = creating_user

        # Additional parent validations for other roles when parent is specified
        if new_role == User.UserRole.MANAGER and parent:
            # If parent is specified for manager, it must be a super manager
            if parent.role != User.UserRole.SUPER_MANAGER:
                log_user_action(
                    creating_user,
                    f"Attempted to assign non-super-manager parent to manager role",
                    level=logging.WARNING
                )
                raise serializers.ValidationError({
                    'parent': 'Managers can only have a Super Manager as their parent.'
                })
                
        if new_role == User.UserRole.COLLECTION_OFFICER and parent:
            # If parent is specified for collection officer, it must be a manager
            if parent.role != User.UserRole.MANAGER:
                log_user_action(
                    creating_user,
                    f"Attempted to assign non-manager parent to collection officer",
                    level=logging.WARNING
                )
                raise serializers.ValidationError({
                    'parent': 'Collection Officers can only have a Manager as their parent.'
                })

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        creating_user = request.user if request else None
        
        # Generate random password if not provided
        password = validated_data.pop('password', None) or generate_random_password()
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Store credentials and get access token
        access_token = store_user_credentials(
            user_id=user.id,
            username=user.username,
            password=password,
            created_by_id=creating_user.id if creating_user else None
        )
        
        # Add access token to the instance for serialization
        user.access_token = access_token
        
        log_user_action(
            creating_user or 'System',
            f"Created new user {user.username} with role {user.get_role_display()} via API"
        )
        
        return user 