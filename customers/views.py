from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Customer
from .serializers import CustomerSerializer
from interactions.serializers import InteractionSerializer
from interactions.models import Interaction
from logger.user_logger import log_user_action
from logger.api_logger import log_api_call
import logging

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_call
def customer_list(request):
    """
    List all customers based on user's role and permissions.
    Optional query parameter:
    - disposition: Filter customers by their latest interaction's disposition
    """
    customers = request.user.get_managed_customers_queryset()
    
    # Filter by latest interaction disposition if provided
    disposition = request.query_params.get('disposition')
    if disposition:
        customers = customers.filter(latest_interaction__disposition=disposition)
    
    serializer = CustomerSerializer(customers, many=True)
    log_user_action(request.user, f"Retrieved list of {customers.count()} customers")
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@log_api_call
def create_customer(request):
    """
    Create a new customer.
    Accessible by super admin, super managers, managers, and collection officers.
    Collection officers can only create customers assigned to themselves.
    """
    serializer = CustomerSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        # Set current user for logging in model save
        customer = serializer.save()
        customer._current_user = request.user
        customer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    log_user_action(
        request.user,
        f"Failed to create customer: {serializer.errors}",
        level=logging.WARNING
    )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_call
def customer_detail(request, pk):
    """
    Retrieve a customer instance.
    Access controlled by user's role and permissions.
    """
    customer = get_object_or_404(Customer, pk=pk)
    has_access, error_message = request.user.can_access_customer(customer)
    
    if not has_access:
        log_user_action(
            request.user,
            f"Attempted unauthorized access to customer {customer.name} (ID: {customer.id})",
            level=logging.WARNING
        )
        return Response(
            {"detail": error_message},
            status=status.HTTP_403_FORBIDDEN
        )
    
    log_user_action(request.user, f"Viewed customer details for {customer.name}")
    serializer = CustomerSerializer(customer)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@log_api_call
