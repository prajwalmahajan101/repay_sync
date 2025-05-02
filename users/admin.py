from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
import csv
import io
from .models import User
from .forms import CSVImportForm
from .utils import generate_random_password, store_user_credentials
from logger.user_logger import log_user_action
import logging

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'parent')
    list_filter = ('role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role & Hierarchy', {'fields': ('role', 'parent')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'parent'),
        }),
    )
    
    change_list_template = "admin/user_change_list.html"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='import_csv'),
        ]
        return custom_urls + urls
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
            
        # Super managers can see all descendants of their managers (descendants' descendants)
        if request.user.role ==User.UserRole.SUPER_MANAGER:
            # Get all direct manager descendants
            manager_descendants = request.user.get_descendants().filter(role=User.UserRole.MANAGER)
            # Get all descendants of those managers
            all_subordinates = set()
            for manager in manager_descendants:
                all_subordinates.update(manager.get_descendants().values_list('id', flat=True))
            # Add the managers themselves and the super manager to the list
            all_subordinates.update(manager_descendants.values_list('id', flat=True))
            all_subordinates.add(request.user.id)
            return qs.filter(id__in=all_subordinates)
            
        # Managers can see all their descendants
        if request.user.role == User.UserRole.MANAGER:
            subordinate_ids = list(request.user.get_descendants().values_list('id', flat=True))
            subordinate_ids.append(request.user.id)
            return qs.filter(id__in=subordinate_ids)
            
        # Collection officers can only see themselves
        return qs.filter(id=request.user.id)
    
    def save_model(self, request, obj, form, change):
        """Log user creation/modification in admin"""
        is_new = not obj.pk
        super().save_model(request, obj, form, change)
        
        if is_new:
            log_user_action(
                request.user,
                f"Created user {obj.username} with role {obj.get_role_display()} via admin interface"
            )
        else:
            log_user_action(
                request.user,
                f"Modified user {obj.username} via admin interface"
            )
    
    def delete_model(self, request, obj):
        """Log user deletion in admin"""
        username = obj.username
        super().delete_model(request, obj)
        log_user_action(
            request.user,
            f"Deleted user {username} via admin interface",
            level=logging.WARNING
        )
    
    def has_add_permission(self, request):
        # Only superusers, super managers, and managers can add users
        has_perm = request.user.is_superuser or request.user.role in [User.UserRole.SUPER_MANAGER, User.UserRole.MANAGER]
        if not has_perm:
            log_user_action(
                request.user,
                "Attempted to access user creation without permission",
                level=logging.WARNING
            )
        return has_perm
    
    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        # Superusers can change any user
        has_perm = request.user.is_superuser or request.user.can_manage_user(obj)
        if not has_perm:
            log_user_action(
                request.user,
                f"Attempted to modify user {obj.username} without permission",
                level=logging.WARNING
            )
        return has_perm
    
    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        # Only superusers can delete users
        has_perm = request.user.is_superuser
        if not has_perm and obj:
            log_user_action(
                request.user,
                f"Attempted to delete user {obj.username} without permission",
                level=logging.WARNING
            )
        return has_perm
    
    def import_csv(self, request):
        # Check if user has permission to import CSV
        if not (request.user.is_superuser or request.user.role in [User.UserRole.SUPER_MANAGER, User.UserRole.MANAGER]):
            log_user_action(
                request.user,
                "Attempted to access CSV import without permission",
                level=logging.WARNING
            )
            raise PermissionDenied("You don't have permission to import users.")
            
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            if not csv_file.name.endswith('.csv'):
                log_user_action(
                    request.user,
                    f"Attempted to upload non-CSV file: {csv_file.name}",
                    level=logging.WARNING
                )
                messages.error(request, 'Please upload a CSV file.')
                return redirect("..")
            
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(decoded_file))
            
            row_count = 0
            error_count = 0
            success_count = 0
            error_messages = []
            
            log_user_action(request.user, f"Started CSV import of users from file: {csv_file.name}")
            
            for row in csv_data:
                try:
                    # Validate required fields
                    required_fields = ['username', 'email', 'role']
                    if not all(field in row for field in required_fields):
                        raise ValueError(f"Missing required fields: {', '.join(required_fields)}")
                    
                    # Validate role
                    if row['role'] not in dict(User.UserRole.choices):
                        raise ValueError(f"Invalid role: {row['role']}")
                    
                    new_role = row['role']
                    parent = None
                    
                    # Role and parent assignment rules based on the creating user's role
                    if request.user.is_superuser:
                        # Superadmin can create any role
                        # Calling agents won't have a parent
                        if new_role == User.UserRole.CALLING_AGENT:
                            parent = None
                        # For other roles, use specified parent or none
                        elif row.get('parent_username'):
                            try:
                                parent = User.objects.get(username=row['parent_username'])
                            except User.DoesNotExist:
                                raise ValueError(f"Parent user not found: {row['parent_username']}")
                                
                    elif request.user.role == User.UserRole.SUPER_MANAGER:
                        # Super managers can only create managers and collection officers
                        if new_role not in [User.UserRole.MANAGER, User.UserRole.COLLECTION_OFFICER]:
                            raise ValueError(f"Super managers cannot create users with role: {new_role}")
                            
                        if new_role == User.UserRole.MANAGER:
                            # Managers created by super manager must have the super manager as parent
                            parent = request.user
                        else:  # COLLECTION_OFFICER
                            # Collection officers must have a manager under this super manager as parent
                            if not row.get('parent_username'):
                                raise ValueError("Collection officers must have a manager parent specified")
                            try:
                                parent = User.objects.get(
                                    username=row['parent_username'],
                                    role=User.UserRole.MANAGER
                                )
                                # Verify the manager is a descendant of this super manager
                                if not request.user.can_manage_user(parent):
                                    raise ValueError(
                                        f"The specified manager {parent.username} is not under your management"
                                    )
                            except User.DoesNotExist:
                                raise ValueError(f"Manager not found: {row['parent_username']}")
                                
                    elif request.user.role == User.UserRole.MANAGER:
                        # Managers can only create collection officers
                        if new_role != User.UserRole.COLLECTION_OFFICER:
                            raise ValueError(f"Managers cannot create users with role: {new_role}")
                        # Collection officers created by manager automatically have the manager as parent
                        parent = request.user
                    
                    # Generate password
                    password = generate_random_password()
                    
                    # Create user
                    user = User(
                        username=row['username'],
                        email=row['email'],
                        first_name=row.get('first_name', ''),
                        last_name=row.get('last_name', ''),
                        role=new_role,
                        parent=parent
                    )
                    
                    # Set creator for automatic parent assignment
                    user._creator = request.user
                    
                    # Set password and save
                    user.set_password(password)
                    user.save()
                    
                    # Store credentials
                    access_token = store_user_credentials(
                        user_id=user.id,
                        username=user.username,
                        password=password,
                        created_by_id=request.user.id
                    )
                    
                    success_count += 1
                    log_user_action(
                        request.user,
                        f"Successfully imported user {user.username} with role {user.get_role_display()} from CSV"
                    )
                    
                    # Add success message with credentials access link
                    messages.success(
                        request,
                        f"Created user {user.username}. Get credentials at: /users/credentials/{access_token}/"
                    )
                    
                except Exception as e:
                    error_count += 1
                    error_message = f"Row {row_count + 1}: {str(e)}"
                    error_messages.append(error_message)
                    log_user_action(
                        request.user,
                        f"Failed to import user from CSV - {error_message}",
                        level=logging.ERROR
                    )
                
                row_count += 1
            
            # Log final import summary
            log_user_action(
                request.user,
                f"Completed CSV import: {success_count} successes, {error_count} errors out of {row_count} rows"
            )
            
            # Display summary
            messages.info(request, f"Processed {row_count} rows: {success_count} successes, {error_count} errors")
            
            # Display errors if any
            for error in error_messages:
                messages.error(request, error)
            
            return redirect("..")
        
        form = CSVImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_form.html", payload)

admin.site.register(User, CustomUserAdmin)
