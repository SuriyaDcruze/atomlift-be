from django.urls import path
from . import views

urlpatterns = [
    path('lionsol/', views.lionsol_homepage, name='lionsol_homepage'),
    path('dashboard/', views.custom_dashboard, name='custom_dashboard'),
]
