from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('subordinates/', views.subordinates, name='subordinates'),
    path('<int:user_id>/assign-parent/', views.assign_parent, name='assign_parent'),
    path('credentials/<str:access_token>/', views.get_credentials, name='get_credentials'),
] 