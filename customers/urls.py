from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='customer-list'),
    path('create/', views.create_customer, name='customer-create'),
    path('<int:pk>/', views.customer_detail, name='customer-detail'),
    path('<int:pk>/update/', views.update_customer, name='customer-update'),
    path('<int:pk>/delete/', views.delete_customer, name='delete-customer'),
    path('unassigned/', views.unassigned_customers, name='unassigned-customers'),
    path('<int:pk>/assign-officer/', views.assign_collection_officer, name='assign-collection-officer'),
    path('<int:pk>/latest-interaction/', views.customer_latest_interaction, name='customer-latest-interaction'),
] 