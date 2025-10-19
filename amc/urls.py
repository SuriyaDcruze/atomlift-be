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
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)