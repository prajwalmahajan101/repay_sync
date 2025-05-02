from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
import csv
import io
from .models import Interaction
from .forms import CSVImportForm
from logger.user_logger import log_user_action
import logging
from django.utils import timezone

User = get_user_model()

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'disposition', 'interaction_type', 'created_by', 'created_at', 'next_call_date')
    list_filter = ('disposition', 'interaction_type', 'created_at')
    search_fields = ('customer__name', 'comment', 'created_by__username')
    ordering = ('-created_at',)
    raw_id_fields = ('customer',)
    
    change_list_template = "admin/interactions_change_list.html"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='import_csv'),
        ]
        return custom_urls + urls
    
    def save_model(self, request, obj, form, change):
        """Log interaction creation/modification in admin"""
        is_new = not obj.pk
        if is_new:
            obj.created_by = request.user
            # Set interaction type based on user role
            obj.interaction_type = Interaction.InteractionTypeChoices.CALL if request.user.role == User.UserRole.CALLING_AGENT else Interaction.InteractionTypeChoices.FIELD
            
        super().save_model(request, obj, form, change)
        
        if is_new:
            log_user_action(
                request.user,
                f"Created interaction for customer {obj.customer.name} via admin interface"
            )
        else:
            log_user_action(
                request.user,
                f"Modified interaction for customer {obj.customer.name} via admin interface"
            )
    
    def delete_model(self, request, obj):
        """Log interaction deletion in admin"""
        customer_name = obj.customer.name
        super().delete_model(request, obj)
        log_user_action(
            request.user,
            f"Deleted interaction for customer {customer_name} via admin interface",
            level=logging.WARNING
        )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
            
        # Calling agents can see all interactions
        if request.user.role == User.UserRole.CALLING_AGENT:
            return qs
            
        # Get customers accessible to the user based on their role
        customers = request.user.get_managed_customers_queryset()
        return qs.filter(customer__in=customers)
    
    def import_csv(self, request):
        # Check if user has permission to import CSV
        if not (request.user.is_superuser or request.user.role in [User.UserRole.CALLING_AGENT, User.UserRole.SUPER_MANAGER, User.UserRole.MANAGER, User.UserRole.COLLECTION_OFFICER]):
            log_user_action(
                request.user,
                "Attempted to access interaction CSV import without permission",
                level=logging.WARNING
            )
            raise PermissionDenied("You don't have permission to import interactions.")
            
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            if not csv_file.name.endswith('.csv'):
                log_user_action(
                    request.user,
                    f"Attempted to upload non-CSV file for interaction import: {csv_file.name}",
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
            
            log_user_action(request.user, f"Started interaction CSV import from file: {csv_file.name}")
            
            for row in csv_data:
                try:
                    # Validate required fields
                    required_fields = ['customer_id', 'disposition', 'comment']
                    if not all(field in row for field in required_fields):
                        raise ValueError(f"Missing required fields: {', '.join(required_fields)}")
                    
                    # Validate customer access
                    try:
                        customer = request.user.get_managed_customers_queryset().get(id=row['customer_id'])
                    except Exception as e:
                        raise ValueError(f"Invalid or inaccessible customer ID: {row['customer_id']}")
                    
                    # Validate disposition
                    if row['disposition'] not in dict(Interaction.DispositionChoices.choices):
                        raise ValueError(f"Invalid disposition: {row['disposition']}")
                    
                    # Handle next_call_date if provided
                    next_call_date = None
                    if row.get('next_call_date'):
                        try:
                            next_call_date = timezone.datetime.strptime(
                                row['next_call_date'],
                                '%Y-%m-%d %H:%M:%S'
                            )
                            next_call_date = timezone.make_aware(next_call_date)
                            if next_call_date < timezone.now():
                                raise ValueError("Next call date must be in the future")
                        except ValueError as e:
                            raise ValueError(f"Invalid next_call_date format. Use YYYY-MM-DD HH:MM:SS: {str(e)}")
                    
                    # Create interaction
                    interaction = Interaction(
                        customer=customer,
                        disposition=row['disposition'],
                        comment=row['comment'],
                        next_call_date=next_call_date,
                        created_by=request.user,
                        interaction_type=row['interaction_type']
                    )
                    interaction.save()
                    
                    success_count += 1
                    log_user_action(
                        request.user,
                        f"Successfully imported interaction for customer {customer.name} from CSV"
                    )
                    
                except Exception as e:
                    error_count += 1
                    error_message = f"Row {row_count + 1}: {str(e)}"
                    error_messages.append(error_message)
                    log_user_action(
                        request.user,
                        f"Failed to import interaction from CSV - {error_message}",
                        level=logging.ERROR
                    )
                
                row_count += 1
            
            # Log final import summary
            log_user_action(
                request.user,
                f"Completed interaction CSV import: {success_count} successes, {error_count} errors out of {row_count} rows"
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
