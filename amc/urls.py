from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Existing form views
    path("amc-form/<int:pk>/", views.amc_form, name="amc_form"),
    path("customer-form/<int:pk>/", views.customer_form, name="customer_form"),

    # Consolidated list/create endpoints (handles GET/POST)
    path("api/amc/amc-types/", views.amc_types_list, name="amc_types_list"),
    path("api/amc/payment-terms/", views.payment_terms_list, name="payment_terms_list"),

    # Consolidated detail endpoints (handles PUT/DELETE)
    path("api/amc/amc-types/<int:amc_type_id>/", views.amc_types_detail, name="amc_types_detail"),
    path("api/amc/payment-terms/<int:payment_term_id>/", views.payment_terms_detail, name="payment_terms_detail"),
    path("api/amc/next-reference/", views.get_next_amc_reference, name="get_next_amc_reference"),

    # Read-only AMC expiry listings
    path("amc/expiring/this-month/", views.amc_expiring_this_month, name="amc_expiring_this_month"),
    path("amc/expiring/last-month/", views.amc_expiring_last_month, name="amc_expiring_last_month"),
    path("amc/expiring/next-month/", views.amc_expiring_next_month, name="amc_expiring_next_month"),

    # Mobile app API endpoints
    path("api/amc/list/", views.list_amcs_mobile, name="list_amcs_mobile"),
    path("api/amc/create/", views.create_amc_mobile, name="create_amc_mobile"),
    path("api/amc/types/list/", views.list_amc_types_mobile, name="list_amc_types_mobile"),
    path("api/amc/types/create/", views.create_amc_type_mobile, name="create_amc_type_mobile"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)