from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Existing form views
    path("amc-form/<int:pk>/", views.amc_form, name="amc_form"),
    path("customer-form/<int:pk>/", views.customer_form, name="customer_form"),

    # API endpoints for fetching dropdown options
    path("api/amc/amc-types/", views.get_amc_types, name="get_amc_types"),
    path("api/amc/payment-terms/", views.get_payment_terms, name="get_payment_terms"),

    # CRUD operations for AMC types
    path("api/amc/amc-types/", views.create_amc_type, name="create_amc_type"),
    path("api/amc/amc-types/<int:amc_type_id>/", views.update_amc_type, name="update_amc_type"),
    path("api/amc/amc-types/<int:amc_type_id>/delete/", views.delete_amc_type, name="delete_amc_type"),

    # CRUD operations for payment terms
    path("api/amc/payment-terms/", views.create_payment_term, name="create_payment_term"),
    path("api/amc/payment-terms/<int:payment_term_id>/", views.update_payment_term, name="update_payment_term"),
    path("api/amc/payment-terms/<int:payment_term_id>/delete/", views.delete_payment_term, name="delete_payment_term"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
