from django.contrib import admin
from .models import TravelRequest

@admin.register(TravelRequest)
class TravelRequestAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'travel_by', 'travel_date', 'from_place', 'to_place', 'amount', 'created_at')
    list_filter = ('travel_by', 'travel_date', 'created_at')
    search_fields = ('created_by__username', 'from_place', 'to_place')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Travel Details', {
            'fields': ('travel_by', 'travel_date', 'from_place', 'to_place', 'amount')
        }),
        ('Additional Information', {
            'fields': ('attachment', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
