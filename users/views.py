from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from .serializers import UserSerializer
from .utils import get_user_credentials
from logger.user_logger import log_user_action
from logger.api_logger import log_api_call
import logging

User = get_user_model()

# Create your views here.

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@log_api_call
def register(request):
    """
    Register a new user. The requesting user must have appropriate permissions
    based on their role to register users with specific roles.
    """
    serializer = UserSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.save()
        log_user_action(
            request.user,
            f"Registered new user {user.username} with role {user.get_role_display()}"
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    log_user_action(
        request.user,
        f"Failed to register new user: {serializer.errors}",
        level=logging.WARNING
    )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_call
def profile(request):
    """
    Get the current user's profile
    """
    serializer = UserSerializer(request.user)
    log_user_action(request.user, "Accessed their profile")
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_call
def subordinates(request):
    """
    Get all users under the current user in the hierarchy
    """
    if request.user.role not in [User.UserRole.SUPER_MANAGER, User.UserRole.MANAGER]:
        log_user_action(
            request.user,
            f"Attempted to access subordinates list when the user is not a super manager or manager",
            level=logging.WARNING
        )
        raise PermissionDenied("You don't have permission to acess this subordinates list")
    users = request.user.get_descendants()
    serializer = UserSerializer(users, many=True)
    log_user_action(request.user, f"Retrieved list of {users.count()} subordinates")
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@log_api_call
def assign_parent(request, user_id):
    """
    Assign a new parent to a user. The requesting user must have permission to manage both
    the target user and the new parent user.
    
    Request body should contain:
    {
        "parent_id": "<id of the new parent user>"
    }
    """
    target_user = get_object_or_404(User, id=user_id)
    new_parent_id = request.data.get('parent_id')

    if request.user.role not in [User.UserRole.SUPER_MANAGER, User.UserRole.MANAGER] and not request.user.is_superuser:
        log_user_action(
                request.user,
                f"Attempted to manage user when the user is not a super manager or manager",
                level=logging.WARNING
            )
        raise PermissionDenied("Only super managers and managers can assign parents")
    
    # Check if the requesting user can manage the target user or is a superuser
    if not (request.user.can_manage_user(target_user) or request.user.is_superuser):
        log_user_action(
            request.user,
            f"Attempted to manage user {target_user.username} without permission",
            level=logging.WARNING
        )
        raise PermissionDenied("You don't have permission to manage this user")
    
    # If parent_id is None, and user is not superuser, raise error
    if new_parent_id is None and not request.user.is_superuser:
        log_user_action(
            request.user,
            f"Attempted to remove parent for user {target_user.username} without superuser privileges",
            level=logging.WARNING
        )
        raise PermissionDenied("Parent ID is required")
        
    if new_parent_id:
        new_parent = get_object_or_404(User, id=new_parent_id)
        
        # Validate that new parent is not the user themselves
        if new_parent.id == target_user.id:
            log_user_action(
                request.user,
                f"Attempted to set user {target_user.username} as their own parent",
                level=logging.WARNING
            )
            raise PermissionDenied("User cannot be their own parent")
            
        # Validate that new parent is not one of user's descendants
        if new_parent in target_user.get_descendants():
            log_user_action(
                request.user,
                f"Attempted to set subordinate {new_parent.username} as parent of {target_user.username}",
                level=logging.WARNING
            )
            raise PermissionDenied("Parent cannot be a subordinate of the user")
            
        # Check if the requesting user can manage the new parent
        # Skip this check for superuser as they can assign any parent
        if not request.user.is_superuser:
            # New parent must be the requesting user or one of their subordinates
            if new_parent != request.user and new_parent not in request.user.get_descendants():
                log_user_action(
                    request.user,
                    f"Attempted to assign unauthorized parent {new_parent.username} to {target_user.username}",
                    level=logging.WARNING
                )
                raise PermissionDenied("You don't have permission to assign this parent")
            
        target_user.parent = new_parent
    else:
        # Only superuser can remove parent (set to None)
        target_user.parent = None
        
    target_user.save()
    log_user_action(
        request.user,
        f"Successfully {'removed parent from' if new_parent_id is None else f'assigned parent {new_parent.username} to'} user {target_user.username}"
    )
    serializer = UserSerializer(target_user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
@log_api_call
def get_credentials(request, access_token):
    """
    Retrieve user credentials using a one-time access token.
    This endpoint is intentionally not authentication protected as it needs
    to be accessible with just the access token.
    """
    credentials = get_user_credentials(access_token)
    
    if not credentials:
        log_user_action(
            "Anonymous",
            f"Failed credential retrieval attempt with invalid token",
            level=logging.WARNING
        )
        return Response(
            {"error": "Invalid or expired access token"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    log_user_action(
        credentials.get('username', 'Unknown'),
        "Successfully retrieved credentials using one-time token"
    )
    return Response(credentials)
