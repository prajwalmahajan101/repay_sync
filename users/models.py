from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from logger.user_logger import log_user_action
import logging

class CustomUserManager(UserManager, TreeManager):
    pass

class User(AbstractUser, MPTTModel):
    class UserRole(models.TextChoices):
        SUPER_MANAGER = 'SUPER_MANAGER', _('Super Manager')
        MANAGER = 'MANAGER', _('Manager')
        COLLECTION_OFFICER = 'COLLECTION_OFFICER', _('Collection Officer')
        CALLING_AGENT = 'CALLING_AGENT', _('Calling Agent')

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.SUPER_MANAGER
    )
    
    # MPTT parent field for hierarchical structure
    parent = TreeForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )

    objects = CustomUserManager()

    class MPTTMeta:
        order_insertion_by = ['username']

    def __str__(self):
        return f"{self.get_username()} {self.get_full_name()} ({self.get_role_display()})"

    def get_collection_officers_under_super_manager(self):
        """
        Get IDs of collection officers under a super manager's managers.
        Only applicable for super managers.
        """
        if self.role != self.UserRole.SUPER_MANAGER:
            return []
        return User.objects.filter(
            role=self.UserRole.COLLECTION_OFFICER,
            manager__in=self.get_descendants()
        ).values_list('id', flat=True)

    def get_collection_officers_under_manager(self):
        """
        Get IDs of collection officers directly under a manager.
        Only applicable for managers.
        """
        if self.role != self.UserRole.MANAGER:
            return []
        return self.get_descendants().filter(
            role=self.UserRole.COLLECTION_OFFICER
        ).values_list('id', flat=True)

    def get_managed_customers_queryset(self):
        """
        Get queryset of customers based on user's role and permissions.
        """
        from customers.models import Customer  # Import here to avoid circular import

        log_user_action(self, f"Accessing managed customers as {self.get_role_display()}")
        
        if self.is_superuser or self.role == self.UserRole.CALLING_AGENT:
            return Customer.objects.all()
        
        if self.role == self.UserRole.SUPER_MANAGER:
            collection_officer_ids = self.get_collection_officers_under_super_manager()
            return Customer.objects.filter(collection_officer_id__in=collection_officer_ids)
        
        if self.role == self.UserRole.MANAGER:
            collection_officer_ids = self.get_collection_officers_under_manager()
            return Customer.objects.filter(collection_officer_id__in=collection_officer_ids)
        
        if self.role == self.UserRole.COLLECTION_OFFICER:
            return Customer.objects.filter(collection_officer=self)
        
        return Customer.objects.none()

    def can_access_customer(self, customer, for_update=False):
        """
        Check if user has access to view/update a customer.
        Returns (has_access, error_message)
        """
        has_access, error_message = True, None

        if self.is_superuser or (not for_update and self.role == self.UserRole.CALLING_AGENT):
            has_access, error_message = True, None
        elif self.role == self.UserRole.SUPER_MANAGER:
            collection_officer_ids = self.get_collection_officers_under_super_manager()
            if customer.collection_officer_id not in collection_officer_ids:
                has_access, error_message = False, "You can only access customers assigned to collection officers under your managers"
        elif self.role == self.UserRole.MANAGER:
            collection_officer_ids = self.get_collection_officers_under_manager()
            if customer.collection_officer_id not in collection_officer_ids:
                has_access, error_message = False, "You can only access customers assigned to your collection officers"
        elif self.role == self.UserRole.COLLECTION_OFFICER:
            if customer.collection_officer != self:
                has_access, error_message = False, "You can only access your assigned customers"
        else:
            has_access, error_message = False, "You don't have permission to access customers"

        log_user_action(
            self,
            f"{'Successfully accessed' if has_access else 'Failed to access'} customer {customer.id} - {error_message if error_message else 'No errors'}",
            level=logging.INFO if has_access else logging.WARNING
        )

        return has_access, error_message

    def validate_collection_officer_assignment(self, officer):
        """
        Validate if user can assign the given collection officer.
        Returns (is_valid, error_message)
        """
        is_valid, error_message = True, None

        if self.is_superuser:
            is_valid, error_message = True, None
        elif self.role == self.UserRole.SUPER_MANAGER:
            valid_officers = self.get_descendants().filter(role=self.UserRole.COLLECTION_OFFICER)
            if officer not in valid_officers:
                is_valid, error_message = False, "You can only assign collection officers under your managers"
        elif self.role == self.UserRole.MANAGER:
            valid_officers = self.get_descendants().filter()
            if officer not in valid_officers:
                is_valid, error_message = False, "You can only assign your direct collection officers"
        else:
            is_valid, error_message = False, "You don't have permission to assign collection officers"

        log_user_action(
            self,
            f"{'Successfully validated' if is_valid else 'Failed to validate'} assignment of officer {officer.id} - {error_message if error_message else 'No errors'}",
            level=logging.INFO if is_valid else logging.WARNING
        )
        
        return is_valid, error_message

    def is_field_team(self):
        """Check if user is part of the field team (collection officer, manager, super manager)"""
        return self.role in [
            self.UserRole.COLLECTION_OFFICER,
            self.UserRole.MANAGER,
            self.UserRole.SUPER_MANAGER
        ]

    def is_calling_agent(self):
        """Check if user is a calling agent"""
        return self.role == self.UserRole.CALLING_AGENT

    def can_manage_user(self, other_user):
        """Check if the current user can manage another user"""
        # Calling agents can't manage anyone
        if self.role == self.UserRole.CALLING_AGENT:
            return False
            
        # Can't manage users who aren't part of field team
        if not other_user.is_field_team():
            return False
            
        # Collection officers can't manage anyone
        if self.role == self.UserRole.COLLECTION_OFFICER:
            return False
            
        # Super managers can manage managers and collection officers
        if self.role == self.UserRole.SUPER_MANAGER:
            return (other_user.role in [self.UserRole.MANAGER, self.UserRole.COLLECTION_OFFICER] 
                   and other_user in self.get_descendants(include_self=False))
            
        # Managers can only manage collection officers
        if self.role == self.UserRole.MANAGER:
            return (other_user.role == self.UserRole.COLLECTION_OFFICER 
                   and other_user in self.get_descendants(include_self=False))

    def can_register_role(self, role_to_register):
        """
        Check if the current user can register a new user with the specified role.
        
        Args:
            role_to_register (str): The role to be assigned to the new user
            
        Returns:
            bool: True if the user can register a new user with the specified role, False otherwise
        """
        # Super admin (is_superuser) can register any role
        if self.is_superuser:
            return True
            
        # SUPER_MANAGER can register MANAGER and COLLECTION_OFFICER
        if self.role == self.UserRole.SUPER_MANAGER:
            return role_to_register in [self.UserRole.MANAGER, self.UserRole.COLLECTION_OFFICER]
            
        # MANAGER can only register COLLECTION_OFFICER
        if self.role == self.UserRole.MANAGER:
            return role_to_register == self.UserRole.COLLECTION_OFFICER
            
        # All other roles cannot register new users
        return False

    def clean(self):
        super().clean()
        
        # Validate role-based parent rules
        if self.role == self.UserRole.CALLING_AGENT:
            # Calling agents cannot have a parent
            if self.parent is not None:
                raise ValidationError({'parent': _('Calling Agents cannot have a parent.')})
                
        elif self.role == self.UserRole.SUPER_MANAGER:
            # Super managers cannot have a parent
            if self.parent is not None:
                raise ValidationError({'parent': _('Super Managers cannot have a parent.')})
                
        elif self.role == self.UserRole.MANAGER:
            # Managers must have a super manager as parent
            if not self.parent or self.parent.role != self.UserRole.SUPER_MANAGER:
                raise ValidationError({'parent': _('Managers must have a Super Manager as their parent.')})
                
        elif self.role == self.UserRole.COLLECTION_OFFICER:
            # Collection officers must have a manager as parent
            if not self.parent or self.parent.role != self.UserRole.MANAGER:
                raise ValidationError({'parent': _('Collection Officers must have a Manager as their parent.')})
        
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        self.clean()
        # Ensure all users have is_staff=True to access admin panel
        self.is_staff = True
        
        # Set superuser status based on role
        if self.role == self.UserRole.SUPER_MANAGER:
            # Give SUPER_MANAGER admin access
            self.is_superuser = True
        
        super().save(*args, **kwargs)
        
        action = "Created" if is_new else "Updated"
        log_user_action(self, f"{action} user profile with role {self.get_role_display()}")