def update_customer(request, pk):
    """
    Update a customer.
    Only accessible by:
    - The assigned collection officer (can't change assignment)
    - The manager of the assigned collection officer
    - The super manager above the manager
    - Super admin
    """
    customer = get_object_or_404(Customer, pk=pk)
    user = request.user

    has_access, error_message = user.can_access_customer(customer, for_update=True)
    if not has_access:
        log_user_action(
            user,
            f"Attempted unauthorized update of customer {customer.name} (ID: {customer.id})",
            level=logging.WARNING
        )
        return Response(
            {"detail": error_message},
            status=status.HTTP_403_FORBIDDEN
        )

    # Collection officers cannot change customer assignments
    if user.role == User.UserRole.COLLECTION_OFFICER and 'collection_officer' in request.data:
        log_user_action(
            user,
            f"Collection officer attempted to change assignment for customer {customer.name}",
            level=logging.WARNING
        )
        return Response(
            {"detail": "Collection officers cannot change customer assignments"},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = CustomerSerializer(
        customer, 
        data=request.data, 
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    if serializer.is_valid():
        # Set current user for logging in model save
        updated_customer = serializer.save()
        updated_customer._current_user = user
        updated_customer.save()
        return Response(serializer.data)
    
    log_user_action(
        user,
        f"Failed to update customer {customer.name}: {serializer.errors}",
        level=logging.WARNING
    )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@log_api_call
def delete_customer(request, pk):
    """
    Delete a customer.
    Only accessible by super admin and super managers.
    """
    customer = get_object_or_404(Customer, pk=pk)
    user = request.user
    
    if not (user.is_superuser or user.role == User.UserRole.SUPER_MANAGER):
        log_user_action(
            user,
            f"Unauthorized attempt to delete customer {customer.name}",
            level=logging.WARNING
        )
        return Response(
            {"detail": "Only super admin and super managers can delete customers"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # For super managers, check if they can manage this customer
    if user.role == User.UserRole.SUPER_MANAGER:
        has_access, error_message = user.can_access_customer(customer)
        if not has_access:
            log_user_action(
                user,
                f"Super manager attempted to delete customer {customer.name} outside their hierarchy",
                level=logging.WARNING
            )
            return Response(
                {"detail": "You can only delete customers assigned to collection officers under your managers"},
                status=status.HTTP_403_FORBIDDEN
            )
    
    customer_name = customer.name
    customer.delete()
    log_user_action(user, f"Deleted customer {customer_name}")
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_call
def unassigned_customers(request):
    """
    List all unassigned customers.
    Accessible by super admin, super managers, managers, and calling agents.
    """
    user = request.user
    if not (user.is_superuser or 
            user.role in [User.UserRole.SUPER_MANAGER, User.UserRole.MANAGER, User.UserRole.CALLING_AGENT]):
        log_user_action(
            user,
            "Unauthorized attempt to view unassigned customers",
            level=logging.WARNING
        )
        return Response(
            {"detail": "You don't have permission to view unassigned customers"},
            status=status.HTTP_403_FORBIDDEN
        )
        
    customers = Customer.objects.filter(collection_officer__isnull=True)
    log_user_action(user, f"Retrieved list of {customers.count()} unassigned customers")
    serializer = CustomerSerializer(customers, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@log_api_call
def assign_collection_officer(request, pk):
    """
    Assign a collection officer to a customer.
    Accessible by super admin, super managers, and managers.
    Managers can only assign collection officers under their management.
    """
    customer = get_object_or_404(Customer, pk=pk)
    user = request.user
    officer_id = request.data.get('officer_id')
    
    if not officer_id:
        log_user_action(
            user,
            f"Failed to assign collection officer to customer {customer.name}: Missing officer_id",
            level=logging.WARNING
        )
        return Response(
            {"detail": "officer_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    try:
        officer = User.objects.get(id=officer_id, role=User.UserRole.COLLECTION_OFFICER)
    except User.DoesNotExist:
        log_user_action(
            user,
            f"Failed to assign collection officer to customer {customer.name}: Invalid officer ID {officer_id}",
            level=logging.WARNING
        )
        return Response(
            {"detail": "Invalid collection officer ID"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    is_valid, error_message = user.validate_collection_officer_assignment(officer)
    if not is_valid:
        log_user_action(
            user,
            f"Unauthorized attempt to assign officer {officer.username} to customer {customer.name}",
            level=logging.WARNING
        )
        return Response(
            {"detail": error_message},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Set current user for logging in model save
    customer.collection_officer = officer
    customer._current_user = user
    customer.save()
    
    serializer = CustomerSerializer(customer)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_call
def customer_latest_interaction(request, pk):
    """
    Get the latest interaction for a specific customer.
    Access controlled by user's role and permissions.
    If latest_interaction is not set, tries to find from interactions and updates the customer model.
    """
    customer = get_object_or_404(Customer, pk=pk)
    has_access, error_message = request.user.can_access_customer(customer)
    
    if not has_access:
        log_user_action(
            request.user,
            f"Attempted unauthorized access to latest interaction for customer {customer.name}",
            level=logging.WARNING
        )
        return Response(
            {"detail": error_message},
            status=status.HTTP_403_FORBIDDEN
        )
    
    latest_interaction = customer.latest_interaction
    
    # If no latest_interaction found, try to get from interactions
    if not latest_interaction:
        latest_interaction = Interaction.objects.filter(customer=customer).order_by('-created_at').first()
        
        # If found an interaction, update the customer's latest_interaction
        if latest_interaction:
            customer.latest_interaction = latest_interaction
            customer.save(update_fields=['latest_interaction'])
            log_user_action(
                request.user,
                f"Updated customer {customer.name}'s latest interaction reference",
                level=logging.INFO
            )
    
    if not latest_interaction:
        return Response(
            {"detail": "No interactions found for this customer"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = InteractionSerializer(latest_interaction)
    log_user_action(request.user, f"Retrieved latest interaction for customer {customer.name}")
    return Response(serializer.data)
