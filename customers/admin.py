from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
import csv
import io
from .models import Customer
from .forms import CSVImportForm
from logger.user_logger import log_user_action
import logging

User = get_user_model()

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'collection_officer', 'is_active')
    list_filter = ('is_active', 'collection_officer')
    search_fields = ('name', 'phone_number', 'email', 'address')
    ordering = ('-updated_at',)
    
    change_list_template = "admin/customer_change_list.html"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='import_csv'),
        ]
        return custom_urls + urls
    
    def save_model(self, request, obj, form, change):
        """Log customer creation/modification in admin"""
        is_new = not obj.pk
        obj._current_user = request.user
        super().save_model(request, obj, form, change)
        
        if is_new:
            log_user_action(
                request.user,
                f"Created customer {obj.name} via admin interface"
            )
        else:
            log_user_action(
                request.user,
                f"Modified customer {obj.name} via admin interface"
            )
    
    def delete_model(self, request, obj):
        """Log customer deletion in admin"""
        customer_name = obj.name
        super().delete_model(request, obj)
        log_user_action(
            request.user,
            f"Deleted customer {customer_name} via admin interface",
            level=logging.WARNING
        )
    
    def import_csv(self, request):
        # Check if user has permission to import CSV
        if not (request.user.is_superuser or request.user.role in [User.UserRole.SUPER_MANAGER, User.UserRole.MANAGER, User.UserRole.COLLECTION_OFFICER]):
            log_user_action(
                request.user,
                "Attempted to access customer CSV import without permission",
                level=logging.WARNING
            )
            raise PermissionDenied("You don't have permission to import customers.")
            
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            if not csv_file.name.endswith('.csv'):
                log_user_action(
                    request.user,
                    f"Attempted to upload non-CSV file for customer import: {csv_file.name}",
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
            
            log_user_action(request.user, f"Started customer CSV import from file: {csv_file.name}")
            
            for row in csv_data:
                try:
                    # Validate required fields
                    required_fields = ['name', 'phone_number', 'address']
                    if not all(field in row for field in required_fields):
                        raise ValueError(f"Missing required fields: {', '.join(required_fields)}")
                    
                    # Handle collection officer assignment based on user role
                    collection_officer = None
                    
                    # For collection officers, they can only assign themselves
                    if request.user.role == User.UserRole.COLLECTION_OFFICER:
                        collection_officer = request.user
                        if row.get('collection_officer_username') and row['collection_officer_username'] != request.user.username:
                            raise ValueError("Collection officers can only assign themselves as collection officer")
                    
                    # For managers and super managers, handle collection officer assignment
                    elif row.get('collection_officer_username'):
                        try:
                            target_officer = User.objects.get(
                                username=row['collection_officer_username'],
                                role=User.UserRole.COLLECTION_OFFICER
                            )
                            
                            # Get all valid collection officers based on user role
                            if request.user.role == User.UserRole.MANAGER:
                                valid_officers = request.user.get_descendants()
                            elif request.user.role == User.UserRole.SUPER_MANAGER:
                                # Get descendants of descendants for super managers
                                valid_officers = request.user.get_descendants().filter(role=User.UserRole.COLLECTION_OFFICER)
                            else:  # superuser
                                valid_officers = User.objects.filter(role=User.UserRole.COLLECTION_OFFICER)
                            
                            if target_officer not in valid_officers:
                                raise ValueError(
                                    f"You don't have permission to assign collection officer: {target_officer.username}"
                                )
                            
                            collection_officer = target_officer
                                
                        except User.DoesNotExist:
                            raise ValueError(f"Collection officer not found: {row['collection_officer_username']}")
                    
                    # Create customer
                    customer = Customer(
                        name=row['name'],
                        phone_number=row['phone_number'],
                        email=row.get('email', ''),
                        address=row['address'],
                        collection_officer=collection_officer,
                    )
                    customer.save()
                    
                    success_count += 1
                    log_user_action(
                        request.user,
                        f"Successfully imported customer {customer.name} from CSV"
                    )
                    
                except Exception as e:
                    error_count += 1
                    error_message = f"Row {row_count + 1}: {str(e)}"
                    error_messages.append(error_message)
                    log_user_action(
                        request.user,
                        f"Failed to import customer from CSV - {error_message}",
                        level=logging.ERROR
                    )
                
                row_count += 1
            
            # Log final import summary
            log_user_action(
                request.user,
                f"Completed customer CSV import: {success_count} successes, {error_count} errors out of {row_count} rows"
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
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == User.UserRole.CALLING_AGENT:
            return qs
            
        # Super managers can see customers assigned to collection officers under their subordinate managers
        if request.user.role == User.UserRole.SUPER_MANAGER:
            # Get all descendants (managers and collection officers)
            descendants = request.user.get_descendants()
            # Get collection officers who are descendants of the super manager's direct manager subordinates
            collection_officer_ids = User.objects.filter(
                role=User.UserRole.COLLECTION_OFFICER,
                manager__in=descendants
            ).values_list('id', flat=True)
            return qs.filter(collection_officer_id__in=collection_officer_ids)
            
        # Managers can see customers assigned to their subordinate collection officers
        if request.user.role == User.UserRole.MANAGER:
            subordinate_ids = request.user.get_descendants().filter(role=User.UserRole.COLLECTION_OFFICER).values_list('id', flat=True)
            return qs.filter(collection_officer_id__in=subordinate_ids)
            
        # Collection officers can only see their assigned customers
        if request.user.role == User.UserRole.COLLECTION_OFFICER:
            return qs.filter(collection_officer=request.user)
            
        return qs.none()
