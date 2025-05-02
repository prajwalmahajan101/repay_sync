from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    path('', views.interaction_list, name='interaction-list'),
    path('create/', views.create_interaction, name='interaction-create'),
    path('<int:pk>/', views.interaction_detail, name='interaction-detail'),
    path('<int:pk>/update/', views.update_interaction, name='interaction-update'),
    path('<int:pk>/delete/', views.delete_interaction, name='interaction-delete'),
] 