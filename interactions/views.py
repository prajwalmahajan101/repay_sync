from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Interaction
from .serializers import InteractionSerializer
from customers.models import Customer
from logger.user_logger import log_user_action
from logger.api_logger import log_api_call
import logging

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_call
def interaction_list(request):
    """
    List interactions based on user's role and permissions.
    Calling agents can view all interactions.
    Collection officers, managers, and super managers can only view interactions
    for their customers or their descendant's customers.
    
    Query parameters:
    - customer: Filter interactions by customer ID
    """
    user = request.user
    # Filter by customer if provided
    customer_id = request.query_params.get('customer')
    # Calling agents can view all interactions
    if user.role == User.UserRole.CALLING_AGENT:
        interactions = Interaction.objects.all()
        if customer_id:
            interactions = interactions.filter(customer_id=customer_id)
    else:
        # Get customers accessible to the user based on their role
        customers = user.get_managed_customers_queryset()
        if customer_id and not customers.filter(id=customer_id).exists():
            return Response(
                {"detail": "You don't have permission to access this customer"},
                status=status.HTTP_403_FORBIDDEN
            )
        interactions = Interaction.objects.filter(customer__in=customers)
    
    
    serializer = InteractionSerializer(interactions, many=True)
    log_user_action(user, f"Retrieved list of {interactions.count()} interactions")
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@log_api_call
def create_interaction(request):
    """
    Create a new interaction.
    Automatically sets interaction_type based on user role:
    - CALL for calling agents
    - FIELD for collection officers, managers, and super managers
    """
    user = request.user
    customer_id = request.data.get('customer')
    
    if not customer_id:
        return Response(
            {"detail": "Customer ID is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify customer access
    customer = get_object_or_404(Customer, pk=customer_id)
    if user.role != User.UserRole.CALLING_AGENT:
        has_access, error_message = user.can_access_customer(customer)
        if not has_access:
            log_user_action(
                user,
                f"Attempted to create interaction for unauthorized customer {customer.name}",
                level=logging.WARNING
            )
            return Response(
                {"detail": error_message},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Set interaction type based on user role
    interaction_type = Interaction.InteractionTypeChoices.CALL if user.role == User.UserRole.CALLING_AGENT else Interaction.InteractionTypeChoices.FIELD
    data = {**request.data, 'interaction_type': interaction_type, 'created_by': user.id}
    
    serializer = InteractionSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        interaction = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    log_user_action(
        user,
        f"Failed to create interaction: {serializer.errors}",
        level=logging.WARNING
    )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_call
def interaction_detail(request, pk):
    """
    Retrieve an interaction instance.
    Access controlled by user's role and permissions.
    """
    interaction = get_object_or_404(Interaction, pk=pk)
    user = request.user
    
    # Calling agents can view all interactions
    if user.role != User.UserRole.CALLING_AGENT:
        has_access, error_message = user.can_access_customer(interaction.customer)
        if not has_access:
            log_user_action(
                user,
                f"Attempted unauthorized access to interaction {pk}",
                level=logging.WARNING
            )
            return Response(
                {"detail": error_message},
                status=status.HTTP_403_FORBIDDEN
            )
    
    serializer = InteractionSerializer(interaction)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@log_api_call
def update_interaction(request, pk):
    """
    Update an interaction.
    For FIELD interactions:
    - Can be updated by super admin, super manager, manager, or collection officer with access to the customer
    For CALL interactions:
    - Can only be updated by the calling agent who created it
    interaction_type field cannot be modified.
    """
    interaction = get_object_or_404(Interaction, pk=pk)
    user = request.user
    
    # Check permissions based on interaction type
    if interaction.interaction_type == Interaction.InteractionTypeChoices.CALL:
        # For CALL interactions, only the calling agent who created it can update or super admin can update
        if not ((user.role == User.UserRole.CALLING_AGENT and interaction.created_by == user) or user.is_superuser):
            log_user_action(
                user,
                f"Attempted to update CALL interaction {pk} without proper permissions",
                level=logging.WARNING
            )
            return Response(
                {"detail": "Only the calling agent who created this interaction can update it"},
                status=status.HTTP_403_FORBIDDEN
            )
    else:  # FIELD interaction
        # For FIELD interactions, check if user has proper role and access to customer
        if not user.is_superuser and user.role not in [
            User.UserRole.SUPER_MANAGER,
            User.UserRole.MANAGER,
            User.UserRole.COLLECTION_OFFICER
        ]:
            log_user_action(
                user,
                f"Attempted to update FIELD interaction {pk} without proper role",
                level=logging.WARNING
            )
            return Response(
                {"detail": "You don't have permission to update field interactions"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Check if user has access to the customer
        has_access, error_message = user.can_access_customer(interaction.customer)
        if not has_access:
            log_user_action(
                user,
                f"Attempted to update FIELD interaction {pk} for unauthorized customer",
                level=logging.WARNING
            )
            return Response(
                {"detail": error_message},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Remove interaction_type from request data if present
    if 'interaction_type' in request.data:
        del request.data['interaction_type']
    
    serializer = InteractionSerializer(
        interaction,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    log_user_action(
        user,
        f"Failed to update interaction {pk}: {serializer.errors}",
        level=logging.WARNING
    )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@log_api_call
def delete_interaction(request, pk):
    """
    Delete an interaction.
    Only super admin and the user who created the interaction can delete it.
    """
    interaction = get_object_or_404(Interaction, pk=pk)
    user = request.user
    
    if not (user.is_superuser or interaction.created_by == user):
        log_user_action(
            user,
            f"Unauthorized attempt to delete interaction {pk}",
            level=logging.WARNING
        )
        return Response(
            {"detail": "Only super admin or the creator can delete an interaction"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    interaction.delete()
    log_user_action(user, f"Deleted interaction {pk}")
    return Response(status=status.HTTP_204_NO_CONTENT)
